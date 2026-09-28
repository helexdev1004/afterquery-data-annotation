"""Work out the probes' altitudes and surfaces from the shipped records alone.

This reads only what the agent's container carries and never looks at the
answer. `TRUE_READING` is how the logs have to be read; gates.py scores every
other way of reading them.
"""

from __future__ import annotations

import bisect
import csv
import pathlib
from fractions import Fraction

import survey

TRUE_READING = {
    # One wheel counted feet: it rolled three and a quarter times the length
    # of its path.
    "feet": "to_metres",
    # One wheel counted miles: it rolled six or seven of something.
    "miles": "to_metres",
    # One logger wrote what the wheel rolled in each ten seconds, not the
    # running total: its distances go up and down and never pass fifteen.
    "increments": "summed",
    # One logger wrote the seconds since the walk began, not the time of day.
    "elapsed": "to_clock",
    # The protocol starts a walk at the foot of the path. Two walks were made
    # from the top. Nothing says which, and no pace says it either: these are
    # railway grades and nobody slows on them. The wheel says it. It runs
    # true on tarmac and chatters on ballast, so the ground it covers from
    # one ten seconds to the next is steady on one and ragged on the other;
    # read from the wrong end the ragged stretches fall on the tarmac.
    "walked_from": "by_the_chatter",
}

OTHERS = {
    "feet": "as_logged",
    "miles": "as_logged",
    "increments": "as_logged",
    "elapsed": "as_logged",
    # the natural reading: every walk began at the foot, as the protocol says
    "walked_from": "from_the_foot",
}

EXTRAS = {"walked_from": ("from_the_top",)}


def places():
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    if (yard / "truth.json").is_file():
        return yard, yard
    return pathlib.Path("/app"), here


def rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def fit(xs, ys):
    """Pearson's r."""
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / (sxx * syy) ** 0.5 if sxx and syy else 0.0


def build(app, reading):
    app = pathlib.Path(app)
    paths = {}
    for row in rows(app / "paths.csv"):
        paths[row["path"]] = {"began": survey.clock(row["walk_began"]),
                              "stations": [], "surfaces": []}
    for row in rows(app / "stations.csv"):
        paths[row["path"]]["stations"].append(
            (survey.mm(row["distance_m"]), survey.mm(row["altitude_m"])))
    for row in rows(app / "surfaces.csv"):
        paths[row["path"]]["surfaces"].append(
            (survey.mm(row["from_m"]), survey.mm(row["to_m"]),
             row["surface"]))

    for name, p in paths.items():
        p["stations"].sort()
        length = p["stations"][-1][0]
        log = rows(app / "wheel" / (name + ".csv"))
        figures = [Fraction(r["distance_m"]) for r in log]

        # ---- the logger's habit, found and not assumed ----------------------
        habit = None
        if any(b < a for a, b in zip(figures, figures[1:])):
            habit = "increments"
        elif abs(figures[-1] * survey.FOOT_MM - length) * 200 < length:
            habit = "feet"
        elif abs(figures[-1] * survey.MILE_MM - length) * 200 < length:
            habit = "miles"
        clocks = ":" in log[0]["time"]
        p["habits"] = [h for h in (habit, None if clocks else "elapsed") if h]

        unit = 1000
        if habit == "feet" and reading["feet"] == "to_metres":
            unit = survey.FOOT_MM
        elif habit == "miles" and reading["miles"] == "to_metres":
            unit = survey.MILE_MM
        rolled = [int(round(f * unit)) for f in figures]
        if habit == "increments" and reading["increments"] == "summed":
            total, summed = 0, []
            for step in rolled:
                total += step
                summed.append(total)
            rolled = summed
        if clocks:
            times = [survey.clock(r["time"]) for r in log]
        elif reading["elapsed"] == "to_clock":
            times = [p["began"] + int(r["time"]) for r in log]
        else:
            times = [int(r["time"]) for r in log]      # as if seconds of the day
        p["times"], p["rolled"], p["length"] = times, rolled, length

        # ---- which end the walk began at -------------------------------------
        # how far each ten seconds on the move strays from the ten seconds
        # either side of it: the middle value on the roughest surface over
        # the middle value on the smoothest. The middle value, because a
        # walker's odd minute of fuss falls anywhere and is no surface's.
        strays = []
        for a, b, c, d in zip(rolled, rolled[1:], rolled[2:], rolled[3:]):
            steps = (b - a, c - b, d - c)
            if min(steps) < 1500 or d > length:         # standing, or not on it
                continue
            strays.append(((b + c) // 2,
                           abs(steps[1] - (steps[0] + steps[2]) / 2.0)
                           / steps[1]))
        p["fits"] = {}
        kinds = sorted(survey.ROUGHNESS, key=survey.ROUGHNESS.get)
        for end in ("foot", "top"):
            on = {kind: [] for kind in kinds}
            for at, stray in strays:
                chainage = at if end == "foot" else length - at
                for low, high, kind in p["surfaces"]:
                    # ten metres in from a change of surface, to be on it
                    if low + 10000 <= chainage < high - 10000:
                        on[kind].append(stray)
            middle = {kind: sorted(v)[len(v) // 2] if v else 0.0
                      for kind, v in on.items()}
            p["fits"][end] = middle[kinds[-1]] / max(middle[kinds[0]], 1e-9)
        p["from_top"] = {
            "by_the_chatter": p["fits"]["top"] > p["fits"]["foot"],
            "from_the_foot": False,
            "from_the_top": True}[reading["walked_from"]]
    return paths


def altitude(stations, chainage):
    for (a, low), (b, high) in zip(stations, stations[1:]):
        if a <= chainage <= b:
            return low + Fraction(high - low) * (chainage - a) / (b - a)
    return None


def run(app, reading=None):
    reading = reading or TRUE_READING
    app = pathlib.Path(app)
    paths = build(app, reading)
    wanted = set((app / "paper.txt").read_text().split())
    out = {}
    for row in rows(app / "readings.csv"):
        if row["reading"] not in wanted:
            continue
        p = paths[row["path"]]
        spoken = survey.clock(row["time"])
        at = bisect.bisect_right(p["times"], spoken) - 1
        at = max(0, min(at, len(p["times"]) - 1))
        rolled = p["rolled"][at]
        if at + 1 < len(p["times"]) and p["times"][at + 1] > p["times"][at]:
            share = Fraction(spoken - p["times"][at],
                             p["times"][at + 1] - p["times"][at])
            rolled += (p["rolled"][at + 1] - rolled) * min(share, 1)
        chainage = p["length"] - rolled if p["from_top"] else rolled
        high = altitude(p["stations"], chainage)
        kind = [k for a, b, k in p["surfaces"] if a <= chainage < b]
        out[row["reading"]] = "NONE" if high is None or not kind \
            else "%.1f %s" % (float(high) / 1000.0, kind[0])
    return out
