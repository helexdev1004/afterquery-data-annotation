"""Work out the altitudes and leave them at /app/probe_altitudes.jsonl."""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import ref                                                    # noqa: E402


def main() -> int:
    got = ref.run("/app")
    lines = []
    for reading in sorted(got):
        high, surface = got[reading].split(None, 1)
        lines.append(json.dumps({"reading": reading,
                                 "altitude_m": float(high),
                                 "surface": surface}))
    pathlib.Path("/app/probe_altitudes.jsonl").write_text(
        "\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
