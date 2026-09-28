"""Monitor and facade means of nitrogen dioxide for every site.

    python no2_report.py [folder]        writes folder/no2_report.csv

`report(folder, stance)` does the work. A stance is a pair: the set of download
oddities that are put right, and where an analyser is taken to stand - where
the site list says, or where its own record says.
"""

import csv
import math
import pathlib
import sys

PPB_TO_UG = 1.9125
ODDITIES = ("ppb", "milligrams", "comma")
BY_THE_RECORD = (frozenset(ODDITIES), "record")
BY_THE_LIST = (frozenset(ODDITIES), "list")
TO_THE_LETTER = (frozenset(), "list")


def town():
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "town"


def readings(path, put_right):
    """Quarter-hour means that count, in ug/m3, in order; and the oddities met."""
    lines = path.read_text().splitlines()
    met = set()
    sep = ","
    if lines[0].count(";") >= 2:
        met.add("comma")
        if "comma" not in put_right:
            return None, met
        sep = ";"
    head = lines[0].split(sep)
    factor = 1.0
    if head[1].endswith("ppb"):
        met.add("ppb")
        if "ppb" in put_right:
            factor = PPB_TO_UG
    if head[1].endswith("mg_m3"):
        met.add("milligrams")
        if "milligrams" in put_right:
            factor = 1000.0
    values = []
    for line in lines[1:]:
        stamp, text, status = line.split(sep)
        if status.strip() == "ok":
            values.append(float(text.replace(",", ".")) * factor)
        else:
            values.append(None)
    return values, met


def liveliness(values):
    """How far a quarter-hour stands from the mean of its two neighbours,
    root mean square, against the spread of the whole record."""
    good = [v for v in values if v is not None]
    mean = sum(good) / len(good)
    spread = math.sqrt(sum((v - mean) ** 2 for v in good) / len(good))
    squares, count = 0.0, 0
    for a, b, c in zip(values, values[1:], values[2:]):
        if a is not None and b is not None and c is not None:
            squares += (b - (a + c) / 2.0) ** 2
            count += 1
    return math.sqrt(squares / count) / spread


def to_facade(mean, site):
    if site["type"] != "roadside":
        return mean
    fall = lambda d: -0.5476 * math.log(d) + 2.7171
    background = float(site["local_background_ug_m3"])
    return (mean - background) / fall(float(site["monitor_to_kerb_m"])) \
        * fall(float(site["facade_to_kerb_m"])) + background


def report(folder, stance):
    """({site: (monitor mean, facade mean)}, what each download showed)."""
    put_right, standing = stance
    folder = pathlib.Path(folder)
    with open(folder / "sites.csv", newline="") as handle:
        sites = {r["site"]: r for r in csv.DictReader(handle)}
    listed = {s["analyser"]: code for code, s in sites.items()}
    shown = {}
    for analyser, code in listed.items():
        values, met = readings(folder / "downloads" / (analyser + ".csv"), put_right)
        if values is None:
            shown[analyser] = dict(listed=code, oddities=sorted(met), unread=True)
            continue
        good = [v for v in values if v is not None]
        shown[analyser] = dict(listed=code, oddities=sorted(met),
                               mean=sum(good) / len(good),
                               liveliness=liveliness(values))
    read = {a: v for a, v in shown.items() if not v.get("unread")}
    stands = {a: v["listed"] for a, v in read.items()}
    if standing == "record":
        roads = sum(1 for v in read.values() if sites[v["listed"]]["type"] == "roadside")
        order = sorted(read, key=lambda a: -read[a]["liveliness"])
        for k, analyser in enumerate(order):
            read[analyser]["looks"] = "roadside" if k < roads else "urban background"
        odd = [a for a in read if read[a]["looks"] != sites[read[a]["listed"]]["type"]]
        if len(odd) == 2:         # the two went back to each other's cabinets
            first, second = odd
            stands[first], stands[second] = read[second]["listed"], read[first]["listed"]
    out = {}
    for analyser, code in stands.items():
        read[analyser]["stands"] = code
        out[code] = (read[analyser]["mean"], to_facade(read[analyser]["mean"], sites[code]))
    return out, shown


if __name__ == "__main__":
    folder = town()
    figures, _ = report(folder, BY_THE_RECORD)
    with open(folder / "no2_report.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["site", "monitor_mean", "facade_mean"])
        for code in sorted(figures):
            out.writerow([code, "%.3f" % figures[code][0], "%.3f" % figures[code][1]])
    print("%d sites written" % len(figures))
