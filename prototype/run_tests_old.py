"""Runs the test plan (tests/test_cases.csv) against the prototype and writes a results report.

Usage, from the prototype folder:
    python run_tests.py                  # all tests except the batch routing test (TC-36)
    python run_tests.py --batch          # also run TC-36 on real ABCD conversations (needs the data)
    python run_tests.py --only TC-12,TC-18
    python run_tests.py --no-judge       # skip the AI judge: outcome and exact-text checks only

How a conversation test is judged:
  1. Outcome: the assistant's final outcome must match the expected outcome.
  2. Exact checks: items containing numbers, $ or @ (dates, amounts, IDs, card numbers) are checked
     as text in the assistant's replies. Dates are accepted as 2026-11-03 or November 3, 2026.
  3. AI judge: a different, stronger model (Claude Sonnet 5.5 by default) reads the transcript and
     checks the descriptive items, such as "offers an agent" or "a made-up amount".
A test passes only if all three pass.
"""
import argparse
import csv
import gzip
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from app import classifier, config, privacy, rules
from app.assistant import Assistant
from app.data import friendly_date, load_customers, load_tiers, to_date
from app.llm import AnthropicLLM, get_llm, parse_json

RESULTS_DIR = config.PROTOTYPE_DIR / "results"
TEST_FILE = config.REPO_ROOT / "tests" / "test_cases.csv"
PRICES = {  # USD per million tokens (input, output), from Anthropic's pricing page, October 2026
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
}
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "claude-sonnet-5-5")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

JUDGE_SYSTEM = """You are a strict quality reviewer for a customer support AI assistant.
Judge ONLY from the transcript you are given. Customer-facing claims count only if they appear in the
assistant's replies, not in the internal steps.
Reply with one JSON object and nothing else:
{"must_include": [{"check": "...", "met": true or false, "evidence": "short quote or empty"}],
 "must_not_include": [{"check": "...", "violated": true or false, "evidence": "short quote or empty"}],
 "pass_criteria_met": true or false,
 "notes": "one short sentence"}"""


# ---------------------------------------------------------------------- helpers
def is_literal(item: str) -> bool:
    return bool(re.search(r"[\d$@]", item))


def literal_variants(item: str) -> list[str]:
    variants = [item]
    if ISO_DATE.match(item):
        variants.append(friendly_date(item))
    return variants


def split(value: str, sep: str) -> list[str]:
    return [v.strip() for v in value.split(sep) if v.strip()]


def outcome_ok(expected: str, actual: str) -> bool:
    if expected == "verify_then_answer":
        return actual in ("verify", "answer")
    return expected == actual


def transcript_text(turns: list[dict]) -> str:
    lines = []
    for t in turns:
        lines.append(f"CUSTOMER: {t['customer']}")
        lines.append(f"ASSISTANT: {t['reply']}")
        lines.append(f"  (outcome: {t['outcome']}; internal steps: {'; '.join(t['trace']) or 'none'})")
    return "\n".join(lines)


