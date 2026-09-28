"""Trace the faults and leave the answer at /app/recall.json."""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import ref                                                    # noqa: E402


def main() -> int:
    got = ref.run("/app")
    pathlib.Path("/app/recall.json").write_text(
        json.dumps(got, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
