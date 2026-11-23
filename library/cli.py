"""Interactive, menu-driven front end."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

from .book import Book, ReferenceBook
from .exceptions import LibraryError
from .member import MEMBER_TYPES
from .service import Library

MENU = """
=========== Library Management System ===========
 1. Add book              6. Return book
 2. Add member            7. Member's loans & history
 3. List books            8. Overdue report
 4. Search books          9. Pay fine
 5. Issue book           10. List members
 0. Exit
================================================="""


@dataclass
class Session:
    library: Library
    today: date
    ask: Callable[[str], str]
    say: Callable[[str], None]

    def prompt(self, label: str) -> str:
        return self.ask(f"{label}: ").strip()

    def prompt_int(self, label: str, default: Optional[int] = None) -> int:
        raw = self.prompt(f"{label}" + (f" [{default}]" if default is not None else ""))
        if not raw and default is not None:
            return default
        return int(raw)  # ValueError is reported by the main loop


def add_book(s: Session) -> None:
    kind = s.prompt("Type - (b)ook for lending or (r)eference only [b]").lower() or "b"
    isbn, title, author = s.prompt("ISBN"), s.prompt("Title"), s.prompt("Author")
    if kind.startswith("r"):
        book: Book = ReferenceBook(isbn, title, author)
    else:
        book = Book(isbn, title, author, copies=s.prompt_int("Copies", default=1))
    s.library.add_book(book)
    s.say(f"Added: {book}")


def add_member(s: Session) -> None:
    kinds = "/".join(MEMBER_TYPES)
    kind = s.prompt(f"Member type ({kinds})").lower()
    if kind not in MEMBER_TYPES:
        raise ValueError(f"member type must be one of: {kinds}")
    cls = MEMBER_TYPES[kind]
    member = cls(s.prompt("Member ID"), s.prompt("Name"))
    s.library.add_member(member)
    s.say(
        f"Added {member}: up to {cls.max_books} book(s), {cls.loan_days}-day loans, "
        f"Rs {cls.fine_per_day}/day fine."
    )


def list_books(s: Session) -> None:
    books = sorted(s.library.books.values(), key=lambda b: b.title.lower())
    if not books:
        s.say("No books yet.")
    for book in books:
        s.say(f"  {book}")


def search_books(s: Session) -> None:
    results = s.library.search(s.prompt("Title / author / ISBN"))
    if not results:
        s.say("No matches.")
    for book in results:
        s.say(f"  {book}")


def issue_book(s: Session) -> None:
    txn = s.library.issue_book(s.prompt("ISBN"), s.prompt("Member ID"), on=s.today)
    s.say(f"Issued (txn #{txn.txn_id}). Due back on {txn.due_date}.")


def return_book(s: Session) -> None:
    txn = s.library.return_book(s.prompt("ISBN"), s.prompt("Member ID"), on=s.today)
    late = txn.days_overdue()
    if late:
        s.say(f"Returned {late} day(s) late. Fine charged: Rs {txn.fine}.")
    else:
        s.say("Returned on time. No fine.")


def member_loans(s: Session) -> None:
    member = s.library.get_member(s.prompt("Member ID"))
    s.say(f"{member} - fines due: Rs {member.fines_due}")
    history = s.library.history(member.member_id)
    if not history:
        s.say("  No transactions.")
    for t in history:
        title = s.library.books[t.isbn].title
        status = f"returned {t.return_date}, fine Rs {t.fine}" if t.return_date else f"due {t.due_date}"
        s.say(f"  #{t.txn_id} '{title}' issued {t.issue_date} - {status}")


def overdue_report(s: Session) -> None:
    rows = s.library.overdue_loans(on=s.today)
    if not rows:
        s.say("Nothing overdue.")
    for o in rows:
        member = s.library.members[o.transaction.member_id]
        title = s.library.books[o.transaction.isbn].title
        s.say(f"  {member.name}: '{title}' is {o.days_overdue} day(s) overdue - fine so far Rs {o.fine_so_far}")


def pay_fine(s: Session) -> None:
    member = s.library.get_member(s.prompt("Member ID"))
    s.say(f"{member.name} owes Rs {member.fines_due}.")
    remaining = s.library.pay_fine(member.member_id, s.prompt_int("Amount to pay"))
    s.say(f"Payment recorded. Remaining balance: Rs {remaining}.")


def list_members(s: Session) -> None:
    if not s.library.members:
        s.say("No members yet.")
    for m in s.library.members.values():
        loans = len(s.library.active_loans(m.member_id))
        s.say(f"  {m} - {loans}/{m.max_books} books out, fines due Rs {m.fines_due}")


ACTIONS: dict[str, Callable[[Session], None]] = {
    "1": add_book,
    "2": add_member,
    "3": list_books,
    "4": search_books,
    "5": issue_book,
    "6": return_book,
    "7": member_loans,
    "8": overdue_report,
    "9": pay_fine,
    "10": list_members,
}


def run(
    library: Library,
    *,
    today: Optional[date] = None,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
    on_change: Optional[Callable[[], None]] = None,
) -> None:
    """Menu loop. ``on_change`` fires after every successful action (used to autosave)."""
    session = Session(library, today or date.today(), input_fn, print_fn)
    print_fn(f"(today is {session.today})")
    while True:
        print_fn(MENU)
        try:
            choice = input_fn("Choose: ").strip()
        except EOFError:
            return
        if choice == "0":
            return
        action = ACTIONS.get(choice)
        if action is None:
            print_fn("Please pick one of the numbers in the menu.")
            continue
        try:
            action(session)
        except LibraryError as exc:
            print_fn(f"Error: {exc}")
        except ValueError as exc:
            print_fn(f"Invalid input: {exc}")
        except EOFError:
            return
        else:
            if on_change is not None:
                on_change()
