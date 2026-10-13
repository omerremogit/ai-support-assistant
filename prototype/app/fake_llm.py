"""A keyword-based stand-in for the AI model, for offline development (LLM_PROVIDER=fake).

It's deliberately simple. Use it to check the app runs without spending API credit,
not to measure quality: real test results must come from the real model.
"""
import json
import re

RULES = [
    (r"talk to a (real )?person|real person|human|speak to an agent", None),
    (r"password", "recover_password"),
    (r"username", "recover_username"),
    (r"two.?factor|2fa", "reset_2fa"),
    (r"morning|evening", "status_delivery_time"),
    (r"\breturn\b", "return_size"),
    (r"refund", "refund_status"),
    (r"shipping email|delayed|on schedule", "status"),
    (r"subscription.*(owe|amount|balance|how much)|(owe|balance|amount due).*subscription", "status_due_amount"),
    (r"subscription.*(renew|when|due)", "status_due_date"),
    (r"subscription.*active|still active", "status_active"),
    (r"search", "search_results"),
    (r"cart", "shopping_cart"),
    (r"card.*(reject|declin)", "credit_card"),
    (r"slow|won't load", "slow_speed"),
    (r"jeans", "jeans"), (r"shirt", "shirt"), (r"boots", "boots"), (r"jacket", "jacket"),
    (r"ignore (your|previous)|admin mode|account details", "account_general"),
    (r"^\s*(hi|hello|hey)\W*$", "greeting"),
]


class FakeLLM:
    usage = {"input_tokens": 0, "output_tokens": 0, "calls": 0}

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        if '"answered"' in system:
            return self._faq(user)
        return self._classify(user)

    def _classify(self, user: str) -> str:
        msg = re.search(r"<message>(.*)</message>", user, re.DOTALL).group(1).lower()
        current = re.search(r"Current request type: (\S+)", user).group(1)
        result = {"request_type": "unclear"}
        for pattern, label in RULES:
            if re.search(pattern, msg):
                if label is None:
                    result["wants_human"] = True
                    result["request_type"] = current if current != "none" else "unclear"
                else:
                    result["request_type"] = label
                break
        follow_up = result["request_type"] == "unclear" and current != "none"
        if follow_up or result["request_type"] == current:
            result["request_type"] = current
            result["is_new_request"] = False
        else:
            result["is_new_request"] = current != "none"
        result["is_change_request"] = bool(re.search(r"\b(mark|change|switch|renew it|update|cancel)\b", msg))
        result["disputes_outcome"] = bool(re.search(r"not acceptable|unacceptable|ridiculous|it's been weeks", msg))
        result["asks_agent_to_place_order"] = bool(re.search(r"order it for me|place the order|just order", msg))
        result["still_has_problem"] = bool(re.search(r"still|didn't work|not working", msg))
        result["asking_for_someone_else"] = bool(re.search(r"\bmy (wife|husband|partner)\b|\bfor my (mother|father)\b|on behalf", msg))
        return json.dumps(result)

    def _faq(self, user: str) -> str:
        question = re.search(r"<question>(.*)</question>", user, re.DOTALL).group(1).lower()
        words = {w for w in re.findall(r"[a-z]{4,}", question)} - {"your", "does", "they", "this", "what", "after", "jeans", "shirt", "shirts", "boots", "jacket", "made"}
        best, best_score = None, 0
        for q, a in re.findall(r"Q: (.*)\nA: (.*)", user):
            score = len(words & set(re.findall(r"[a-z]{4,}", q.lower())))
            if score > best_score:
                best, best_score = a, score
        if best_score >= 1:
            return json.dumps({"answered": True, "answer": best})
        return json.dumps({"answered": False, "answer": ""})
