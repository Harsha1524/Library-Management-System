"""Entry point:  python main.py [--data library_data.json] [--demo] [--today YYYY-MM-DD]"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from library import cli, demo, storage


def main() -> None:
    parser = argparse.ArgumentParser(description="Library Management System")
    parser.add_argument("--data", default="library_data.json", help="JSON file used to persist the library")
    parser.add_argument("--demo", action="store_true", help="load sample books and members if the library is empty")
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        help="pretend today is this date (YYYY-MM-DD) - handy for trying out overdue fines",
    )
    args = parser.parse_args()

    lib = storage.load(args.data)
    if args.demo and not lib.books and not lib.members:
        demo.seed(lib)
        storage.save(lib, args.data)
        print(f"Loaded sample data into {Path(args.data).resolve()}")

    cli.run(lib, today=args.today, on_change=lambda: storage.save(lib, args.data))
    print("Goodbye!")


if __name__ == "__main__":
    main()
