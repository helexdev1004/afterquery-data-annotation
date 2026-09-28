"""Locate the peaks and leave the answer at /app/targets.txt."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import ref                                                    # noqa: E402


def main() -> int:
    got = ref.run("/app")
    pathlib.Path("/app/targets.txt").write_text(
        "".join("%s %s\n" % (anomaly, got[anomaly])
                for anomaly in sorted(got)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
