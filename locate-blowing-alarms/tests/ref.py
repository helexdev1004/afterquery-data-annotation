"""Work out where each alarm sounded from the shipped records alone.

This reads only what the agent's container carries and never looks at the
answer. `TRUE_READING` is how the logs have to be read; gates.py scores every
other way of reading them.
"""

from __future__ import annotations

import bisect
import csv
import pathlib
from fractions import Fraction

import blowing

TRUE_READING = {
    # One machine counts feet: it paid out three and a quarter times the
    # length of its route.
    "feet": "to_metres",
    # One counts centimetres: a hundred times it.
    "centimetres": "to_metres",
    # One writes what was paid out in each second, not the running total: its
    # figures go up and down and never pass two.
    "per_second": "summed",
    # One writes the seconds since the blow began, not the time of day.
    "elapsed": "to_clock",
    # The procedure sets the machine up at the A chamber. Two routes were
    # blown from the far chamber. Nothing says which, and no speed says it: the
    # machine holds its set speed in any duct. The cable says it. It runs
    # sweetly into smoothwall and raggedly into old earthenware, so the length
    # paid out from one second to the next is steady in the one and ragged in
    # the other; read from the wrong end the ragged stretches fall in the
    # smoothwall.
    "blown_from": "by_the_raggedness",
}

OTHERS = {
    "feet": "as_logged",
    "centimetres": "as_logged",
    "per_second": "as_logged",
    "elapsed": "as_logged",
    # the natural reading: every route blown from its A chamber
    "blown_from": "from_a",
}

EXTRAS = {"blown_from": ("from_the_far_end",)}


def places():
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    if (yard / "truth.json").is_file():
        return yard, yard
    return pathlib.Path("/app"), here


def rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def build(app, reading):
    app = pathlib.Path(app)
    routes = {}
    for row in rows(app / "routes.csv"):
        routes[row["route"]] = {"began": blowing.clock(row["blow_began"]),
                                "ducts": []}
    for row in rows(app / "ducts.csv"):
        routes[row["route"]]["ducts"].append(
            (blowing.mm(row["from_m"]), blowing.mm(row["to_m"]), row["duct"]))

    for name, r in routes.items():
        r["ducts"].sort()
        length = r["ducts"][-1][1]
        log = rows(app / "blows" / (name + ".csv"))
        figures = [Fraction(row["paid_out_m"]) for row in log]

        # ---- the crew's habit, found and not assumed ------------------------
        habit = None
        if any(b < a for a, b in zip(figures, figures[1:])):
            habit = "per_second"
        elif abs(figures[-1] * blowing.FOOT_MM - length) * 200 < length:
            habit = "feet"
        elif abs(figures[-1] * 10 - length) * 200 < length:
            habit = "centimetres"
        clocks = ":" in log[0]["time"]
        r["habits"] = [h for h in (habit, None if clocks else "elapsed") if h]

        unit = 1000
        if habit == "feet" and reading["feet"] == "to_metres":
            unit = blowing.FOOT_MM
        elif habit == "centimetres" and reading["centimetres"] == "to_metres":
            unit = 10
        paid = [int(round(f * unit)) for f in figures]
        if habit == "per_second" and reading["per_second"] == "summed":
            total, summed = 0, []
            for step in paid:
                total += step
                summed.append(total)
            paid = summed
        if clocks:
            times = [blowing.clock(row["time"]) for row in log]
        elif reading["elapsed"] == "to_clock":
            times = [r["began"] + int(row["time"]) for row in log]
        else:
            times = [int(row["time"]) for row in log]   # as if seconds of the day
        r["times"], r["paid"], r["length"] = times, paid, length

        # ---- which end the route was blown from ------------------------------
        # how far each second on the move strays from the seconds either side
        # of it: the middle value in the roughest duct over the middle value in
        # the smoothest. The middle value, because a crew's odd half minute of
        # fuss falls anywhere and is no duct's.
        strays = []
        for a, b, c, d in zip(paid, paid[1:], paid[2:], paid[3:]):
            steps = (b - a, c - b, d - c)
            if min(steps) < 300 or d > length:          # stopped, or not on it
                continue
            strays.append(((b + c) // 2,
                           abs(steps[1] - (steps[0] + steps[2]) / 2.0)
                           / steps[1]))
        kinds = sorted(blowing.ROUGHNESS, key=blowing.ROUGHNESS.get)
        r["fits"] = {}
        for end in ("a", "far"):
            on = {kind: [] for kind in kinds}
            for at, stray in strays:
                head = at if end == "a" else length - at
                for low, high, kind in r["ducts"]:
                    # five metres in from a change of duct, to be in it
                    if low + 5000 <= head < high - 5000:
                        on[kind].append(stray)
            middle = {kind: sorted(v)[len(v) // 2] if v else 0.0
                      for kind, v in on.items()}
            r["fits"][end] = middle[kinds[-1]] / max(middle[kinds[0]], 1e-9)
        r["from_far"] = {
            "by_the_raggedness": r["fits"]["far"] > r["fits"]["a"],
            "from_a": False,
            "from_the_far_end": True}[reading["blown_from"]]
    return routes


def run(app, reading=None):
    reading = reading or TRUE_READING
    app = pathlib.Path(app)
    routes = build(app, reading)
    wanted = set((app / "follow_up.txt").read_text().split())
    out = {}
    for row in rows(app / "alarms.csv"):
        if row["alarm"] not in wanted:
            continue
        r = routes[row["route"]]
        sounded = blowing.clock(row["time"])
        at = bisect.bisect_right(r["times"], sounded) - 1
        at = max(0, min(at, len(r["times"]) - 1))
        paid = r["paid"][at]
        head = r["length"] - paid if r["from_far"] else paid
        kind = [k for a, b, k in r["ducts"] if a <= head < b]
        out[row["alarm"]] = "%.1f %s" % (head / 1000.0,
                                         kind[0] if kind else "NONE")
    return out
