"""Members. The fine policy is where inheritance and polymorphism earn their keep.

``Member`` is abstract: it owns identity, the outstanding-fine balance and the
shared ``calculate_fine`` template, and leaves the pricing rule to subclasses.
Everything else in the system just calls ``member.calculate_fine(days)`` and
``member.max_books`` without knowing -- or caring -- which kind of member it has.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Any, ClassVar


class Member(ABC):
    kind: ClassVar[str]
    max_books: ClassVar[int]  # how many titles may be on loan at once
    loan_days: ClassVar[int]  # standard loan period
    fine_per_day: ClassVar[int]  # rupees per overdue day

    def __init__(self, member_id: str, name: str, fines_due: int = 0) -> None:
        if not member_id.strip():
            raise ValueError("member ID is required")
        if not name.strip():
            raise ValueError("name is required")
        if fines_due < 0:
            raise ValueError("fines due cannot be negative")
        self.member_id = member_id.strip()
        self.name = name.strip()
        self.fines_due = fines_due

    def due_date(self, issued_on: date) -> date:
        return issued_on + timedelta(days=self.loan_days)

    def calculate_fine(self, days_overdue: int) -> int:
        """Template method: no fine unless overdue, otherwise defer to the subclass."""
        if days_overdue <= 0:
            return 0
        return self._fine_for_overdue(days_overdue)

    @abstractmethod
    def _fine_for_overdue(self, days_overdue: int) -> int:
        """Fine for a loan that is ``days_overdue`` (>= 1) days late."""

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "member_id": self.member_id, "name": self.name, "fines_due": self.fines_due}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Member":
        return cls(data["member_id"], data["name"], data.get("fines_due", 0))

    def __str__(self) -> str:
        return f"{self.name} ({self.member_id}, {self.kind})"


class StudentMember(Member):
    """Simple rule: a flat rate for every day late."""

    kind = "student"
    max_books = 3
    loan_days = 14
    fine_per_day = 2

    def _fine_for_overdue(self, days_overdue: int) -> int:
        return days_overdue * self.fine_per_day


class FacultyMember(Member):
    """Longer loans, more books, and a grace period before fines start."""

    kind = "faculty"
    max_books = 10
    loan_days = 30
    fine_per_day = 1
    grace_days = 7

    def _fine_for_overdue(self, days_overdue: int) -> int:
        return max(0, days_overdue - self.grace_days) * self.fine_per_day


class GuestMember(Member):
    """Short loans and a stiff penalty: a flat late fee plus a daily rate, capped."""

    kind = "guest"
    max_books = 1
    loan_days = 7
    fine_per_day = 5
    late_fee = 20
    fine_cap = 500

    def _fine_for_overdue(self, days_overdue: int) -> int:
        return min(self.fine_cap, self.late_fee + days_overdue * self.fine_per_day)


MEMBER_TYPES: dict[str, type[Member]] = {cls.kind: cls for cls in (StudentMember, FacultyMember, GuestMember)}


def member_from_dict(data: dict[str, Any]) -> Member:
    """Rebuild the right ``Member`` subclass from saved data."""
    try:
        cls = MEMBER_TYPES[data["kind"]]
    except KeyError:
        raise ValueError(f"unknown member kind {data.get('kind')!r}") from None
    return cls.from_dict(data)
