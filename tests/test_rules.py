import unittest
from datetime import date

from lending.domain import rules
from lending.domain.models import Member


class DueDateTest(unittest.TestCase):
    def test_due_date_is_fourteen_days_after_borrow(self):
        self.assertEqual(rules.due_date_for(date(2026, 1, 5)), date(2026, 1, 19))


class CanBorrowTest(unittest.TestCase):
    def test_standard_member_limit(self):
        member = Member(1, "Alice", "standard")
        self.assertTrue(rules.can_borrow(member, 2))
        self.assertFalse(rules.can_borrow(member, 3))

    def test_premium_member_limit(self):
        member = Member(2, "Bob", "premium")
        self.assertTrue(rules.can_borrow(member, 4))
        self.assertFalse(rules.can_borrow(member, 5))

    def test_unknown_tier_falls_back_to_standard(self):
        self.assertFalse(rules.can_borrow(Member(3, "Eve", "gold"), 3))


class LateFeeTest(unittest.TestCase):
    def test_no_fee_when_on_time(self):
        self.assertEqual(rules.late_fee_cents(date(2026, 1, 19), date(2026, 1, 19)), 0)
        self.assertEqual(rules.late_fee_cents(date(2026, 1, 19), date(2026, 1, 10)), 0)

    def test_fee_per_day(self):
        self.assertEqual(rules.late_fee_cents(date(2026, 1, 19), date(2026, 1, 22)), 150)

    def test_fee_is_capped(self):
        self.assertEqual(rules.late_fee_cents(date(2026, 1, 19), date(2026, 6, 1)), rules.MAX_LATE_FEE_CENTS)


class CanRenewTest(unittest.TestCase):
    def test_fresh_loan_can_be_renewed(self):
        self.assertTrue(rules.can_renew(0))
        self.assertTrue(rules.can_renew(1))


if __name__ == "__main__":
    unittest.main()
