"""Identity verification (FR-06 to FR-10). Plain code, no AI involved.

Standard check (test plan assumption, pending issue 4): full name, account ID and email.
"""
import re

ACCOUNT_RE = re.compile(r"\bHT-\d{5}\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
MAX_ATTEMPTS = 3
SECURITY_QUESTION_RE = re.compile(r"maiden name|security question|first pet|mother'?s", re.IGNORECASE)


def looks_like_identity(text: str) -> bool:
    return bool(ACCOUNT_RE.search(text) or EMAIL_RE.search(text))


def parse_identity(text: str) -> dict:
    account = ACCOUNT_RE.search(text)
    email = EMAIL_RE.search(text)
    rest = ACCOUNT_RE.sub(" ", EMAIL_RE.sub(" ", text))
    rest = re.sub(r"(?i)\b(my name is|name:|account id:?|email:?|it's|i am|i'm)\b", " ", rest)
    parts = [p.strip(" .:;-") for p in re.split(r"[,\n;]", rest)]
    name = next((p for p in parts if len(re.findall(r"[A-Za-z]+", p)) >= 2), "")
    return {
        "full_name": " ".join(name.split()),
        "account_id": account.group(0).upper() if account else "",
        "email": email.group(0).lower() if email else "",
    }


def verify(customers: dict, details: dict):
    """Returns the matching customer, or None. All three details must match."""
    customer = customers.get(details.get("account_id", ""))
    if not customer:
        return None
    name_ok = details.get("full_name", "").casefold() == customer["full_name"].casefold()
    email_ok = details.get("email", "") == customer["email"].lower()
    return customer if name_ok and email_ok else None


def mentions_security_question(text: str) -> bool:
    return bool(SECURITY_QUESTION_RE.search(text))
