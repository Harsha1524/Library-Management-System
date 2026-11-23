"""Glue between the web page and the unchanged `library` package (runs in Pyodide)."""
import json
from collections import Counter
from datetime import date

from library import Book, Library, LibraryError, ReferenceBook
from library.member import MEMBER_TYPES

LIB: Library = Library()


def init(text):
    global LIB
    LIB = Library.from_dict(json.loads(text))
    return len(LIB.transactions)


def _ok(msg, **extra):
    return json.dumps({"ok": True, "msg": msg, **extra})


def _err(msg):
    return json.dumps({"ok": False, "msg": msg})


def apply(op_json):
    """Apply one operation, exactly as the CLI menu would. Failures change nothing."""
    op = json.loads(op_json)
    t, a, on = op["t"], op["a"], date.fromisoformat(op["on"])
    try:
        if t == "issue":
            txn = LIB.issue_book(a["isbn"], a["mid"], on=on)
            return _ok(f"Issued '{LIB.books[txn.isbn].title}' to {LIB.members[txn.member_id].name}. Due back {txn.due_date:%d %b %Y}.")
        if t == "return":
            txn = LIB.return_book(a["isbn"], a["mid"], on=on)
            late = txn.days_overdue()
            if late:
                return _ok(f"Returned {late} day(s) late. Fine charged: Rs {txn.fine}.")
            return _ok("Returned on time. No fine.")
        if t == "pay":
            left = LIB.pay_fine(a["mid"], int(a["amount"]))
            return _ok(f"Payment of Rs {int(a['amount'])} recorded. Remaining balance: Rs {left}.")
        if t == "add_book":
            if a.get("ref"):
                book = ReferenceBook(a["isbn"], a["title"], a["author"])
            else:
                book = Book(a["isbn"], a["title"], a["author"], copies=int(a.get("copies") or 1))
            LIB.add_book(book)
            return _ok(f"Added {book}")
        if t == "add_member":
            cls = MEMBER_TYPES.get(a["kind"])
            if cls is None:
                raise ValueError("unknown member type")
            m = LIB.add_member(cls(a["mid"], a["name"]))
            return _ok(f"Added {m}: up to {cls.max_books} book(s), {cls.loan_days}-day loans.")
        return _err(f"unknown action {t}")
    except LibraryError as exc:
        return _err(str(exc))
    except (ValueError, KeyError) as exc:
        return _err(f"Invalid input: {exc}")


def snapshot(today_iso):
    today = date.fromisoformat(today_iso)
    loans_by_book, loans_by_member = Counter(), Counter()
    active_by_member, monthly = Counter(), Counter()
    active, fines_charged = [], 0
    for t in LIB.transactions:
        loans_by_book[t.isbn] += 1
        loans_by_member[t.member_id] += 1
        monthly[t.issue_date.strftime("%Y-%m")] += 1
        fines_charged += t.fine
        if t.is_active:
            active_by_member[t.member_id] += 1
            over = t.days_overdue(today)
            fine = LIB.members[t.member_id].calculate_fine(over)
            active.append([t.txn_id, t.isbn, t.member_id, t.issue_date.isoformat(), t.due_date.isoformat(), over, fine])
    books = [[b.isbn, b.title, b.author, b.total_copies, b.available_copies, int(b.lendable), loans_by_book[b.isbn]]
             for b in LIB.books.values()]
    members = [[m.member_id, m.name, m.kind, m.fines_due, active_by_member[m.member_id], m.max_books,
                loans_by_member[m.member_id]] for m in LIB.members.values()]
    events = []
    for t in LIB.transactions[-400:]:
        events.append([t.issue_date.isoformat(), "issue", t.isbn, t.member_id, 0])
        if t.return_date:
            events.append([t.return_date.isoformat(), "return", t.isbn, t.member_id, t.fine])
    issues = sorted((e for e in events if e[1] == "issue"), key=lambda e: e[0], reverse=True)[:7]
    rets = sorted((e for e in events if e[1] == "return"), key=lambda e: e[0], reverse=True)[:7]
    events = [e for pair in zip(issues, rets) for e in pair]
    return json.dumps({
        "books": books, "members": members, "active": active,
        "monthly": sorted(monthly.items())[-18:], "events": events[:14],
        "fines_charged": fines_charged, "txns": len(LIB.transactions),
    })


def history(mid):
    m = LIB.get_member(mid)
    rows = [[t.txn_id, t.isbn, LIB.books[t.isbn].title, t.issue_date.isoformat(), t.due_date.isoformat(),
             t.return_date.isoformat() if t.return_date else None, t.fine] for t in LIB.history(mid)]
    return json.dumps({"id": m.member_id, "name": m.name, "kind": m.kind, "fines": m.fines_due,
                       "max": m.max_books, "loan_days": m.loan_days, "rows": rows[::-1]})


def overdue(today_iso):
    rows = []
    for o in LIB.overdue_loans(on=date.fromisoformat(today_iso)):
        t = o.transaction
        rows.append([t.txn_id, t.isbn, t.member_id, t.due_date.isoformat(), o.days_overdue, o.fine_so_far])
    return json.dumps(rows)
