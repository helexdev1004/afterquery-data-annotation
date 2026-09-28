"""Work the estate out and leave the answer at /app/connections.csv."""

from __future__ import annotations

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import solver                                                 # noqa: E402


def main() -> int:
    got = solver.run("/app")
    with open("/app/connections.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["drain", "manhole"])
        for drain in sorted(got):
            writer.writerow([drain, got[drain]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
