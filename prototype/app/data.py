"""Loads the mock company systems: customers, the request-type tiers and the FAQ."""
import csv
import json
from datetime import date

from . import config


def load_customers():
    """Customers keyed by account ID. Stands in for the account, order and subscription systems."""
    data = json.loads(config.MOCK_CUSTOMERS_FILE.read_text(encoding="utf-8"))
    return {c["account_id"].upper(): c for c in data["customers"]}


def load_tiers():
    """Request type -> tier (A, B, C or D), from the automation matrix (Step 4)."""
    with open(config.AUTOMATION_MATRIX_FILE, encoding="utf-8") as f:
        return {row["request_type"]: row["tier"] for row in csv.DictReader(f)}


def load_faq():
    return json.loads(config.FAQ_FILE.read_text(encoding="utf-8"))


def to_date(value: str) -> date:
    return date.fromisoformat(value)


def friendly_date(value: str) -> str:
    """'2026-11-03' -> 'November 3, 2026'."""
    d = to_date(value)
    return f"{d.strftime('%B')} {d.day}, {d.year}"
