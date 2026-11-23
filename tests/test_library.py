import unittest
from datetime import date, timedelta

from library import Book, FacultyMember, GuestMember, Library, ReferenceBook, StudentMember
from library.exceptions import (
    AlreadyBorrowedError,
    BookNotFoundError,
    BorrowLimitError,
    DuplicateError,
    LibraryError,
    LoanNotFoundError,
    MemberNotFoundError,
    NoCopiesAvailableError,
    NotLendableError,
    OutstandingFinesError,
)

DAY0 = date(2025, 4, 1)


class LibraryTestCase(unittest.TestCase):
    def setUp(self):
        self.lib = Library()
        self.lib.add_book(Book("B1", "Clean Code", "Robert Martin", copies=2))
        self.lib.add_book(Book("B2", "Design Patterns", "Gang of Four"))
        self.lib.add_book(Book("B3", "Refactoring", "Martin Fowler"))
        self.lib.add_book(Book("B4", "SICP", "Abelson"))
        self.lib.add_book(ReferenceBook("R1", "Oxford Dictionary", "OUP"))
        self.lib.add_member(StudentMember("S1", "Asha"))
        self.lib.add_member(StudentMember("S2", "Ravi"))
        self.lib.add_member(FacultyMember("F1", "Dr. Iyer"))
        self.lib.add_member(GuestMember("G1", "Sam"))


class CatalogueTests(LibraryTestCase):
    def test_duplicates_are_rejected(self):
        with self.assertRaises(DuplicateError):
            self.lib.add_book(Book("B1", "Other", "X"))
        with self.assertRaises(DuplicateError):
            self.lib.add_member(StudentMember("S1", "Imposter"))

    def test_lookup_errors(self):
        with self.assertRaises(BookNotFoundError):
            self.lib.get_book("nope")
        with self.assertRaises(MemberNotFoundError):
            self.lib.get_member("nope")

    def test_search_by_title_author_and_isbn(self):
        self.assertEqual([b.isbn for b in self.lib.search("martin")], ["B1", "B3"])
        self.assertEqual([b.isbn for b in self.lib.search("sicp")], ["B4"])
        self.assertEqual([b.isbn for b in self.lib.search("B2")], ["B2"])
        self.assertEqual(self.lib.search("zzz"), [])


class IssueTests(LibraryTestCase):
    def test_issue_sets_due_date_by_member_type_and_updates_stock(self):
        t_student = self.lib.issue_book("B1", "S1", on=DAY0)
        t_faculty = self.lib.issue_book("B1", "F1", on=DAY0)
        self.assertEqual(t_student.due_date, DAY0 + timedelta(days=14))
        self.assertEqual(t_faculty.due_date, DAY0 + timedelta(days=30))
        self.assertEqual(self.lib.get_book("B1").available_copies, 0)
        self.assertEqual([t.txn_id for t in self.lib.active_loans()], [1, 2])

    def test_no_copies_left(self):
        self.lib.issue_book("B2", "S1", on=DAY0)
        with self.assertRaises(NoCopiesAvailableError):
            self.lib.issue_book("B2", "S2", on=DAY0)

    def test_reference_books_cannot_be_borrowed(self):
        with self.assertRaises(NotLendableError):
            self.lib.issue_book("R1", "S1", on=DAY0)

    def test_same_member_cannot_borrow_two_copies_of_a_title(self):
        self.lib.issue_book("B1", "S1", on=DAY0)
        with self.assertRaises(AlreadyBorrowedError):
            self.lib.issue_book("B1", "S1", on=DAY0)

    def test_borrow_limits_differ_by_member_type(self):
        for isbn in ("B1", "B2", "B3"):
            self.lib.issue_book(isbn, "S1", on=DAY0)
        with self.assertRaises(BorrowLimitError):  # students: 3
            self.lib.issue_book("B4", "S1", on=DAY0)
        self.lib.issue_book("B4", "F1", on=DAY0)  # faculty: 10 -- fine

        self.lib.issue_book("B1", "G1", on=DAY0)  # guest: 1
        with self.assertRaises(BorrowLimitError):
            self.lib.issue_book("B3", "G1", on=DAY0)

    def test_unknown_book_or_member(self):
        with self.assertRaises(BookNotFoundError):
            self.lib.issue_book("nope", "S1", on=DAY0)
        with self.assertRaises(MemberNotFoundError):
            self.lib.issue_book("B1", "nope", on=DAY0)

    def test_failed_issue_changes_nothing(self):
        with self.assertRaises(LibraryError):
            self.lib.issue_book("R1", "S1", on=DAY0)
        self.assertEqual(self.lib.transactions, [])


