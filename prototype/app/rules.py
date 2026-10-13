"""Business rules as fixed code (NFR-07). The AI model never decides eligibility.

RET-01 return eligibility (business rules catalog, section 5.1):
  Gold:   any time
  Silver: within 6 months, or with a receipt, or in original packaging
  Bronze: within 90 days, or with a receipt, or in original packaging
  Guest:  within 30 days, or with a receipt (original packaging doesn't count)
Day 90 counts as within 90 days (test plan TC-31 assumption).
"""
from dataclasses import dataclass
from datetime import date


@dataclass
class Decision:
    allowed: bool
    rule_id: str
    reason: str


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year, month = d.year + month_index // 12, month_index % 12 + 1
    days_in_month = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    return date(year, month, min(d.day, days_in_month))


def return_eligibility(membership: str, purchase_date: date, has_receipt: bool,
                       original_packaging: bool, today: date) -> Decision:
    level = membership.strip().lower()
    days = (today - purchase_date).days

    if level == "gold":
        return Decision(True, "RET-01", "Gold members can return items at any time.")
    if level == "silver":
        if today <= add_months(purchase_date, 6):
            return Decision(True, "RET-01", "The item was bought within the last 6 months.")
        if has_receipt:
            return Decision(True, "RET-01", "You have the receipt.")
        if original_packaging:
            return Decision(True, "RET-01", "The item is in its original packaging.")
        return Decision(False, "RET-01", "It's outside the 6-month return window for Silver members, "
                                         "and there's no receipt or original packaging.")
    if level == "bronze":
        if days <= 90:
            return Decision(True, "RET-01", "The item was bought within the last 90 days.")
        if has_receipt:
            return Decision(True, "RET-01", "You have the receipt.")
        if original_packaging:
            return Decision(True, "RET-01", "The item is in its original packaging.")
        return Decision(False, "RET-01", "It's outside the 90-day return window for Bronze members, "
                                         "and there's no receipt or original packaging.")
    if level == "guest":
        if days <= 30:
            return Decision(True, "RET-01", "The item was bought within the last 30 days.")
        if has_receipt:
            return Decision(True, "RET-01", "You have the receipt.")
        return Decision(False, "RET-01", "It's outside the 30-day return window for guest purchases, "
                                         "and guest returns need a receipt after 30 days.")
    return Decision(False, "RET-01", "The membership level on the account isn't recognized.")
