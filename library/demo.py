"""Sample data for trying the system out (``python main.py --demo``)."""

from .book import Book, ReferenceBook
from .member import FacultyMember, GuestMember, StudentMember
from .service import Library


def seed(library: Library) -> None:
    for book in (
        Book("9780262033848", "Introduction to Algorithms", "Cormen, Leiserson, Rivest, Stein", copies=2),
        Book("9780132350884", "Clean Code", "Robert C. Martin", copies=1),
        Book("9780201633610", "Design Patterns", "Gamma, Helm, Johnson, Vlissides", copies=1),
        Book("9780134494166", "Clean Architecture", "Robert C. Martin", copies=1),
        ReferenceBook("9780198611868", "Oxford English Dictionary", "Oxford University Press"),
    ):
        library.add_book(book)
    for member in (
        StudentMember("S001", "Asha Rao"),
        StudentMember("S002", "Ravi Kumar"),
        FacultyMember("F001", "Dr. Meera Iyer"),
        GuestMember("G001", "Sam Fernandes"),
    ):
        library.add_member(member)
