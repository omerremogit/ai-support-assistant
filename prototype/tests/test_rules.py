"""Rules unit tests TC-27 to TC-33 (test plan, section 5). Run: python -m unittest discover -s tests"""
import unittest
from datetime import date

from app.rules import return_eligibility

TODAY = date(2026, 10, 12)


class ReturnRuleTests(unittest.TestCase):
    def check(self, membership, purchased, receipt, packaging, expected):
        decision = return_eligibility(membership, date.fromisoformat(purchased), receipt, packaging, TODAY)
        self.assertEqual(decision.allowed, expected, decision.reason)

    def test_tc27_gold_any_date(self):
        self.check("Gold", "2026-03-15", False, False, True)

    def test_tc28_silver_5_months_no_receipt(self):
        self.check("Silver", "2026-05-10", False, False, True)

    def test_tc29_bronze_120_days_no_receipt_or_packaging(self):
        self.check("Bronze", "2026-06-14", False, False, False)

    def test_tc30_bronze_120_days_with_receipt(self):
        self.check("Bronze", "2026-06-14", True, False, True)

    def test_tc31_bronze_exactly_90_days(self):
        self.check("Bronze", "2026-07-14", False, False, True)

    def test_tc32_guest_20_days(self):
        self.check("Guest", "2026-09-22", False, False, True)

    def test_tc33_guest_45_days_packaging_only(self):
        self.check("Guest", "2026-08-28", False, True, False)

    def test_silver_7_months_no_receipt_is_declined(self):
        self.check("Silver", "2026-03-01", False, False, False)


if __name__ == "__main__":
    unittest.main()
