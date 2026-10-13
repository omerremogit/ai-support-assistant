"""The assistant. Each customer message goes through these steps:

1. Remove card numbers (NFR-03).
2. If the chat was handed to an agent, stop.
3. If we're waiting for identity details or return details, handle those (plain code).
4. Otherwise, ask the AI what the customer wants (classifier).
5. Route by tier (A, B, C, D). Facts come from the mock systems and decisions from the rules,
   never from the AI model (FR-19, NFR-07).
6. Log the turn with personal data masked (FR-39, NFR-05).

Reply "outcomes" match the expected outcomes in tests/test_cases.csv.
"""
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import classifier, config, faq, identity, privacy, rules
from .data import friendly_date, load_customers, load_faq, load_tiers, to_date

DISCLOSURE = "Hi, I'm Harbor & Thread's AI assistant. You can ask for a person at any time."
VERIFY_ASK = ("To help with that, I need to confirm who you are. Please send your full name, "
              "account ID (it starts with HT-) and the email address on your account, all in one message.")
ESCALATION = ("If you'd like this reviewed, I can arrange a callback from a manager to the phone "
              "number on your account.")
CARD_WARNING = ("For your security, I've removed the card number from this chat. "
                "Please don't share card details here.")
HANDOFF_NOTE = ("I'm connecting you with a support agent now. I've passed along a summary of our chat, "
                "so you won't need to repeat yourself.")

TROUBLESHOOTING_FIXES = {
    "credit_card": ["Please check that your card's expiry date and billing address are up to date, then try again.",
                    "Try logging out and back in, then retry the payment."],
    "shopping_cart": ["Try refreshing the page and adding the item again.",
                      "Try logging out and back in, and check whether the item has gone out of stock."],
    "search_results": ["Try clearing your browser cookies, then search again.",
                       "Try logging out and back in, then search again."],
    "slow_speed": ["Try closing other browser tabs, and check whether other websites load normally.",
                   "Try logging out and back in, then reload the page."],
}
REPORTED_TO_WEBSITE_TEAM = {"search_results", "slow_speed"}
FAQ_TOPICS = {"jeans", "shirt", "boots", "jacket", "pricing", "membership", "timing", "policy"}
RETURN_TYPES = {"return_size", "return_color", "return_stain"}
ORDER_RE = re.compile(r"\bORD-\d{4}\b", re.IGNORECASE)
INJECTION_RE = re.compile(r"ignore (all |your |the )?(previous |prior )?instructions|admin mode|developer mode",
                          re.IGNORECASE)


@dataclass
class Session:
    session_id: str
    customer: dict | None = None
    failed_attempts: int = 0
    clarifications: int = 0
    current_request: str | None = None
    pending_request: str | None = None      # waiting for identity details before answering this
    troubleshooting_step: int = 0
    return_state: dict = field(default_factory=dict)
    handed_off: bool = False
    handoff_summary: dict | None = None
    turns: int = 0
    last_reply: str | None = None
    tried: list = field(default_factory=list)


