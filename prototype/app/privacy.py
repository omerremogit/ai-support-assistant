"""Masking for card numbers and personal data (NFR-03, NFR-05)."""
import re

CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\(?\b\d{3}\)?[ .-]?\d{3}[ .-]\d{4}\b")


def remove_card_numbers(text: str):
    """Returns the text with card numbers removed, and whether any were found."""
    cleaned, count = CARD_RE.subn("[card number removed]", text)
    return cleaned, count > 0


def mask_personal_data(text: str) -> str:
    """Used for anything stored in logs."""
    text, _ = remove_card_numbers(text)
    text = EMAIL_RE.sub("[email]", text)
    text = PHONE_RE.sub("[phone]", text)
    return text
