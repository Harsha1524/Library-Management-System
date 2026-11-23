import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from library import FacultyMember, GuestMember, Library, ReferenceBook, StudentMember, cli, demo, storage

TODAY = date(2025, 4, 1)


def seeded() -> Library:
    lib = Library()
    demo.seed(lib)
    return lib


class StorageTests(unittest.TestCase):
    def test_missing_file_gives_an_empty_library(self):
        with tempfile.TemporaryDirectory() as d:
            lib = storage.load(Path(d) / "nope.json")
            self.assertEqual((lib.books, lib.members, lib.transactions), ({}, {}, []))

    def test_roundtrip_preserves_everything(self):
        lib = seeded()
        lib.issue_book("9780132350884", "S001", on=TODAY)
        lib.issue_book("9780201633610", "S001", on=TODAY)
        lib.return_book("9780201633610", "S001", on=TODAY + timedelta(days=20))  # late -> fine

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sub" / "lib.json"  # parent directory is created on demand
            storage.save(lib, path)
            restored = storage.load(path)
            self.assertEqual(list(Path(d, "sub").iterdir()), [path])  # no temp files left behind

        self.assertEqual(restored.to_dict(), lib.to_dict())
        self.assertIsInstance(restored.get_member("F001"), FacultyMember)
        self.assertIsInstance(restored.get_member("G001"), GuestMember)
        self.assertIsInstance(restored.get_book("9780198611868"), ReferenceBook)
        self.assertEqual(restored.get_member("S001").fines_due, 12)
        # state keeps working after a reload, including transaction numbering
        txn = restored.issue_book("9780134494166", "F001", on=TODAY)
        self.assertEqual(txn.txn_id, 3)

    def test_saved_file_is_plain_json(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "lib.json"
            storage.save(seeded(), path)
            data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(set(data), {"next_txn_id", "books", "members", "transactions"})


class ScriptedIO:
    """Feeds canned answers to the CLI and records what it prints."""

    def __init__(self, *answers: str):
        self._answers = iter(answers)
        self.output: list[str] = []

    def ask(self, prompt: str) -> str:
        try:
            return next(self._answers)
        except StopIteration:
            raise EOFError from None

    def say(self, text: str) -> None:
        self.output.append(text)

    @property
    def text(self) -> str:
        return "\n".join(self.output)


class CliTests(unittest.TestCase):
    def run_cli(self, lib, *answers, today=TODAY, on_change=None):
        io = ScriptedIO(*answers)
        cli.run(lib, today=today, input_fn=io.ask, print_fn=io.say, on_change=on_change)
        return io

    def test_issue_and_return_flow(self):
        lib = seeded()
        io = self.run_cli(lib, "5", "9780132350884", "S001", "6", "9780132350884", "S001", "0")
        self.assertIn("Issued (txn #1). Due back on 2025-04-15.", io.text)
        self.assertIn("Returned on time. No fine.", io.text)

    def test_late_return_reports_the_fine(self):
        lib = seeded()
        lib.issue_book("9780132350884", "S001", on=TODAY - timedelta(days=20))  # due 6 days ago
        io = self.run_cli(lib, "6", "9780132350884", "S001", "0")
        self.assertIn("Returned 6 day(s) late. Fine charged: Rs 12.", io.text)

    def test_business_rule_errors_are_reported_not_raised(self):
        io = self.run_cli(seeded(), "5", "9780198611868", "S001", "0")  # reference book
        self.assertIn("Error: 'Oxford English Dictionary' is a reference book", io.text)

    def test_bad_input_is_reported_not_raised(self):
        io = self.run_cli(seeded(), "2", "alien", "0")
        self.assertIn("Invalid input: member type must be one of", io.text)
        io = self.run_cli(seeded(), "1", "b", "X1", "Title", "Author", "lots", "0")
        self.assertIn("Invalid input", io.text)
        io = self.run_cli(seeded(), "banana", "0")
        self.assertIn("Please pick one of the numbers", io.text)

    def test_add_book_and_member(self):
        lib = Library()
        self.run_cli(lib, "1", "b", "X1", "Dune", "Herbert", "3", "2", "student", "S9", "Zed", "0")
        self.assertEqual(lib.get_book("X1").total_copies, 3)
        self.assertIsInstance(lib.get_member("S9"), StudentMember)

    def test_overdue_report_and_fine_payment(self):
        lib = seeded()
        lib.issue_book("9780132350884", "G001", on=TODAY - timedelta(days=17))  # guest: 10 days late
        io = self.run_cli(lib, "8", "0")
        self.assertIn("Sam Fernandes: 'Clean Code' is 10 day(s) overdue - fine so far Rs 70", io.text)

        lib.return_book("9780132350884", "G001", on=TODAY)
        io = self.run_cli(lib, "9", "G001", "70", "0")
        self.assertIn("Remaining balance: Rs 0.", io.text)

    def test_on_change_fires_only_after_successful_actions(self):
        calls = []
        self.run_cli(seeded(), "3", "5", "bogus", "S001", "0", on_change=lambda: calls.append(1))
        self.assertEqual(len(calls), 1)  # list books succeeded; the failed issue did not count

    def test_ends_cleanly_when_input_runs_out(self):
        self.run_cli(seeded(), "5", "9780132350884")  # EOF in the middle of an action


if __name__ == "__main__":
    unittest.main()
