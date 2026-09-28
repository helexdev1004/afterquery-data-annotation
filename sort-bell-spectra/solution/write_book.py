"""Write the attribution and the tuning book from the tapes in a directory."""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import refimpl3


def main() -> int:
    root = pathlib.Path(sys.argv[1])
    pathlib.Path(sys.argv[2]).write_text(
        json.dumps(refimpl3.attribute(root), indent=1, sort_keys=True))
    pathlib.Path(sys.argv[3]).write_text(
        json.dumps(refimpl3.tune(root), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
