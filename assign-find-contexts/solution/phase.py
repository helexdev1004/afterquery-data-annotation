"""Phase the finds and leave the answer at /app/contexts.csv."""

from __future__ import annotations

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import ref                                                    # noqa: E402


def main() -> int:
    got = ref.run("/app")
    with open("/app/contexts.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["find", "context"])
        for find in sorted(got):
            writer.writerow([find, got[find]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
