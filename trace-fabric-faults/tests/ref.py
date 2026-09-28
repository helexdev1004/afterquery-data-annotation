"""Trace the faults from the shipped records alone.

This reads only what the agent's container carries and never looks at the
answer. `TRUE_READING` is how the records have to be read; gates.py scores
every other way of reading them.
"""

from __future__ import annotations

import csv
import pathlib
from fractions import Fraction

import cutroom

TRUE_READING = {
    # One inspector books the distance along the roll in yards: his faults run
    # on past the end of the roll.
    "yards": "to_metres",
    # One inspector books the distance across the roll in inches: his faults
    # stand forty times the roll's width from the selvedge.
    "inches": "to_metres",
    # One inspector books across before along.
    "columns": "unswap",
    # One inspector runs his counter from the last seam he passed rather than
    # from the head of the roll: his distances fall back at every seam.
    "counter": "from_the_head",
    # A roll comes off the inspection frame wound with its first-seen end at the
    # core, so it is laid up tail first - turned end for end, and so side for
    # side - unless it was re-rolled in between, and nothing says which rolls
    # were. The lay says it: a mill seam is never cut into a panel, the lay is
    # parted at it, so the seams the inspector booked stand in the gaps of the
    # cut plan with the roll taken the right way about, and inside panels with
    # it taken the wrong way.
    "lay": "by_the_seams",
}

OTHERS = {
    "yards": "as_booked",
    "inches": "as_booked",
    "columns": "as_booked",
    "counter": "as_booked",
    # the natural reading: the lay runs the way the inspection did
    "lay": "as_inspected",
}

# Two more ways of taking the lay, scored alongside: every roll tail first, and
# a roll turned end for end but not side for side.
EXTRAS = {"lay": ("all_tail_first", "end_for_end_only")}


def places():
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    if (yard / "truth.json").is_file():
        return yard, yard
    return pathlib.Path("/app"), here


def load(app):
    app = pathlib.Path(app)

    def rows(name):
        with open(app / (name + ".csv"), newline="") as fh:
            return list(csv.DictReader(fh))

    book = {name: rows(name) for name in ("rolls", "inspection", "cutplans")}
    book["recall"] = (app / "recall.txt").read_text().split()
    return book


def build(app, reading):
    book = load(app)
    rolls = {r["roll"]: {"inspector": r["inspector"],
                         "length": cutroom.cm(r["length_m"]),
                         "width": cutroom.cm(r["width_m"])}
             for r in book["rolls"]}

    panels = {}
    for row in book["cutplans"]:
        panels.setdefault(row["roll"], []).append(
            (row["panel"], cutroom.cm(row["along_from_m"]),
             cutroom.cm(row["along_to_m"]), cutroom.cm(row["across_from_m"]),
             cutroom.cm(row["across_to_m"])))

    by_inspector = {}
    for row in book["inspection"]:
        who = rolls[row["roll"]]["inspector"]
        by_inspector.setdefault(who, []).append(row)

    # ---- each inspector's habit, found and not assumed ----------------------
    habits = {}
    for who, rows in by_inspector.items():
        along = [Fraction(r["along_m"]) * 100 for r in rows]
        across = [Fraction(r["across_m"]) * 100 for r in rows]
        lengths = [rolls[r["roll"]]["length"] for r in rows]
        widths = [rolls[r["roll"]]["width"] for r in rows]
        habit = set()
        # across before along: the "along" figures stop at the roll's width
        if reading["columns"] == "unswap" and max(along) <= max(widths) \
                and max(across) > max(widths):
            habit.add("exchanged")
            along, across = across, along
        # inches: a fault forty times the roll's width from the selvedge
        if reading["inches"] == "to_metres" and any(
                a > w for a, w in zip(across, widths)):
            habit.add("inches")
        # yards: faults booked beyond the end of the roll
        if reading["yards"] == "to_metres" and any(
                a > n for a, n in zip(along, lengths)):
            habit.add("yards")
        # counted from the last seam: the distance falls back after a seam
        falls = sum(1 for prev, row, a, b in zip(rows, rows[1:], along,
                                                 along[1:])
                    if prev["roll"] == row["roll"] and b < a)
        if reading["counter"] == "from_the_head" and falls:
            habit.add("from_seam")
        habits[who] = habit

    faults = []
    since = {}
    for row in book["inspection"]:
        roll = row["roll"]
        habit = habits[rolls[roll]["inspector"]]
        along = Fraction(row["along_m"]) * 100
        across = Fraction(row["across_m"]) * 100
        if "exchanged" in habit:
            along, across = across, along
        if "yards" in habit:
            along = along / 100 * cutroom.YARD_CM
        if "inches" in habit:
            across = across / 100 * cutroom.INCH_CM
        if "from_seam" in habit:
            along += since.get(roll, 0)
        along, across = cutroom.nearest_cm(along), cutroom.nearest_cm(across)
        if row["kind"] == "seam":
            since[roll] = along
        faults.append({"fault": row["fault"], "roll": roll,
                       "kind": row["kind"], "along": along, "across": across})

    # ---- which way each roll was laid up ------------------------------------
    tail_first = {}
    for roll, r in rolls.items():
        seams = [f for f in faults if f["roll"] == roll and f["kind"] == "seam"]

        def cut_into(way):
            return sum(1 for s in seams if cutroom.panel_at(
                panels[roll], *cutroom.to_lay(s["along"], r["width"] // 2,
                                              r["length"], r["width"], way)))

        if reading["lay"] == "by_the_seams":
            tail_first[roll] = cut_into(True) < cut_into(False)
        elif reading["lay"] == "as_inspected":
            tail_first[roll] = False
        else:
            tail_first[roll] = True

    return book, rolls, panels, faults, tail_first


def run(app, reading=None):
    reading = reading or TRUE_READING
    book, rolls, panels, faults, tail_first = build(app, reading)
    wanted = set(book["recall"])

    out = {}
    for f in faults:
        if f["fault"] not in wanted:
            continue
        r = rolls[f["roll"]]
        along, across = cutroom.to_lay(f["along"], f["across"], r["length"],
                                       r["width"], tail_first[f["roll"]])
        if reading["lay"] == "end_for_end_only":
            across = f["across"]
        out[f["fault"]] = cutroom.panel_at(panels[f["roll"]], along,
                                           across) or "WASTE"
    return out
