import unittest
from datetime import date

from library.book import Book, ReferenceBook, book_from_dict
from library.member import FacultyMember, GuestMember, Member, StudentMember, member_from_dict
from library.transaction import Transaction


class FinePolymorphismTests(unittest.TestCase):
    """Same call -- ``calculate_fine(days)`` -- gives different answers per member type."""

    def test_no_fine_when_on_time_or_early(self):
        for member in (StudentMember("1", "a"), FacultyMember("2", "b"), GuestMember("3", "c")):
            self.assertEqual(member.calculate_fine(0), 0, member.kind)
            self.assertEqual(member.calculate_fine(-5), 0, member.kind)

    def test_student_pays_flat_daily_rate(self):
        s = StudentMember("S1", "Asha")
        self.assertEqual(s.calculate_fine(1), 2)
        self.assertEqual(s.calculate_fine(10), 20)

    def test_faculty_has_a_grace_period(self):
        f = FacultyMember("F1", "Dr. Iyer")
        self.assertEqual(f.calculate_fine(3), 0)
        self.assertEqual(f.calculate_fine(7), 0)
        self.assertEqual(f.calculate_fine(8), 1)
        self.assertEqual(f.calculate_fine(17), 10)

    def test_guest_pays_late_fee_plus_daily_rate_up_to_a_cap(self):
        g = GuestMember("G1", "Sam")
        self.assertEqual(g.calculate_fine(1), 25)  # 20 + 1*5
        self.assertEqual(g.calculate_fine(10), 70)
        self.assertEqual(g.calculate_fine(1000), 500)  # capped

    def test_same_lateness_costs_differently(self):
        fines = {m.kind: m.calculate_fine(10) for m in (StudentMember("1", "a"), FacultyMember("2", "b"), GuestMember("3", "c"))}
        self.assertEqual(fines, {"student": 20, "faculty": 3, "guest": 70})

    def test_member_is_abstract(self):
        with self.assertRaises(TypeError):
            Member("1", "x")  # type: ignore[abstract]

    def test_due_date_uses_each_membership_loan_period(self):
        issued = date(2025, 4, 1)
        self.assertEqual(StudentMember("1", "a").due_date(issued), date(2025, 4, 15))
        self.assertEqual(FacultyMember("2", "b").due_date(issued), date(2025, 5, 1))
        self.assertEqual(GuestMember("3", "c").due_date(issued), date(2025, 4, 8))

    def test_validation(self):
        with self.assertRaises(ValueError):
            StudentMember("", "x")
        with self.assertRaises(ValueError):
            StudentMember("1", " ")
        with self.assertRaises(ValueError):
            StudentMember("1", "x", fines_due=-1)


class BookTests(unittest.TestCase):
    def test_copy_accounting(self):
        b = Book("1", "T", "A", copies=2)
        b.check_out()
        b.check_out()
        self.assertEqual(b.available_copies, 0)
        with self.assertRaises(ValueError):
            b.check_out()
        b.check_in()
        self.assertEqual(b.available_copies, 1)

    def test_cannot_check_in_more_than_owned(self):
        b = Book("1", "T", "A")
        with self.assertRaises(ValueError):
            b.check_in()

    def test_validation(self):
        with self.assertRaises(ValueError):
            Book("", "T", "A")
        with self.assertRaises(ValueError):
            Book("1", "", "A")
        with self.assertRaises(ValueError):
            Book("1", "T", "A", copies=0)

    def test_reference_books_are_not_lendable(self):
        self.assertTrue(Book("1", "T", "A").lendable)
        self.assertFalse(ReferenceBook("2", "Dictionary", "OUP").lendable)

    def test_matches(self):
        b = Book("978-1", "Clean Code", "Robert Martin")
        self.assertTrue(b.matches("clean"))
        self.assertTrue(b.matches("MARTIN"))
        self.assertTrue(b.matches("978-1"))
        self.assertFalse(b.matches("978"))  # ISBN must match exactly
        self.assertFalse(b.matches("python"))

    def test_roundtrip_preserves_subclass(self):
        original = ReferenceBook("2", "Dictionary", "OUP")
        restored = book_from_dict(original.to_dict())
        self.assertIsInstance(restored, ReferenceBook)
        self.assertEqual(restored.to_dict(), original.to_dict())

    def test_unknown_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            book_from_dict({"kind": "scroll", "isbn": "1", "title": "T", "author": "A", "copies": 1})


class MemberSerializationTests(unittest.TestCase):
    def test_roundtrip_preserves_subclass_and_fines(self):
        original = FacultyMember("F1", "Dr. Iyer", fines_due=12)
        restored = member_from_dict(original.to_dict())
        self.assertIsInstance(restored, FacultyMember)
        self.assertEqual((restored.member_id, restored.name, restored.fines_due), ("F1", "Dr. Iyer", 12))

    def test_unknown_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            member_from_dict({"kind": "alien", "member_id": "1", "name": "x"})


class TransactionTests(unittest.TestCase):
    def make(self, **kw):
        return Transaction(1, "isbn", "m1", date(2025, 4, 1), date(2025, 4, 15), **kw)

    def test_days_overdue_for_returned_loan(self):
        self.assertEqual(self.make(return_date=date(2025, 4, 15)).days_overdue(), 0)
        self.assertEqual(self.make(return_date=date(2025, 4, 20)).days_overdue(), 5)
        self.assertEqual(self.make(return_date=date(2025, 4, 10)).days_overdue(), 0)

    def test_days_overdue_for_active_loan_needs_a_date(self):
        t = self.make()
        self.assertTrue(t.is_active)
        self.assertEqual(t.days_overdue(date(2025, 4, 18)), 3)
        with self.assertRaises(ValueError):
            t.days_overdue()

    def test_roundtrip(self):
        for t in (self.make(), self.make(return_date=date(2025, 4, 20), fine=10)):
            self.assertEqual(Transaction.from_dict(t.to_dict()), t)


if __name__ == "__main__":
    unittest.main()