class Assistant:
    def __init__(self, llm):
        self.llm = llm
        self.customers = load_customers()
        self.tiers = load_tiers()
        self.faq = load_faq()
        self.sessions: dict[str, Session] = {}
        self.approvals: dict[str, dict] = {}

    # ------------------------------------------------------------------ entry point
    def handle(self, session_id: str, message: str) -> dict:
        s = self.sessions.setdefault(session_id, Session(session_id))
        s.turns += 1
        message, had_card = privacy.remove_card_numbers(message)
        trace = []
        if had_card:
            trace.append("Card number removed from the message (NFR-03)")

        result = self._route(s, message, trace)
        if had_card:
            result["reply"] = CARD_WARNING + " " + result["reply"]
        if s.turns == 1:
            result["reply"] = DISCLOSURE + " " + result["reply"]
        s.last_reply = result["reply"]

        result.update({
            "session_id": session_id,
            "request_type": s.current_request,
            "tier": self.tiers.get(s.current_request or "", "-"),
            "verified": s.customer is not None,
            "handoff_summary": s.handoff_summary,
            "trace": trace,
        })
        self._log(s, message, result)
        return result

    # ------------------------------------------------------------------ routing
    def _route(self, s: Session, message: str, trace: list) -> dict:
        if s.handed_off:
            trace.append("Chat already handed to an agent")
            return self._reply("An agent will be with you shortly. They can see our full conversation.", "handoff")

        # Waiting for identity details?
        if s.pending_request and s.customer is None and identity.looks_like_identity(message):
            return self._verify(s, message, trace)

        # Waiting for return details (Phase 2)?
        if s.return_state.get("awaiting") and s.customer is not None:
            return self._continue_return(s, message, trace)

        c = classifier.classify(self.llm, message, s.current_request, s.last_reply)
        trace.append(f"AI classified the request as '{c['request_type']}'")

        if c["wants_human"]:
            return self._handoff(s, message, "Customer asked for a person", trace)

        # Follow-ups on the current request
        if s.current_request and not c["is_new_request"]:
            follow_up = self._follow_up(s, message, c, trace)
            if follow_up:
                return follow_up

        request = c["request_type"]
        if INJECTION_RE.search(message) and request in ("unclear", "greeting"):
            request = "account_general"
            trace.append("Instruction-injection attempt detected; treated as an account request")

        if request == "greeting":
            return self._reply("How can I help you today?", "answer")
        if request == "unclear":
            return self._clarify(s, message, trace)

        s.current_request = request
        s.clarifications = 0
        tier = self.tiers.get(request, "B" if request == "account_general" else "D")
        trace.append(f"Tier {tier}")

        if tier == "D":
            return self._handoff(s, message, f"Tier D request ({request}): people only during the pilot", trace)
        if tier == "A":
            return self._tier_a(s, request, message, trace)
        if tier == "C" and not (config.PHASE >= 2 and request in RETURN_TYPES):
            return self._handoff(s, message, f"Tier C request ({request}) needs an agent in this phase", trace)

        # Tiers B and C (returns in Phase 2) need a verified customer
        if s.customer is None:
            s.pending_request = request
            if request in RETURN_TYPES:
                order = ORDER_RE.search(message)
                s.return_state = {"order_id": order.group(0).upper() if order else None,
                                  "method": self._return_method(message)}
            return self._ask_verification(message, c, trace)
        return self._answer_verified(s, request, message, trace)

    # ------------------------------------------------------------------ follow-ups
    def _follow_up(self, s: Session, message: str, c: dict, trace: list):
        request = s.current_request
        if request in TROUBLESHOOTING_FIXES and (c["still_has_problem"] or c["asks_agent_to_place_order"]):
            return self._troubleshoot_next(s, request, c, trace)
        if c["is_change_request"]:
            if request == "refund_status":
                trace.append("Refund status comes from the system and can't be changed in chat (FR-27)")
                return self._reply("I'm not able to change the status of a refund. It reflects where the "
                                   "refund is in our system. " + ESCALATION, "decline_and_offer_escalation")
            if self.tiers.get(request) == "B":
                trace.append("Read-only request became a change: stricter path (FR-03)")
                return self._handoff(s, message, f"Change requested during a read-only request ({request})", trace,
                                     lead="I can't make changes to your account in this chat.")
        if c["disputes_outcome"] and s.customer is not None:
            trace.append("Customer disputed the answer: official escalation path (FR-33)")
            return self._reply("I understand this is frustrating. The information I gave you is what our "
                               "system shows. " + ESCALATION, "decline_and_offer_escalation")
        return None

    # ------------------------------------------------------------------ tier A
    def _tier_a(self, s: Session, request: str, message: str, trace: list) -> dict:
        if request in FAQ_TOPICS:
            result = faq.answer(self.llm, self.faq, request, message)
            if result["answered"] and result["answer"]:
                trace.append("Answered from the FAQ (FR-12)")
                return self._reply(result["answer"], "answer")
            trace.append("Question not covered by the FAQ: no guessing (FR-13)")
            return self._handoff(s, message, f"Question not covered by the {request} FAQ", trace,
                                 lead="I don't have that information, so I'll connect you with an agent who can help.")
        s.troubleshooting_step = 0
        return self._troubleshoot_next(s, request, {"asks_agent_to_place_order": False}, trace, first=True)

    def _troubleshoot_next(self, s: Session, request: str, c: dict, trace: list, first: bool = False) -> dict:
        fixes = TROUBLESHOOTING_FIXES[request]
        if not first and (c.get("asks_agent_to_place_order") or s.troubleshooting_step >= len(fixes)):
            trace.append("Fixes didn't work: secure checkout link instead of taking the order in chat (FR-16)")
            return self._reply("I'm sorry that didn't work. I can't place orders or take card details in chat, "
                               f"but you can finish your purchase on our secure checkout page: "
                               f"{config.SECURE_CHECKOUT_LINK}", "secure_link")
        fix = fixes[s.troubleshooting_step]
        s.troubleshooting_step += 1
        s.tried.append(fix)
        text = ("Sorry you're having trouble. " if first else "Thanks for trying that. ") + fix
        if first and request in REPORTED_TO_WEBSITE_TEAM:
            text += " I've also reported this problem to our Website Team."
            trace.append("Reported to the Website Team (TRB-02)")
        trace.append(f"Offered approved fix {s.troubleshooting_step} of {len(fixes)} (TRB-01)")
        return self._reply(text + " Let me know if it works.", "answer")

    # ------------------------------------------------------------------ identity
    def _ask_verification(self, message: str, c: dict, trace: list) -> dict:
        lead = ""
        if c.get("asking_for_someone_else"):
            lead = "I can only share account information with the account holder once they've verified their identity. "
            trace.append("Asked about someone else's account: account holder must verify (FR-06)")
        if identity.mentions_security_question(message):
            lead += "I can't verify your identity with a security question answer. "
            trace.append("Security question answer not accepted (FR-09)")
        if INJECTION_RE.search(message):
            lead += "I can't skip identity checks. "
        trace.append("Asked for the standard identity details in one message (FR-07)")
        return self._reply(lead + VERIFY_ASK, "verify")

    def _verify(self, s: Session, message: str, trace: list) -> dict:
        customer = identity.verify(self.customers, identity.parse_identity(message))
        if customer is None:
            s.failed_attempts += 1
            trace.append(f"Verification failed (attempt {s.failed_attempts} of {identity.MAX_ATTEMPTS})")
            if s.failed_attempts >= identity.MAX_ATTEMPTS:
                return self._handoff(s, message, "Identity couldn't be verified after 3 attempts", trace,
                                     lead="I wasn't able to verify your identity.")
            return self._reply("Those details don't match our records. Please check your full name, account ID "
                               "and email address, and send them again in one message.", "verify")
        s.customer = customer
        request, s.pending_request = s.pending_request, None
        trace.append("Identity verified (FR-06)")
        return self._answer_verified(s, request, message, trace)

    # ------------------------------------------------------------------ tier B (read-only) and returns
    def _answer_verified(self, s: Session, request: str, message: str, trace: list) -> dict:
        cust = s.customer
        if request in RETURN_TYPES:
            return self._continue_return(s, message, trace)
        if request in ("status_active", "status_due_amount", "status_due_date"):
            return self._subscription(s, cust, message, trace)
        if request == "refund_status":
            trace.append("Read refunds from the system")
            if not cust["refunds"]:
                return self._handoff(s, message, "No refund on record", trace,
                                     lead="I don't see any refund on your account, so I'll connect you with an agent who can look into it.")
            r = cust["refunds"][-1]
            return self._reply(f"Your refund for order {r['order_id']} (${r['amount']:.2f}) is {r['status']}. "
                               f"It was requested by {r['requested_via']}.", "answer")
        if request == "status":
            trace.append("Read shipping status from the order system (FR-11)")
            open_orders = [o for o in cust["orders"] if o["shipping_status"] != "Delivered"]
            if not open_orders:
                return self._reply("All the orders on your account show as delivered.", "answer")
            o = open_orders[-1]
            when = f" and is expected to arrive on {friendly_date(o['expected_delivery'])}" if o.get("expected_delivery") else ""
            return self._reply(f"Your order {o['order_id']} ({o['item']}) is {o['shipping_status']}{when}. "
                               "According to our system it's on schedule, so you don't need to do anything.", "answer")
        if request == "recover_username":
            trace.append("Read username from the account")
            return self._reply(f"Your username is {cust['username']}.", "answer")
        return self._reply("You're verified. What would you like to know about your account?", "answer")

    def _subscription(self, s: Session, cust: dict, message: str, trace: list) -> dict:
        trace.append("Read subscription from the system (FR-18)")
        sub = cust.get("subscription")
        if not sub:
            return self._reply("I don't see a subscription on your account.", "answer")
        due, amount = to_date(sub["due_date"]), sub["amount_due"]
        if amount <= 0 and due <= config.TODAY:
            trace.append("System values look wrong: flagged, not adjusted (FR-19)")
            return self._handoff(s, message, f"Subscription data looks wrong: ${amount:.2f} due {sub['due_date']}", trace,
                                 lead=(f"Something looks wrong with your subscription details: our system shows "
                                       f"${amount:.2f} due on {friendly_date(sub['due_date'])}. Rather than guess, "
                                       "I'll have an agent check it."))
        if sub["status"] == "past due":
            trace.append("Past due: secure payment link (FR-20)")
            return self._reply(f"Your subscription is past due. ${amount:.2f} was due on {friendly_date(sub['due_date'])}. "
                               f"You can pay securely here: {config.SECURE_PAYMENT_LINK}. Please don't share card "
                               "details in this chat.", "secure_link")
        return self._reply(f"Your subscription is {sub['status']}. Your next payment of ${amount:.2f} is due on "
                           f"{friendly_date(sub['due_date'])}.", "answer")

    def _continue_return(self, s: Session, message: str, trace: list) -> dict:
        st = s.return_state
        order_match = ORDER_RE.search(message)
        if order_match:
            st["order_id"] = order_match.group(0).upper()
        st["method"] = st.get("method") or self._return_method(message)
        if not st.get("order_id"):
            st["awaiting"] = True
            return self._reply("Which order is it? Please share the order ID (it starts with ORD-).", "answer")
        order = next((o for o in s.customer["orders"] if o["order_id"] == st["order_id"]), None)
        if order is None:
            st["order_id"], st["awaiting"] = None, True
            return self._reply("I can't find that order on your account. Please check the order ID and send it again.", "answer")

        membership = s.customer["membership"]
        decision = rules.return_eligibility(membership, to_date(order["purchase_date"]), order["has_receipt"],
                                            order["original_packaging"], config.TODAY)
        trace.append(f"Rule {decision.rule_id} applied with system data: {membership}, bought "
                     f"{order['purchase_date']} -> {'allowed' if decision.allowed else 'declined'}")
        if not decision.allowed:
            st["awaiting"] = False
            return self._reply(f"I've checked your account: you're a {membership} member and order {order['order_id']} "
                               f"was bought on {friendly_date(order['purchase_date'])}. {decision.reason} "
                               "So I'm not able to accept this return. " + ESCALATION,
                               "decline_and_offer_escalation")
        if not st.get("method"):
            st["awaiting"] = True
            return self._reply("Good news: this item can be returned. Would you like to return it by mail, in store, "
                               "or at a drop-off center?", "answer")
        st["awaiting"] = False
        approval_id = "APR-" + uuid.uuid4().hex[:6].upper()
        self.approvals[approval_id] = {
            "approval_id": approval_id, "status": "pending", "session_id": s.session_id,
            "customer": s.customer["full_name"], "account_id": s.customer["account_id"],
            "action": f"Create a return and shipping label for {order['order_id']} ({order['item']})",
            "method": st["method"], "rule": decision.rule_id, "reason": decision.reason,
            "data_used": {"membership": membership, "purchase_date": order["purchase_date"],
                          "has_receipt": order["has_receipt"], "original_packaging": order["original_packaging"]},
        }
        trace.append(f"Prepared {approval_id} for agent approval: nothing created yet (FR-23, FR-24)")
        return {"reply": (f"Good news: this return is allowed. {decision.reason} I've prepared your return by {st['method']} "
                          "for one of our agents to approve. Once it's approved, you'll get a shipping label at the "
                          "email address on your account, sent to the address we have on file."),
                "outcome": "prepare_for_approval", "approval_id": approval_id}

    @staticmethod
    def _return_method(message: str):
        text = message.lower()
        if "mail" in text:
            return "mail"
        if "drop" in text:
            return "drop-off center"
        if "store" in text:
            return "store"
        return None

    # ------------------------------------------------------------------ approvals (Phase 2)
    def decide_approval(self, approval_id: str, approve: bool, reason_code: str | None = None) -> dict:
        a = self.approvals[approval_id]
        if a["status"] != "pending":
            return a
        if not approve and not reason_code:
            raise ValueError("A reason code is required to reject (FR-37)")
        a["status"] = "approved" if approve else "rejected"
        a["reason_code"] = reason_code
        a["decided_at"] = datetime.now(timezone.utc).isoformat()
        return a

    # ------------------------------------------------------------------ helpers
    def _clarify(self, s: Session, message: str, trace: list) -> dict:
        s.clarifications += 1
        if s.clarifications > 2:
            return self._handoff(s, message, "Request still unclear after two clarifying questions", trace)
        trace.append(f"Clarifying question {s.clarifications} of 2 (FR-05)")
        if s.clarifications == 1:
            return self._reply("Could you tell me a bit more about what you need? For example, a product question, "
                               "an order, a refund, your subscription or a problem with the website.", "clarify")
        return self._reply("Sorry, I'm still not sure what you need. Is it about a product, an order or refund, "
                           "your subscription, or the website?", "clarify")

    def _handoff(self, s: Session, message: str, reason: str, trace: list, lead: str = "") -> dict:
        s.handed_off = True
        s.handoff_summary = {
            "request_type": s.current_request or "unknown",
            "tier": self.tiers.get(s.current_request or "", "-"),
            "verified": s.customer is not None,
            "customer": s.customer["full_name"] if s.customer else None,
            "reason": reason,
            "what_was_tried": s.tried or ["Nothing yet"],
            "customer_words": privacy.mask_personal_data(message),
        }
        trace.append(f"Handed off to an agent: {reason} (FR-31)")
        return self._reply((lead + " " if lead else "") + HANDOFF_NOTE, "handoff")

    @staticmethod
    def _reply(text: str, outcome: str) -> dict:
        return {"reply": text, "outcome": outcome}

    def _log(self, s: Session, message: str, result: dict):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": s.session_id,
            "turn": s.turns,
            "request_type": result["request_type"],
            "tier": result["tier"],
            "outcome": result["outcome"],
            "resolved_by": "agent" if s.handed_off else "ai",
            "handoff_reason": (s.handoff_summary or {}).get("reason"),
            "verified": result["verified"],
            "actions": result["trace"],
            "customer_message": privacy.mask_personal_data(message),
            "assistant_reply": privacy.mask_personal_data(result["reply"]),
        }
        config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(config.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
