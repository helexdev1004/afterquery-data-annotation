"""Grade the pulled boards and leave the answer at /app/grades.csv."""

from __future__ import annotations

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import grader_ref                                             # noqa: E402


def main() -> int:
    got = grader_ref.run("/app")
    with open("/app/grades.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["board", "grade"])
        for board in sorted(got):
            writer.writerow([board, got[board]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
