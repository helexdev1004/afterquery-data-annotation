"""The obvious wrong answer: take the nearest chamber that is low enough.

This is what a solver gets by taking each drain on its own, and it must score
well under the bar or the task is not carrying its difficulty.
"""

import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import world                                                  # noqa: E402


def main():
    app = pathlib.Path("/app")
    estate = world.Estate()
    with open(app / "manholes.csv", newline="") as handle:
        for row in csv.DictReader(handle):
            estate.parent[row["manhole"]] = (
                None if row["falls_to"] == "OUTFALL" else row["falls_to"])
            estate.at[row["manhole"]] = (int(row["east"]), int(row["north"]))
            estate.invert[row["manhole"]] = int(row["invert_mm"])

    known = set()
    with open(app / "known.csv", newline="") as handle:
        known = {row["drain"] for row in csv.DictReader(handle)}

    out = []
    with open(app / "drains.csv", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["drain"] in known:
                continue
            spot = (int(row["east"]), int(row["north"]))
            best, far = None, None
            for manhole in estate.parent:
                gap = world.distance(spot, estate.at[manhole])
                if gap and int(row["invert_mm"]) > estate.invert[manhole]:
                    if far is None or gap < far:
                        best, far = manhole, gap
            out.append((row["drain"], best or "MH01"))

    with open("/app/connections.csv", "w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["drain", "manhole"])
        writer.writerows(sorted(out))


if __name__ == "__main__":
    main()
