import unittest

from lending.domain.errors import BorrowLimitReached, LoanAlreadyReturned, NoCopiesAvailable, NotFound
from tests.helpers import START, make_env


class BorrowTest(unittest.TestCase):
    def setUp(self):
        self.service, self.repo, self.clock = make_env()
        self.member = self.repo.add_member("Alice", "standard")
        self.book = self.repo.add_book("SICP", "Abelson", 1)

    def test_borrow_creates_loan_with_due_date(self):
        loan = self.service.borrow(self.member.id, self.book.id)
        self.assertEqual(loan.borrowed_on, START)
        self.assertEqual((loan.due_on - START).days, 14)

    def test_borrow_fails_when_no_copies_left(self):
        other = self.repo.add_member("Bob")
        self.service.borrow(self.member.id, self.book.id)
        with self.assertRaises(NoCopiesAvailable):
            self.service.borrow(other.id, self.book.id)

    def test_borrow_fails_at_member_limit(self):
        many = self.repo.add_book("Many copies", "X", 10)
        for _ in range(3):
            self.service.borrow(self.member.id, many.id)
        with self.assertRaises(BorrowLimitReached):
            self.service.borrow(self.member.id, many.id)

    def test_unknown_member_or_book(self):
        with self.assertRaises(NotFound):
            self.service.borrow(999, self.book.id)
        with self.assertRaises(NotFound):
            self.service.borrow(self.member.id, 999)


class ReturnTest(unittest.TestCase):
    def setUp(self):
        self.service, self.repo, self.clock = make_env()
        member = self.repo.add_member("Alice")
        book = self.repo.add_book("SICP", "Abelson", 1)
        self.loan = self.service.borrow(member.id, book.id)

    def test_on_time_return_has_no_fee(self):
        self.clock.advance(10)
        receipt = self.service.return_book(self.loan.id)
        self.assertEqual(receipt.late_fee_cents, 0)
        self.assertFalse(receipt.loan.is_active)

    def test_late_return_charges_fee(self):
        self.clock.advance(14 + 4)
        self.assertEqual(self.service.return_book(self.loan.id).late_fee_cents, 200)

    def test_cannot_return_twice(self):
        self.service.return_book(self.loan.id)
        with self.assertRaises(LoanAlreadyReturned):
            self.service.return_book(self.loan.id)


class RenewTest(unittest.TestCase):
    def setUp(self):
        self.service, self.repo, self.clock = make_env()
        member = self.repo.add_member("Alice")
        book = self.repo.add_book("SICP", "Abelson", 1)
        self.loan = self.service.borrow(member.id, book.id)

    def test_renew_extends_due_date(self):
        renewed = self.service.renew(self.loan.id)
        self.assertGreater(renewed.due_on, self.loan.due_on)
        self.assertEqual(renewed.renew_count, 1)

    def test_cannot_renew_returned_loan(self):
        self.service.return_book(self.loan.id)
        with self.assertRaises(LoanAlreadyReturned):
            self.service.renew(self.loan.id)


if __name__ == "__main__":
    unittest.main()
