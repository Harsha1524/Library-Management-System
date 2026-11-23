# Library Management System

**Live demo:** https://harsha-library-management.vercel.app · **Report:** [docs/Deployment_Report.pdf](docs/Deployment_Report.pdf)

The web demo runs this exact `library` package in your browser (Pyodide / WebAssembly), loaded with
18 months of simulated activity from a large college library: 1,917 titles, 7,081 copies, 1,465 members
and 19,780 loans. Your changes are saved in your own browser (use *reset* in the header to start over).

A menu-driven Library Management System designed with **OOP principles**: modular classes for **books**,
**members** and **transactions**, with **issue/return tracking** and **fine calculation through inheritance
and polymorphism**. Pure Python 3.10+, standard library only.

## Run it

```powershell
python main.py --demo          # first run: loads sample books & members
python main.py                 # afterwards: picks up where you left off (library_data.json)
```

Want to see fines without waiting two weeks? Pretend it is a later date:

```powershell
python main.py --today 2025-05-01
```

```
=========== Library Management System ===========
 1. Add book              6. Return book
 2. Add member            7. Member's loans & history
 3. List books            8. Overdue report
 4. Search books          9. Pay fine
 5. Issue book           10. List members
 0. Exit
```

Data is saved to `library_data.json` (override with `--data PATH`) after every successful action.

## Design

```
library/
  book.py         Book  ◄── ReferenceBook             (lendable or not)
  member.py       Member (abstract) ◄── StudentMember / FacultyMember / GuestMember
  transaction.py  Transaction                         (one loan: issue → due → return, fine)
  service.py      Library                             (enforces the rules, owns the collections)
  exceptions.py   LibraryError ◄── BorrowLimitError, NoCopiesAvailableError, ...
  storage.py      JSON save/load (atomic write)
  cli.py          menu front end
```

### Inheritance & polymorphism: fines

`Member` is abstract. It owns identity, the fine balance, and a **template method**:

```python
def calculate_fine(self, days_overdue):      # shared guard: on time → 0
    if days_overdue <= 0:
        return 0
    return self._fine_for_overdue(days_overdue)   # ← each subclass supplies the rule
```

`Library.return_book` just calls `member.calculate_fine(days_late)` — it never checks what kind of member it
is. Adding a new membership type means one new subclass, with no changes to the service.

| Member | Max books | Loan | Fine rule | 10 days late |
| --- | --- | --- | --- | --- |
| `StudentMember` | 3 | 14 days | Rs 2 / day | Rs 20 |
| `FacultyMember` | 10 | 30 days | Rs 1 / day after a 7-day grace period | Rs 3 |
| `GuestMember` | 1 | 7 days | Rs 20 flat + Rs 5 / day, capped at Rs 500 | Rs 70 |

`Book` / `ReferenceBook` follow the same idea: `ReferenceBook.lendable` is `False`, so the library refuses
to issue it without any special-casing by type.

### Rules enforced by `Library`

* Reference books can't be borrowed; every title has a copy count and can't be over-issued.
* A member can't exceed their membership's book limit, or hold two copies of the same title.
* Fines are charged to the member when a book is returned; **unpaid fines block further borrowing** until
  paid (`Pay fine`, partial payments allowed).
* Every rule violation raises a specific `LibraryError` subclass; a failed operation changes nothing.

## Tests

```powershell
python -m unittest -v
```

52 tests: fine rules per member type (boundaries like the faculty grace period and the guest cap),
issue/return/limit/fine workflows, overdue report, JSON round-trips (subclasses survive a reload), and the
CLI driven by scripted input.

## Web app (`web/`) and deployment

```
web/index.html               single-page UI: desk dashboard, catalogue, members, issue/return, overdue
web/bridge.py                glue: calls Library.issue_book / return_book / pay_fine / overdue_loans
web/data/library_data.json   seed data (normal library_data.json format + a `meta` block)
tools/seed.py                generates the seed by driving the real Library class day by day
vercel.json                  static hosting config ("/" -> web/index.html, no build step)
```

The page loads Pyodide 0.26.4 from the jsDelivr CDN, fetches `library/*.py` and `web/bridge.py` straight
from this repo, writes them into Pyodide's file system and imports them, so the site always runs the same
code as the CLI. No server, no database: visitor actions are stored as an operation log in `localStorage`
and replayed on load.

Run locally (any static server from the repo root):

```bash
python -m http.server 8000      # then open http://localhost:8000/web/
python main.py --data web/data/library_data.json --today 2026-12-31   # same data in the CLI
python tools/seed.py . web/data/library_data.json                     # regenerate the seed
python -m unittest -v                                                 # 52 tests
```

Deploy: import the repo in Vercel (framework preset *Other*, no build command, root directory `/`),
with this branch as the production branch. Every push redeploys automatically.
