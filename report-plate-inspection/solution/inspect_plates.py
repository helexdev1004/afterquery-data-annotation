"""Write the inspection report for every plate in a directory."""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import refimpl


def main() -> int:
    plates_dir = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2])
    reports = []
    for path in sorted(plates_dir.glob("*.json")):
        reports.append(refimpl.inspect(json.loads(path.read_text())))
    out.write_text(json.dumps(reports, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
