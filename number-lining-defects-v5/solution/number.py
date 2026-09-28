"""Number the defects' rings and leave the answer at /app/rings.tsv."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import ref                                                    # noqa: E402


def main() -> int:
    got = ref.run("/app")
    pathlib.Path("/app/rings.tsv").write_text(
        "".join("%s\t%s\n" % (defect, got[defect]) for defect in sorted(got)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
