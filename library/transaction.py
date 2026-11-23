"""A transaction records one loan from issue to return."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Optional


@dataclass
class Transaction:
    txn_id: int
    isbn: str
    member_id: str
    issue_date: date
    due_date: date
    return_date: Optional[date] = None
    fine: int = 0  # settled when the book is returned

    @property
    def is_active(self) -> bool:
        return self.return_date is None

    def days_overdue(self, on: Optional[date] = None) -> int:
        """Days past the due date, measured at the return date (or ``on`` if still out)."""
        end = self.return_date or on
        if end is None:
            raise ValueError("need a reference date for a loan that has not been returned")
        return max(0, (end - self.due_date).days)

    def to_dict(self) -> dict[str, Any]:
        return {
            "txn_id": self.txn_id,
            "isbn": self.isbn,
            "member_id": self.member_id,
            "issue_date": self.issue_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "fine": self.fine,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        returned = data.get("return_date")
        return cls(
            txn_id=data["txn_id"],
            isbn=data["isbn"],
            member_id=data["member_id"],
            issue_date=date.fromisoformat(data["issue_date"]),
            due_date=date.fromisoformat(data["due_date"]),
            return_date=date.fromisoformat(returned) if returned else None,
            fine=data.get("fine", 0),
        )