class ReturnAndFineTests(LibraryTestCase):
    def test_on_time_return_has_no_fine_and_restocks(self):
        self.lib.issue_book("B2", "S1", on=DAY0)
        txn = self.lib.return_book("B2", "S1", on=DAY0 + timedelta(days=14))
        self.assertEqual(txn.fine, 0)
        self.assertFalse(txn.is_active)
        self.assertEqual(self.lib.get_book("B2").available_copies, 1)
        self.assertEqual(self.lib.get_member("S1").fines_due, 0)

    def test_late_return_charges_the_member_polymorphically(self):
        self.lib.issue_book("B1", "S1", on=DAY0)  # due day 14
        self.lib.issue_book("B2", "F1", on=DAY0)  # due day 30
        self.lib.issue_book("B3", "G1", on=DAY0)  # due day 7

        student = self.lib.return_book("B1", "S1", on=DAY0 + timedelta(days=24))  # 10 late
        faculty = self.lib.return_book("B2", "F1", on=DAY0 + timedelta(days=40))  # 10 late
        guest = self.lib.return_book("B3", "G1", on=DAY0 + timedelta(days=17))  # 10 late

        self.assertEqual((student.fine, faculty.fine, guest.fine), (20, 3, 70))
        self.assertEqual(self.lib.get_member("S1").fines_due, 20)
        self.assertEqual(self.lib.get_member("F1").fines_due, 3)
        self.assertEqual(self.lib.get_member("G1").fines_due, 70)

    def test_returning_something_not_on_loan(self):
        with self.assertRaises(LoanNotFoundError):
            self.lib.return_book("B1", "S1", on=DAY0)
        self.lib.issue_book("B1", "S1", on=DAY0)
        with self.assertRaises(LoanNotFoundError):  # a different member has not borrowed it
            self.lib.return_book("B1", "S2", on=DAY0)

    def test_cannot_return_twice(self):
        self.lib.issue_book("B1", "S1", on=DAY0)
        self.lib.return_book("B1", "S1", on=DAY0)
        with self.assertRaises(LoanNotFoundError):
            self.lib.return_book("B1", "S1", on=DAY0)

    def test_return_before_issue_date_is_rejected(self):
        self.lib.issue_book("B1", "S1", on=DAY0)
        with self.assertRaises(ValueError):
            self.lib.return_book("B1", "S1", on=DAY0 - timedelta(days=1))
        self.assertEqual(len(self.lib.active_loans()), 1)  # loan still open

    def test_unpaid_fines_block_new_loans_until_paid(self):
        self.lib.issue_book("B1", "S1", on=DAY0)
        self.lib.return_book("B1", "S1", on=DAY0 + timedelta(days=20))  # 6 days late -> Rs 12
        with self.assertRaises(OutstandingFinesError):
            self.lib.issue_book("B2", "S1", on=DAY0 + timedelta(days=21))
        self.assertEqual(self.lib.pay_fine("S1", 5), 7)
        with self.assertRaises(OutstandingFinesError):
            self.lib.issue_book("B2", "S1", on=DAY0 + timedelta(days=21))
        self.assertEqual(self.lib.pay_fine("S1", 7), 0)
        self.lib.issue_book("B2", "S1", on=DAY0 + timedelta(days=21))  # allowed again

    def test_pay_fine_validation(self):
        with self.assertRaises(ValueError):
            self.lib.pay_fine("S1", 0)
        with self.assertRaises(ValueError):
            self.lib.pay_fine("S1", 10)  # owes nothing
        with self.assertRaises(MemberNotFoundError):
            self.lib.pay_fine("nope", 1)

    def test_returned_copy_can_be_borrowed_again(self):
        self.lib.issue_book("B2", "S1", on=DAY0)
        self.lib.return_book("B2", "S1", on=DAY0)
        self.lib.issue_book("B2", "S2", on=DAY0)
        self.assertEqual(self.lib.get_book("B2").available_copies, 0)


class ReportTests(LibraryTestCase):
    def test_overdue_report(self):
        self.lib.issue_book("B1", "S1", on=DAY0)  # due +14
        self.lib.issue_book("B2", "G1", on=DAY0)  # due +7
        self.lib.issue_book("B3", "F1", on=DAY0)  # due +30
        report = self.lib.overdue_loans(on=DAY0 + timedelta(days=20))
        self.assertEqual([(o.transaction.member_id, o.days_overdue, o.fine_so_far) for o in report], [("G1", 13, 85), ("S1", 6, 12)])

    def test_report_ignores_returned_and_on_time_loans(self):
        self.lib.issue_book("B1", "S1", on=DAY0)
        self.lib.return_book("B1", "S1", on=DAY0 + timedelta(days=30))
        self.assertEqual(self.lib.overdue_loans(on=DAY0 + timedelta(days=60)), [])

    def test_history_includes_returned_and_active(self):
        self.lib.issue_book("B1", "S1", on=DAY0)
        self.lib.return_book("B1", "S1", on=DAY0)
        self.lib.issue_book("B2", "S1", on=DAY0)
        self.assertEqual([t.isbn for t in self.lib.history("S1")], ["B1", "B2"])
        with self.assertRaises(MemberNotFoundError):
            self.lib.history("nope")


if __name__ == "__main__":
    unittest.main()