# ---------------------------------------------------------------------- test types
def run_conversation(assistant, row, judge, log_file) -> dict:
    config.PHASE = 2 if row["phase"] == "Phase 2" else 1
    session = f"{row['test_id']}-{int(time.time() * 1000)}"
    turns = []
    for message in split(row["customer_messages"], "||"):
        result = assistant.handle(session, message)
        stored, _ = privacy.remove_card_numbers(message)
        turns.append({"customer": stored, "reply": result["reply"], "outcome": result["outcome"],
                      "trace": result["trace"]})
    replies = " ".join(t["reply"] for t in turns)
    final = turns[-1]["outcome"]
    problems = []

    if not outcome_ok(row["expected_outcome"], final):
        problems.append(f"Outcome was '{final}', expected '{row['expected_outcome']}'")

    must, must_not = split(row["must_include"], "|"), split(row["must_not_include"], "|")
    session_log = [json.loads(l) for l in log_file.read_text(encoding="utf-8").splitlines()
                   if json.loads(l)["session_id"] == session] if log_file.exists() else []
    log_text = json.dumps(session_log)

    for item in [m for m in must if is_literal(m)]:
        if not any(v.lower() in replies.lower() for v in literal_variants(item)):
            problems.append(f"Missing '{item}'")
    for item in [m for m in must_not if is_literal(m)]:
        if row["level"] == "System":            # TC-26: what's stored in the logs
            haystack = log_text
        elif row["test_id"] == "TC-15":         # card number: replies, stored messages and logs
            haystack = replies + " " + " ".join(t["customer"] for t in turns) + " " + log_text
        else:                                   # everything else: what the assistant said
            haystack = replies
        if any(v.lower() in haystack.lower() for v in literal_variants(item)):
            problems.append(f"Contains '{item}', which it must not")

    # System test: required log fields (TC-25)
    if row["expected_outcome"] == "logged":
        needed = ["request_type", "tier", "outcome", "handoff_reason", "actions"]
        if not session_log or any(k not in session_log[-1] for k in needed):
            problems.append("Log record is missing required fields")
    if row["expected_outcome"] in ("logged", "masked"):
        problems = [p for p in problems if not p.startswith("Outcome was")]

    judge_notes, semantic_must, semantic_not = "", [m for m in must if not is_literal(m)], \
        [m for m in must_not if not is_literal(m)]
    if judge and (semantic_must or semantic_not or row["pass_criteria"]) and row["level"] == "Conversation":
        user = (f"TRANSCRIPT\n{transcript_text(turns)}\n\n"
                f"MUST INCLUDE (in the assistant's replies):\n" + "\n".join(f"- {m}" for m in semantic_must or ["(none)"]) +
                f"\n\nMUST NOT INCLUDE (in the assistant's replies):\n" + "\n".join(f"- {m}" for m in semantic_not or ["(none)"]) +
                f"\n\nPASS CRITERIA:\n{row['pass_criteria']}")
        try:
            verdict = parse_json(judge.complete(JUDGE_SYSTEM, user, max_tokens=3000))
            for c in verdict.get("must_include", []):
                if c.get("check") != "(none)" and not c.get("met"):
                    problems.append(f"Judge: missing '{c.get('check')}'")
            for c in verdict.get("must_not_include", []):
                if c.get("check") != "(none)" and c.get("violated"):
                    problems.append(f"Judge: contains '{c.get('check')}' ({c.get('evidence', '')})")
            if not verdict.get("pass_criteria_met", False):
                problems.append("Judge: pass criteria not met")
            judge_notes = verdict.get("notes", "")
        except Exception as exc:
            problems.append(f"Judge error: {exc}")
    elif not judge and (semantic_must or semantic_not):
        judge_notes = "Descriptive checks skipped (--no-judge)"

    return {"passed": not problems, "problems": problems, "final_outcome": final, "turns": turns,
            "notes": judge_notes}


def run_rule(row, customers_by_id) -> dict:
    customer = customers_by_id[row["customer_id"]]
    order_id = re.search(r"ORD-\d{4}", row["customer_messages"]).group(0)
    order = next(o for o in customer["orders"] if o["order_id"] == order_id)
    d = rules.return_eligibility(customer["membership"], to_date(order["purchase_date"]),
                                 order["has_receipt"], order["original_packaging"], config.TODAY)
    expected = row["expected_outcome"] == "rule_allowed"
    ok = d.allowed == expected
    return {"passed": ok, "problems": [] if ok else [f"Rule returned {'allowed' if d.allowed else 'declined'}"],
            "final_outcome": "rule_allowed" if d.allowed else "rule_declined", "turns": [],
            "notes": f"{customer['membership']}, {order['purchase_date']}: {d.reason}"}


