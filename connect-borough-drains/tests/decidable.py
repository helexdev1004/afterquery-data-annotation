"""Prove each thing the survey does not spell out can be FOUND in what ships.

    python decidable.py

This is the fairness argument and it runs before the bundle goes anywhere. A
task whose answer turns on something a careful surveyor could not have worked
out from the records is a hidden contract, not a hard problem. Every check here
reads only the files the agent's container carries.
"""

from __future__ import annotations

import collections
import csv
import json
import pathlib

import solver
import world

YARD, SEALED = solver.places()


def main() -> int:
    book = solver.load(YARD)
    truth = json.loads((SEALED / "truth.json").read_text())
    faults = []

    # ---- the gauge set the wrong way round ---------------------------------
    gauges = {row["manhole"]: int(row["litres_hour"]) for row in book["flows"]}
    falls_to = {row["manhole"]: row["falls_to"] for row in book["manholes"]}
    kids = collections.defaultdict(list)
    for manhole, parent in falls_to.items():
        if parent != "OUTFALL":
            kids[parent].append(manhole)

    crossed = [m for m in gauges if kids[m]
               and gauges[m] < sum(gauges[c] for c in kids[m])]
    if len(crossed) != 1:
        faults.append("expected exactly one chamber reading less than what "
                      "falls into it, got %d" % len(crossed))
    else:
        manhole = crossed[0]
        print("gauge    ok - %s reads %d l/h while the chambers falling into it "
              "read %d, which nothing standing above them can; and it reads the "
              "same on every visit, so no average across readings repairs it"
              % (manhole, gauges[manhole],
                 sum(gauges[c] for c in kids[manhole])))

    # ---- the old datum -----------------------------------------------------
    estate, _, _, _ = solver.build(YARD, {"gauge": "as_read",
                                          "datum": "as_booked",
                                          "storm": "ignore"})
    books = collections.defaultdict(set)
    for row in book["manholes"]:
        books[row["level_book"]].add(row["manhole"])

    def uphill(levels):
        return sum(1 for m in estate.parent if estate.parent[m]
                   and levels[m] <= levels[estate.parent[m]])

    as_booked = uphill(estate.invert)
    tried = {}
    for name, members in sorted(books.items()):
        lowered = {m: v - (world.OLD_DATUM_MM if m in members else 0)
                   for m, v in estate.invert.items()}
        tried[name] = uphill(lowered)
    winners = [n for n, wrong in tried.items() if wrong == 0]
    if as_booked == 0:
        faults.append("nothing is uphill as booked, so the datum is invisible")
    elif len(winners) != 1:
        faults.append("lowering a book leaves the estate falling in %d ways, "
                      "so which book is on the old datum is not decidable"
                      % len(winners))
    else:
        print("datum    ok - as booked %d chambers stand at or above the one "
              "they fall into; lowering book %s by %d mm leaves none, and "
              "lowering the other leaves %d"
              % (as_booked, winners[0], world.OLD_DATUM_MM,
                 tried[[n for n in tried if n != winners[0]][0]]))

    # ---- the storm ---------------------------------------------------------
    wet = [(int(r["from_min"]), int(r["to_min"])) for r in book["rain"]
           if int(r["mm"]) >= 5]
    spans = (min(a for a, _ in wet), max(b for _, b in wet)) if wet else None

    paths = {}
    for row in book["manholes"]:
        paths[row["manhole"]] = row["falls_to"]

    def below(manhole):
        out, seen = [], set()
        while manhole and manhole != "OUTFALL" and manhole not in seen:
            out.append(manhole)
            seen.add(manhole)
            manhole = paths.get(manhole)
        return out

    dosed_dry_seen_wet, impossible = set(), set()
    for row in book["tracer"]:
        drain, seen_at = row["drain"], int(row["seen_min"])
        in_wet = any(a <= seen_at <= b for a, b in wet)
        if in_wet and not any(a <= int(row["dosed_min"]) <= b for a, b in wet):
            dosed_dry_seen_wet.add(drain)
        if drain in truth and row["observer"] not in below(truth[drain]):
            impossible.add(drain)

    print("storm    ok - the rain runs %d to %d minutes; %d traces were dosed "
          "in the dry and seen in the wet, and every sighting that cannot be "
          "reached from its own drain (%d of them) falls in the wet"
          % (spans[0], spans[1], len(dosed_dry_seen_wet), len(impossible)))
    if not dosed_dry_seen_wet:
        faults.append("no trace straddles the storm, so the boundary is inert")
    if not impossible:
        faults.append("no sighting is unreachable, so the surcharge is unseen")

    # ---- the attested set must not settle the boundary ---------------------
    known = {row["drain"]: row["manhole"] for row in book["known"]}
    straddlers = dosed_dry_seen_wet & set(known)
    if straddlers:
        faults.append("the borough's own recorded drains include %d of the "
                      "traces the boundary turns on, so it can be fitted "
                      "rather than reasoned" % len(straddlers))
    else:
        print("attested ok - none of the %d recorded connections is among the "
              "traces that straddle the storm, so reproducing them cannot "
              "settle which way to read it" % len(known))

    summary = {
        "crossed": crossed[0] if len(crossed) == 1 else None,
        "crossed_reads": gauges[crossed[0]] if len(crossed) == 1 else 0,
        "crossed_above": (sum(gauges[c] for c in kids[crossed[0]])
                          if len(crossed) == 1 else 0),
        "books": {name: len(members) for name, members in sorted(books.items())},
        "uphill_as_booked": as_booked,
        "uphill_when_lowered": tried,
        "old_datum_mm": world.OLD_DATUM_MM,
        "storm_from": spans[0], "storm_to": spans[1],
        "straddling": len(dosed_dry_seen_wet),
        "unreachable_sightings": len(impossible),
        "manholes": len(estate.parent),
        "drains": len(estate.drains),
        "known": len(known),
        "graded": len(truth),
    }
    try:
        (SEALED / "decidable.json").write_text(json.dumps(summary, indent=1),
                                               newline="\n")
    except OSError:
        pass          # read-only when run from /tests; the printout is the point

    print()
    if faults:
        for fault in faults:
            print("FAILED: %s" % fault)
        return 1
    print("every departure is findable in the records as shipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
