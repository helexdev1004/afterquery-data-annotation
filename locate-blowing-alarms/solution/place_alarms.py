"""Place the alarms and leave the dig sheet at /app/dig_sheet.csv."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import ref                                                    # noqa: E402


def main() -> int:
    got = ref.run("/app")
    lines = ["alarm,from_a_m,duct"]
    for alarm in sorted(got):
        far, duct = got[alarm].split(None, 1)
        lines.append("%s,%s,%s" % (alarm, far, duct))
    pathlib.Path("/app/dig_sheet.csv").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