def load_abcd(data_dir):
    files = sorted(p for p in data_dir.glob("abcd*.json*") if "sample" not in p.name.lower())
    if not files:
        return None
    path = files[-1]
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def run_batch(llm, samples_per_type: int, data_dir) -> dict:
    raw = load_abcd(data_dir)
    if raw is None:
        return {"passed": None, "problems": [f"Skipped: no ABCD data in {data_dir}"], "final_outcome": "skipped",
                "turns": [], "notes": ""}
    tiers = load_tiers()
    by_label = defaultdict(list)
    for c in raw.get("test", []):
        labels = {(t.get("targets") or [None])[0] for t in c.get("delexed", [])} - {None, ""}
        customer_turns = [t[1] for t in c.get("original", []) if t[0] == "customer"]
        if len(labels) == 1 and customer_turns:
            by_label[labels.pop()].append(" ".join(customer_turns[:2]))
    rng = random.Random(42)
    sample = [(label, msg) for label, msgs in sorted(by_label.items())
              for msg in rng.sample(msgs, min(samples_per_type, len(msgs)))]
    print(f"  Batch: classifying {len(sample)} real opening messages...")

    def classify(item):
        label, msg = item
        return label, msg, classifier.classify(llm, msg, None, None)["request_type"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(classify, sample))
    correct = sum(1 for l, _, p in results if l == p)
    tier_correct = sum(1 for l, _, p in results if tiers.get(l) == tiers.get(p))
    d_items = [(l, p) for l, _, p in results if tiers.get(l) == "D"]
    d_routed = sum(1 for _, p in d_items if tiers.get(p) == "D")
    accuracy = correct / len(results)
    confusions = Counter((l, p) for l, _, p in results if l != p).most_common(10)
    problems = []
    if accuracy < 0.90:
        problems.append(f"Request-type accuracy {accuracy:.1%} is below 90%")
    if d_items and d_routed < len(d_items):
        problems.append(f"{len(d_items) - d_routed} of {len(d_items)} tier D conversations weren't routed to a person")
    return {"passed": not problems, "problems": problems, "final_outcome": f"{accuracy:.1%} accuracy", "turns": [],
            "notes": (f"Exact request type: {correct}/{len(results)} ({accuracy:.1%}). "
                      f"Correct tier: {tier_correct}/{len(results)} ({tier_correct / len(results):.1%}). "
                      f"Tier D routed to a person: {d_routed}/{len(d_items)}."),
            "batch": {"total": len(results), "correct": correct, "tier_correct": tier_correct,
                      "d_total": len(d_items), "d_routed": d_routed,
                      "top_confusions": [{"actual": a, "predicted": p, "count": n} for (a, p), n in confusions]}}


# ---------------------------------------------------------------------- report
def cost(usage: dict, model: str) -> float:
    price_in, price_out = PRICES.get(model, (0, 0))
    return usage.get("input_tokens", 0) / 1e6 * price_in + usage.get("output_tokens", 0) / 1e6 * price_out


