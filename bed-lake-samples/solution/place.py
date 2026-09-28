"""Place the samples and leave the table at /app/beds_for_paper.md."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import ref                                                    # noqa: E402


def main() -> int:
    got = ref.run("/app")
    lines = ["| sample | bed |", "| --- | --- |"]
    lines += ["| %s | %s |" % (sample, got[sample]) for sample in sorted(got)]
    pathlib.Path("/app/beds_for_paper.md").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
