"""Work the estate out from the shipped records alone.

This reads only what the agent's container carries and never looks at the
truth. `READING` says how each of the three things the survey does not spell
out is taken; the reference ships with `TRUE_READING` and the ladder scores
every other way of taking them.
"""

from __future__ import annotations

import csv
import pathlib

import world

TRUE_READING = {
    # A gauge that reads a flat zero is a chamber that was stopped off, not a
    # chamber with nothing above it. Those rounds are not the estate working.
    "gauge": "own_channel",
    # One level book is worked to the old borough datum. A sewer does not run
    # uphill, and that is what gives it away.
    "datum": "correct_book",
    # The estate surcharges in heavy rain and the dye backs up. What decides
    # whether a trace was in a surcharged sewer is when it was SEEN.
    "storm": "by_sighting",
}


def places():
    """Where the records and the sealed answer live, here and as shipped.

    In the build both sit in ../yard. In the bundle the records are the ones
    the agent's container carries at /app and the sealed answer sits beside the
    grader, so ladder.py and decidable.py can be re-run exactly as they ship
    rather than needing the build tree reconstructed.
    """
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    if (yard / "truth.json").is_file():
        return yard, yard
    return pathlib.Path("/app"), here


def load(app):
    app = pathlib.Path(app)

    def rows(name):
        with open(app / name, newline="") as fh:
            return list(csv.DictReader(fh))

    return {name: rows(name + ".csv") for name in
            ("manholes", "drains", "flows", "tracer", "rain", "known")}


def build(app, reading):
    book = load(app)
    estate = world.Estate()

    for row in book["manholes"]:
        name = row["manhole"]
        falls = row["falls_to"]
        estate.parent[name] = None if falls == "OUTFALL" else falls
        estate.at[name] = (int(row["east"]), int(row["north"]))
        estate.invert[name] = int(row["invert_mm"])
        estate.cover[name] = int(row["cover_mm"])

    # ---- the datum ---------------------------------------------------------
    if reading["datum"] == "correct_book":
        # Which book is on the old datum is found, not assumed. A sewer falls
        # to its outfall, so every chamber must stand above the one it falls
        # into. Try each book on the old datum and keep the one that leaves the
        # whole estate falling.
        books = {}
        for row in book["manholes"]:
            books.setdefault(row["level_book"], set()).add(row["manhole"])

        def uphill(levels):
            return sum(1 for m in estate.parent if estate.parent[m]
                       and levels[m] <= levels[estate.parent[m]])

        best, shift_by = uphill(estate.invert), None
        for name, members in sorted(books.items()):
            tried = {m: v - (world.OLD_DATUM_MM if m in members else 0)
                     for m, v in estate.invert.items()}
            wrong = uphill(tried)
            if wrong < best:
                best, shift_by = wrong, members
        if shift_by:
            for manhole in shift_by:
                estate.invert[manhole] -= world.OLD_DATUM_MM
                estate.cover[manhole] -= world.OLD_DATUM_MM

    for row in book["drains"]:
        estate.drains[row["drain"]] = {
            "at": (int(row["east"]), int(row["north"])),
            "invert": int(row["invert_mm"]),
            "flow": int(row["litres_hour"]),
        }

    # ---- the flow survey ---------------------------------------------------
    gauges = {row["manhole"]: int(row["litres_hour"]) for row in book["flows"]}

    # A gauge is meant to read everything standing above its chamber, so it can
    # never read LESS than the chambers that fall into it. One does, because it
    # was set in the incoming channel and reads only that chamber's own drains.
    crossed = [m for m in estate.parent if estate.children(m)
               and gauges[m] < sum(gauges[c] for c in estate.children(m))]

    if reading["gauge"] == "own_channel":
        want = world.residuals(estate, gauges, crossed)
    else:
        want = world.residuals(estate, gauges)
        if reading["gauge"] == "clamp":
            # The crude repair: a chamber that comes out owing less than
            # nothing is set to nothing. It stops the search falling over and
            # still loses every drain on that chamber and below it.
            want = {m: max(0, v) for m, v in want.items()}

    # ---- the traces --------------------------------------------------------
    storm = []
    for row in book["rain"]:
        if int(row["mm"]) >= 5:
            storm.append((int(row["from_min"]), int(row["to_min"])))

    def wet(minute):
        return any(a <= minute <= b for a, b in storm)

    sightings, watched = {}, set()
    spoiled = set()
    for row in book["tracer"]:
        drain, observer = row["drain"], row["observer"]
        watched.add(observer)
        sightings.setdefault(drain, set()).add(observer)
        if reading["storm"] == "by_sighting":
            if wet(int(row["seen_min"])):
                spoiled.add(drain)
        elif reading["storm"] == "by_dosing":
            if wet(int(row["dosed_min"])):
                spoiled.add(drain)
        elif reading["storm"] == "drop_wet_sightings":
            # The crude fix: throw away the individual sightings made in the
            # wet and keep the rest of the trace. It loses the real sightings
            # along with the spurious one and under-constrains those drains.
            if wet(int(row["seen_min"])):
                sightings.setdefault(drain, set()).discard(observer)
        # "ignore" leaves spoiled empty and takes every sighting at face value

    watched = sorted(watched)
    cands = {}
    for drain in estate.drains:
        options = estate.candidates(drain, estate.invert)
        if drain in sightings and drain not in spoiled:
            options = [m for m in options
                       if {o for o in watched if o in estate.path_down(m)}
                       == sightings[drain]]
        cands[drain] = options

    known = {row["drain"]: row["manhole"] for row in book["known"]}
    return estate, want, cands, known


def best_effort(estate, want, cands, known):
    """What a surveyor does when the books will not reconcile: the best fit.

    A reading that is wrong somewhere usually leaves the gauges irreconcilable.
    Giving up then would score nothing and make every wrong account look alike,
    which is not what a competent solver would hand in - they would place the
    drains that are forced, and put the rest where they fit best. Scoring that
    is what makes the ladder mean anything.
    """
    placed = dict(known)
    free = [d for d in sorted(cands) if d not in known]

    # A drain the records leave only one chamber for is settled whatever else
    # is wrong; the rest are fitted as closely as the gauges allow.
    for drain in free:
        options = cands[drain] or sorted(estate.parent)
        placed[drain] = options[0]

    def error(assignment):
        got = {}
        for drain, manhole in assignment.items():
            got.setdefault(manhole, []).append(drain)
        total = 0
        for manhole in estate.parent:
            mine = sum(estate.drains[d]["flow"] for d in got.get(manhole, ()))
            total += abs(want.get(manhole, 0) - mine)
        return total

    current = error(placed)
    for _ in range(6):
        moved = False
        for drain in free:
            options = cands[drain] or sorted(estate.parent)
            if len(options) < 2:
                continue
            here = placed[drain]
            for option in options:
                if option == here:
                    continue
                placed[drain] = option
                fresh = error(placed)
                if fresh < current:
                    current, here, moved = fresh, option, True
                else:
                    placed[drain] = here
            placed[drain] = here
        if not moved:
            break
    return {d: placed[d] for d in free}


def run(app, reading=None):
    estate, want, cands, known = build(app, reading or TRUE_READING)
    answers = world.solve(estate, want, cands, known, cap=1)
    if answers:
        return answers[0]
    return best_effort(estate, want, cands, known)
