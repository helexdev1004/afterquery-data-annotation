"""The solver a frontier agent actually writes in seventy seconds.

Three submissions were solved 3/3 in 69-122 seconds, and the reason turned out
to be that every defect had a generic defence costing no insight: the median
across gauge rounds dodged the stopped chamber, the uphill test fixed the datum,
and binning any trace constraint nothing satisfied dealt with the storm. That
version scored 40 of 40 here.

So this is now a build gate. It plays every defensive move a competent solver
makes WITHOUT understanding the records - clamp what is impossible, drop what
will not fit, take what is robust - and the bundle must not ship if any of them
reaches the bar.
"""

from __future__ import annotations

import collections
import json

import solver
import world

RECORDS, SEALED = solver.places()


def main() -> int:
    truth = json.loads((SEALED / "truth.json").read_text())
    book = solver.load(RECORDS)

    estate = world.Estate()
    for row in book["manholes"]:
        estate.parent[row["manhole"]] = (
            None if row["falls_to"] == "OUTFALL" else row["falls_to"])
        estate.at[row["manhole"]] = (int(row["east"]), int(row["north"]))
        estate.invert[row["manhole"]] = int(row["invert_mm"])
    for row in book["drains"]:
        estate.drains[row["drain"]] = {
            "at": (int(row["east"]), int(row["north"])),
            "invert": int(row["invert_mm"]),
            "flow": int(row["litres_hour"]),
        }

    # the uphill test, applied with no thought about what a level book is
    books = collections.defaultdict(set)
    for row in book["manholes"]:
        books[row["level_book"]].add(row["manhole"])

    def uphill(levels):
        return sum(1 for m in estate.parent if estate.parent[m]
                   and levels[m] <= levels[estate.parent[m]])

    for members in books.values():
        lowered = {m: v - (world.OLD_DATUM_MM if m in members else 0)
                   for m, v in estate.invert.items()}
        if uphill(lowered) < uphill(estate.invert):
            estate.invert = lowered

    gauges = {row["manhole"]: int(row["litres_hour"]) for row in book["flows"]}

    sightings, watched = collections.defaultdict(set), set()
    for row in book["tracer"]:
        watched.add(row["observer"])
        sightings[row["drain"]].add(row["observer"])
    watched = sorted(watched)
    known = {row["drain"]: row["manhole"] for row in book["known"]}

    cands = {}
    for drain in estate.drains:
        options = estate.candidates(drain, estate.invert)
        if drain in sightings:
            keep = [m for m in options
                    if {o for o in watched if o in estate.path_down(m)}
                    == sightings[drain]]
            # nothing fits the sightings, so bin the trace and carry on
            options = keep or options
        cands[drain] = options

    plain = world.residuals(estate, gauges)
    crossed = [m for m in estate.parent if estate.children(m)
               and gauges[m] < sum(gauges[c] for c in estate.children(m))]

    ways = {
        "as read": plain,
        "clamp what is negative": {m: max(0, v) for m, v in plain.items()},
        "absolute value": {m: abs(v) for m, v in plain.items()},
        "drop the odd chamber": {m: v for m, v in plain.items()
                                 if m not in crossed},
        "and drop its parent too": {
            m: v for m, v in plain.items()
            if m not in crossed
            and m not in {estate.parent[c] for c in crossed}},
    }

    worst = 0
    for name, want in sorted(ways.items()):
        answers = world.solve(estate, want, cands, known, cap=1)
        got = answers[0] if answers else solver.best_effort(
            estate, want, cands, known)
        right = sum(1 for d in truth if got.get(d) == truth[d])
        worst = max(worst, right)
        print("  %-26s -> %2d of %d" % (name, right, len(truth)))

    print()
    print("the best a solver gets without understanding anything: %d of %d"
          % (worst, len(truth)))
    try:
        (SEALED / "generic.json").write_text(
            json.dumps({"generic": worst, "total": len(truth)}, indent=1),
            newline="\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