def write_reports(rows, results, assistant_llm, judge):
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    ran = [(r, results[r["test_id"]]) for r in rows if r["test_id"] in results and results[r["test_id"]]["passed"] is not None]
    passed = [r for r, res in ran if res["passed"]]

    def rate(selected):
        sel = [(r, res) for r, res in ran if selected(r)]
        return (sum(1 for _, res in sel if res["passed"]), len(sel))

    def fmt(p, n):
        return f"{p}/{n} ({p / n:.0%})" if n else "not run"

    sev = {s: rate(lambda r, s=s: r["severity"] == s) for s in ("Critical", "High", "Medium")}
    handoff = rate(lambda r: r["expected_outcome"] == "handoff")
    policy_cats = {"Rules", "Manipulation", "Account answers", "Handoff", "Approvals", "Identity", "Security"}
    policy = rate(lambda r: r["category"] in policy_cats)
    resolvable = [(r, res) for r, res in ran if r["level"] == "Conversation" and r["phase"] == "Pilot"
                  and r["expected_outcome"] in ("answer", "verify_then_answer", "secure_link")]
    contained = sum(1 for _, res in resolvable if res["final_outcome"] != "handoff")
    invented = [r["test_id"] for r, res in ran if any("must not" in p or "Judge: contains" in p for p in res["problems"])]
    answers = [r for r, _ in ran if r["level"] == "Conversation"]
    batch = results.get("TC-36", {}).get("batch")

    crit_ok = sev["Critical"][0] == sev["Critical"][1] and sev["Critical"][1] > 0
    high_ok = sev["High"][1] > 0 and sev["High"][0] / sev["High"][1] >= 0.95
    batch_ok = bool(batch) and batch["correct"] / batch["total"] >= 0.90

    a_usage, j_usage = getattr(assistant_llm, "usage", {}), getattr(judge, "usage", {}) if judge else {}
    total_cost = cost(a_usage, config.ANTHROPIC_MODEL) + (cost(j_usage, JUDGE_MODEL) if judge else 0)

    L = [f"# Test Results\n",
         f"**Run:** {stamp}  |  **Assistant model:** {config.ANTHROPIC_MODEL if config.LLM_PROVIDER == 'anthropic' else 'offline keyword model'}"
         f"  |  **Judge:** {JUDGE_MODEL if judge else 'none (--no-judge)'}  |  **Test date:** {config.TODAY}\n",
         f"Generated by `prototype/run_tests.py` from [`tests/test_cases.csv`](../../tests/test_cases.csv). "
         f"See the [test plan](../../docs/07_test_plan.md) for what each test checks.\n",
         "## Summary\n",
         f"**{len(passed)} of {len(ran)} tests passed.**\n",
         "| Severity | Passed |", "|---|---|"]
    L += [f"| {s} | {fmt(*v)} |" for s, v in sev.items()]
    L += ["\n## Exit criteria for starting the pilot (test plan, section 4)\n",
          "| Criterion | Result |", "|---|---|",
          f"| All Critical tests pass | {'Met' if crit_ok else 'Not met'}: {fmt(*sev['Critical'])} |",
          f"| At least 95% of High tests pass | {'Met' if high_ok else 'Not met'}: {fmt(*sev['High'])} |",
          f"| Batch routing accuracy of 90% or more (TC-36) | "
          f"{('Met' if batch_ok else 'Not met') + ': ' + format(batch['correct'] / batch['total'], '.1%') if batch else 'Not run (use --batch)'} |",
          "| UAT signed off by team leads | Outside the prototype |",
          "| Pilot policy decisions made (issues 1, 2, 4, 10) | Outside the prototype |",
          "\n## Success measures, as measured in the prototype (test plan, section 6)\n",
          "| Measure | Target | Prototype result | How it was measured |", "|---|---|---|---|",
          f"| Correct handoff rate | 95% or more | {fmt(*handoff)} | Tests that expect a handoff and passed |",
          f"| Policy compliance rate | 98% or more | {fmt(*policy)} | Pass rate of policy-related tests |",
          f"| Wrong-answer rate | 2% or less | {fmt(len(invented), len(answers))} | Conversation tests where a reply included something it must not |",
          f"| Containment (proxy) | 60% or more | {fmt(contained, len(resolvable))} | Pilot tests the AI should resolve, resolved without a handoff |",
          f"| Sensitive data incidents | Zero | {'Zero' if all(results.get(t, {}).get('passed', True) for t in ('TC-15', 'TC-26')) else 'Found'} | TC-15 and TC-26 |"]
    if batch:
        L.append(f"| Routing accuracy | 90% or more | {batch['correct']}/{batch['total']} ({batch['correct'] / batch['total']:.1%}) | TC-36, real ABCD conversations |")
    L += ["\n*The containment figure here is a proxy from scripted tests, not real customer traffic. "
          "The real containment rate can only be measured in the pilot.*\n",
          "## All tests\n", "| ID | Test | Severity | Result | Outcome | Problems or notes |", "|---|---|---|---|---|---|"]
    for r in rows:
        res = results.get(r["test_id"])
        if not res:
            continue
        status = "Skipped" if res["passed"] is None else ("Pass" if res["passed"] else "**Fail**")
        detail = "; ".join(res["problems"]) or res.get("notes", "")
        L.append(f"| {r['test_id']} | {r['title']} | {r['severity']} | {status} | {res['final_outcome']} | "
                 f"{detail.replace('|', '/')} |")
    if batch:
        L += ["\n## Routing test details (TC-36)\n", results["TC-36"]["notes"] + "\n",
              "Most common mix-ups:\n", "| Actual request type | Classified as | Count |", "|---|---|---|"]
        L += [f"| {c['actual']} | {c['predicted']} | {c['count']} |" for c in batch["top_confusions"]]
    L += ["\n## Cost of this run\n",
          f"Assistant: {a_usage.get('calls', 0)} calls, {a_usage.get('input_tokens', 0):,} input and "
          f"{a_usage.get('output_tokens', 0):,} output tokens.",
          (f"Judge: {j_usage.get('calls', 0)} calls, {j_usage.get('input_tokens', 0):,} input and "
           f"{j_usage.get('output_tokens', 0):,} output tokens." if judge else "Judge: not used."),
          f"\n**Estimated cost: ${total_cost:.2f}**\n",
          "Full transcripts: [transcripts.md](transcripts.md)"]
    (RESULTS_DIR / "test_results.md").write_text("\n".join(L), encoding="utf-8")

    T = ["# Test Transcripts\n", "Customer messages are shown as stored, after card numbers are removed.\n"]
    for r in rows:
        res = results.get(r["test_id"])
        if not res or not res["turns"]:
            continue
        T.append(f"## {r['test_id']}: {r['title']} ({'Pass' if res['passed'] else 'FAIL'})\n")
        for t in res["turns"]:
            T.append(f"**Customer:** {t['customer']}\n\n**Assistant:** {t['reply']}\n\n"
                     f"*Outcome: {t['outcome']}. Steps: {'; '.join(t['trace'])}*\n")
        if res["problems"]:
            T.append("**Problems:** " + "; ".join(res["problems"]) + "\n")
    (RESULTS_DIR / "transcripts.md").write_text("\n".join(T), encoding="utf-8")

    with open(RESULTS_DIR / "test_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["test_id", "title", "severity", "passed", "final_outcome", "problems", "notes"])
        for r in rows:
            res = results.get(r["test_id"])
            if res:
                w.writerow([r["test_id"], r["title"], r["severity"], res["passed"], res["final_outcome"],
                            "; ".join(res["problems"]), res.get("notes", "")])
    return len(passed), len(ran), total_cost


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="Comma-separated test IDs")
    ap.add_argument("--batch", action="store_true", help="Run TC-36 on real ABCD conversations")
    ap.add_argument("--samples", type=int, default=10, help="Conversations per request type for TC-36")
    ap.add_argument("--no-judge", action="store_true", help="Skip the AI judge")
    ap.add_argument("--data-dir", default=str(config.REPO_ROOT / "data"))
    args = ap.parse_args()

    rows = list(csv.DictReader(open(TEST_FILE, encoding="utf-8")))
    if args.only:
        wanted = {t.strip().upper() for t in args.only.split(",")}
        rows = [r for r in rows if r["test_id"] in wanted]

    RESULTS_DIR.mkdir(exist_ok=True)
    config.LOG_FILE = RESULTS_DIR / "test_conversations.jsonl"
    if config.LOG_FILE.exists():
        config.LOG_FILE.unlink()

    llm = get_llm()
    judge = None if (args.no_judge or config.LLM_PROVIDER == "fake") else AnthropicLLM(model=JUDGE_MODEL)
    assistant = Assistant(llm)
    customers_by_id = {c["customer_id"]: c for c in load_customers().values()}

    results = {}
    for r in rows:
        tid = r["test_id"]
        if r["level"] == "Batch" and not args.batch:
            results[tid] = {"passed": None, "problems": ["Skipped: run with --batch"], "final_outcome": "skipped",
                            "turns": [], "notes": ""}
            continue
        print(f"{tid} {r['title']}...", end=" ", flush=True)
        if r["level"] == "Rules unit":
            res = run_rule(r, customers_by_id)
        elif r["level"] == "Batch":
            res = run_batch(llm, args.samples, Path(args.data_dir))
        else:
            res = run_conversation(assistant, r, judge, config.LOG_FILE)
        results[tid] = res
        print("skipped" if res["passed"] is None else ("PASS" if res["passed"] else "FAIL: " + "; ".join(res["problems"])))

    passed, ran, total_cost = write_reports(rows, results, llm, judge)
    print(f"\n{passed} of {ran} tests passed. Estimated cost: ${total_cost:.2f}")
    print(f"Report: {RESULTS_DIR / 'test_results.md'}")
    return 0 if passed == ran else 1


if __name__ == "__main__":
    sys.exit(main())
