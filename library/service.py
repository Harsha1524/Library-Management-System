"""The ``Library`` ties books, members and transactions together and enforces the rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from .book import Book, book_from_dict
from .exceptions import (
    AlreadyBorrowedError,
    BookNotFoundError,
    BorrowLimitError,
    DuplicateError,
    LoanNotFoundError,
    MemberNotFoundError,
    NoCopiesAvailableError,
    NotLendableError,
    OutstandingFinesError,
)
from .member import Member, member_from_dict
from .transaction import Transaction


@dataclass(frozen=True)
class OverdueLoan:
    transaction: Transaction
    days_overdue: int
    fine_so_far: int


class Library:
    def __init__(self) -> None:
        self.books: dict[str, Book] = {}
        self.members: dict[str, Member] = {}
        self.transactions: list[Transaction] = []
        self._next_txn_id = 1

    # ----------------------------------------------------------------- catalogue
    def add_book(self, book: Book) -> Book:
        if book.isbn in self.books:
            raise DuplicateError(f"a book with ISBN {book.isbn} already exists")
        self.books[book.isbn] = book
        return book

    def add_member(self, member: Member) -> Member:
        if member.member_id in self.members:
            raise DuplicateError(f"member ID {member.member_id} is already registered")
        self.members[member.member_id] = member
        return member

    def get_book(self, isbn: str) -> Book:
        try:
            return self.books[isbn.strip()]
        except KeyError:
            raise BookNotFoundError(f"no book with ISBN {isbn.strip()}") from None

    def get_member(self, member_id: str) -> Member:
        try:
            return self.members[member_id.strip()]
        except KeyError:
            raise MemberNotFoundError(f"no member with ID {member_id.strip()}") from None

    def search(self, query: str) -> list[Book]:
        """Books whose title or author contains ``query`` (case-insensitive), or whose ISBN equals it."""
        return sorted((b for b in self.books.values() if b.matches(query)), key=lambda b: b.title.lower())

    # --------------------------------------------------------------------- loans
    def active_loans(self, member_id: Optional[str] = None) -> list[Transaction]:
        return [t for t in self.transactions if t.is_active and (member_id is None or t.member_id == member_id)]

    def history(self, member_id: str) -> list[Transaction]:
        self.get_member(member_id)
        return [t for t in self.transactions if t.member_id == member_id.strip()]

    def issue_book(self, isbn: str, member_id: str, on: Optional[date] = None) -> Transaction:
        on = on or date.today()
        book = self.get_book(isbn)
        member = self.get_member(member_id)

        if not book.lendable:
            raise NotLendableError(f"'{book.title}' is a reference book and cannot be borrowed")
        if member.fines_due > 0:
            raise OutstandingFinesError(f"{member.name} must pay Rs {member.fines_due} in fines before borrowing")
        loans = self.active_loans(member.member_id)
        if any(t.isbn == book.isbn for t in loans):
            raise AlreadyBorrowedError(f"{member.name} already has '{book.title}'")
        if len(loans) >= member.max_books:
            raise BorrowLimitError(f"{member.name} ({member.kind}) can borrow at most {member.max_books} book(s) at a time")
        if book.available_copies == 0:
            raise NoCopiesAvailableError(f"all copies of '{book.title}' are on loan")

        txn = Transaction(
            txn_id=self._next_txn_id,
            isbn=book.isbn,
            member_id=member.member_id,
            issue_date=on,
            due_date=member.due_date(on),
        )
        self._next_txn_id += 1
        book.check_out()
        self.transactions.append(txn)
        return txn

    def return_book(self, isbn: str, member_id: str, on: Optional[date] = None) -> Transaction:
        """Close the loan, charge any fine to the member and put the copy back on the shelf."""
        on = on or date.today()
        book = self.get_book(isbn)
        member = self.get_member(member_id)
        txn = next((t for t in self.active_loans(member.member_id) if t.isbn == book.isbn), None)
        if txn is None:
            raise LoanNotFoundError(f"{member.name} has no active loan for '{book.title}'")
        if on < txn.issue_date:
            raise ValueError("a book cannot be returned before it was issued")

        txn.return_date = on
        txn.fine = member.calculate_fine(txn.days_overdue())  # polymorphic: depends on member type
        member.fines_due += txn.fine
        book.check_in()
        return txn

    def pay_fine(self, member_id: str, amount: int) -> int:
        """Record a payment and return the member's remaining balance."""
        member = self.get_member(member_id)
        if amount <= 0:
            raise ValueError("payment must be positive")
        if amount > member.fines_due:
            raise ValueError(f"payment of Rs {amount} exceeds the Rs {member.fines_due} owed")
        member.fines_due -= amount
        return member.fines_due

    def overdue_loans(self, on: Optional[date] = None) -> list[OverdueLoan]:
        """Active loans past their due date, with the fine they would incur if returned ``on``."""
        on = on or date.today()
        report = []
        for txn in self.active_loans():
            days = txn.days_overdue(on)
            if days > 0:
                member = self.members[txn.member_id]
                report.append(OverdueLoan(txn, days, member.calculate_fine(days)))
        return sorted(report, key=lambda o: o.days_overdue, reverse=True)

    # --------------------------------------------------------------- persistence
    def to_dict(self) -> dict[str, Any]:
        return {
            "next_txn_id": self._next_txn_id,
            "books": [b.to_dict() for b in self.books.values()],
            "members": [m.to_dict() for m in self.members.values()],
            "transactions": [t.to_dict() for t in self.transactions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Library":
        lib = cls()
        for b in data.get("books", []):
            lib.add_book(book_from_dict(b))
        for m in data.get("members", []):
            lib.add_member(member_from_dict(m))
        lib.transactions = [Transaction.from_dict(t) for t in data.get("transactions", [])]
        lib._next_txn_id = data.get("next_txn_id", max((t.txn_id for t in lib.transactions), default=0) + 1)
        return lib
