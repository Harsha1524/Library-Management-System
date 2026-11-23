"""Books. ``Book`` is the base class; subclasses change the lending rules."""

from __future__ import annotations

from typing import Any, ClassVar


class Book:
    kind: ClassVar[str] = "book"
    lendable: ClassVar[bool] = True

    def __init__(self, isbn: str, title: str, author: str, copies: int = 1, available: int | None = None) -> None:
        if not isbn.strip():
            raise ValueError("ISBN is required")
        if not title.strip():
            raise ValueError("title is required")
        if copies < 1:
            raise ValueError("a book needs at least one copy")
        self.isbn = isbn.strip()
        self.title = title.strip()
        self.author = author.strip()
        self.total_copies = copies
        self.available_copies = copies if available is None else available
        if not 0 <= self.available_copies <= self.total_copies:
            raise ValueError("available copies must be between 0 and total copies")

    # -- copy accounting (called by the Library, which enforces the rules) -------
    def check_out(self) -> None:
        if self.available_copies == 0:
            raise ValueError("no copies left to check out")
        self.available_copies -= 1

    def check_in(self) -> None:
        if self.available_copies >= self.total_copies:
            raise ValueError("all copies are already checked in")
        self.available_copies += 1

    def matches(self, query: str) -> bool:
        q = query.lower()
        return q in self.title.lower() or q in self.author.lower() or q == self.isbn.lower()

    # -- persistence -------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "copies": self.total_copies,
            "available": self.available_copies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Book":
        return cls(data["isbn"], data["title"], data["author"], data["copies"], data.get("available"))

    def __str__(self) -> str:
        status = f"{self.available_copies}/{self.total_copies} available" if self.lendable else "reference only"
        return f"[{self.isbn}] {self.title} by {self.author} ({status})"


class ReferenceBook(Book):
    """Encyclopedias, dictionaries... readable in the library but never lent out."""

    kind = "reference"
    lendable = False


BOOK_TYPES: dict[str, type[Book]] = {cls.kind: cls for cls in (Book, ReferenceBook)}


def book_from_dict(data: dict[str, Any]) -> Book:
    """Rebuild the right ``Book`` subclass from saved data."""
    try:
        cls = BOOK_TYPES[data.get("kind", "book")]
    except KeyError:
        raise ValueError(f"unknown book kind {data.get('kind')!r}") from None
    return cls.from_dict(data)
