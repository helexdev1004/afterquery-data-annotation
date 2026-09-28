"""Number the defects' rings from the shipped records alone.

This reads only what the agent's container carries and never looks at the
answer. `TRUE_READING` is how the records have to be read; gates.py scores
every other way of reading them.
"""

from __future__ import annotations

import csv
import pathlib
from fractions import Fraction

import lining

TRUE_READING = {
    # One inspector books chainage in feet: his defects lie beyond the far
    # portal.
    "feet": "to_metres",
    # One inspector books the clock position before the chainage: his
    # "chainages" are whole numbers from one to twelve.
    "columns": "unswap",
    # One inspector books chainage in yards: his defects, too, lie beyond the
    # far portal, but only just.
    "yards": "to_metres",
    # One inspector books chainage in kilometres: all his defects lie in the
    # first two metres of the tunnel.
    "kilometres": "to_metres",
    # The survey tape was begun from whichever portal had the access, and
    # nothing says which. Drive A numbered its rings from portal A and drive B
    # from portal B, so which way the tape runs decides every number. What says
    # it is the joint survey itself: the two drives' rings were not cast to
    # the same tolerance, so how evenly the joints are spaced changes where
    # the drives met - and the two drives did not build the same number of
    # rings, so how many rings along the tape that change comes says which
    # drive the tape met first.
    "tape": "by_the_joints",
    # Segments are lettered looking up-chainage, and the inspector booked the
    # clock as he saw it walking the tape. On a tape begun at portal B he was
    # walking down-chainage, so his three o'clock is the register's nine.
    "clock": "as_he_walked",
}

OTHERS = {
    "feet": "as_booked",
    "columns": "as_booked",
    "yards": "as_booked",
    "kilometres": "as_booked",
    # the natural reading: the tape runs from portal A, as the numbering does
    "tape": "from_portal_a",
    # the natural reading: the clock taken as booked
    "clock": "as_booked",
}

EXTRAS = {"tape": ("from_portal_b",)}


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

    book = {name: rows(name) for name in ("tunnels", "joints", "defects")}
    book["wanted"] = (app / "wanted.txt").read_text().split()
    return book


def change_of_hand(joints):
    """How many rings along the tape the evenness of the joints changes.

    Returns (how sharply, the number of rings before the change). How far the
    rings before a candidate stray from the usual ring width is set against
    how far the rings after it do, and the candidate that sets them furthest
    apart is taken.
    """
    widths = [b - a for a, b in zip(joints, joints[1:])]
    usual = sorted(widths)[len(widths) // 2]
    stray = [abs(w - usual) for w in widths]
    best = (Fraction(1), len(widths) // 2)
    for k in range(10, len(widths) - 9):
        before = Fraction(sum(stray[:k]) + 1, k)
        after = Fraction(sum(stray[k:]) + 1, len(widths) - k)
        ratio = max(before / after, after / before)
        if ratio > best[0]:
            best = (ratio, k)
    return best


def build(app, reading):
    book = load(app)
    tunnels = {t["tunnel"]: {"inspector": t["inspector"],
                             "rings_a": int(t["rings_drive_a"]),
                             "rings_b": int(t["rings_drive_b"])}
               for t in book["tunnels"]}
    joints = {}
    for row in sorted(book["joints"], key=lambda r: (r["tunnel"],
                                                     int(r["joint"]))):
        joints.setdefault(row["tunnel"], []).append(lining.mm(row["tape_m"]))

    # ---- which portal each tape was begun from ------------------------------
    from_a = {}
    for name, t in tunnels.items():
        if reading["tape"] == "by_the_joints":
            _, rings_before = change_of_hand(joints[name])
            from_a[name] = abs(rings_before - t["rings_a"]) <= abs(
                rings_before - t["rings_b"])
        else:
            from_a[name] = reading["tape"] == "from_portal_a"

    # ---- each inspector's habit, found and not assumed ----------------------
    by_tunnel = {}
    for row in book["defects"]:
        by_tunnel.setdefault(row["tunnel"], []).append(row)

    defects = []
    for name, rows in by_tunnel.items():
        end = joints[name][-1]
        exchanged = False
        if reading["columns"] == "unswap":
            exchanged = all(float(r["tape_m"]) <= 12 for r in rows) and any(
                float(r["clock"]) > 12 for r in rows)
        values = []
        for r in rows:
            text = r["clock"] if exchanged else r["tape_m"]
            values.append(Fraction(text) * 1000)
        if max(values) < 2000 and end > 100000:
            if reading["kilometres"] == "to_metres":
                values = [v * 1000 for v in values]
        elif max(values) > end:
            # Booked in a longer measure than the tape was taped in. Defects
            # were booked the length of the bore, so the measure is the one
            # that brings the furthest of them back inside the far portal
            # without leaving the last stretch of tunnel bare: a yard if a
            # yard will do it, and a foot if it takes a foot.
            in_yards = max(values) / 1000 * lining.YARD_MM <= end
            if in_yards and reading["yards"] == "to_metres":
                values = [v / 1000 * lining.YARD_MM for v in values]
            elif not in_yards and reading["feet"] == "to_metres":
                values = [v / 1000 * lining.FOOT_MM for v in values]
        for r, value in zip(rows, values):
            clock = r["tape_m"] if exchanged else r["clock"]
            defects.append({"defect": r["defect"], "tunnel": name,
                            "chainage": lining.nearest_mm(Fraction(value)),
                            "clock": int(float(clock))})
    return book, tunnels, joints, from_a, defects


def run(app, reading=None):
    reading = reading or TRUE_READING
    book, tunnels, joints, from_a, defects = build(app, reading)
    wanted = set(book["wanted"])
    out = {}
    for d in defects:
        if d["defect"] not in wanted:
            continue
        t = tunnels[d["tunnel"]]
        along = lining.ring_along(joints[d["tunnel"]], d["chainage"])
        if along is None:
            out[d["defect"]] = "NONE"
            continue
        up_chainage = from_a[d["tunnel"]] or reading["clock"] == "as_booked"
        out[d["defect"]] = "%s-%s" % (
            lining.painted(d["tunnel"], along, t["rings_a"], t["rings_b"],
                           from_a[d["tunnel"]]),
            lining.segment(d["clock"], up_chainage))
    return out
