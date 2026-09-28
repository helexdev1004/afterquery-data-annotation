"""Weave the rolls, truth first, then write the records as they were kept.

    python gen.py [outdir]

Every roll is woven with its faults and its mill seams before anything is
recorded, then laid up on a cutting table and cut to a plan, and each fault
lands in a known panel or in the waste. The mill's inspection reports and the
cutting room's cut plans are written afterwards, the way five inspectors and
the cutting room would have kept them. So every answer is exact by construction
rather than a judgement made afterwards.

Internally everything is whole centimetres: along the roll from the end the
inspector saw first, across it from the selvedge on his left.
"""

from __future__ import annotations

import csv
import json
import pathlib
import random
import sys
from fractions import Fraction

import cutroom

SEED = 20260920
TO_TRACE = 40

INSPECTORS = {
    "Ashworth": "yards",        # books the distance along the roll in yards
    "Birtwistle": "inches",     # books the distance across the roll in inches
    "Crabtree": "exchanged",    # books across before along
    "Dewhurst": "from_seam",    # runs his counter from the last seam he passed
    "Eccles": None,             # keeps to the procedure
}

KINDS = ("slub", "float", "stain", "hole", "missing end", "broken pick",
         "crease", "oil spot")


def weave(rng, number, inspector, tail_first):
    """One roll: its seams, its faults, and the lay it was cut in."""
    length = rng.randrange(6000, 9001, 50)
    width = rng.choice((140, 150, 160))

    # Mill seams, where two pieces were joined. Kept clear of the ends and of
    # one another, and clear of the middle of the roll, where turning the roll
    # end for end would leave a seam more or less where it was and the lay
    # would say nothing about which end came first.
    seams = []
    tries = 0
    while len(seams) < 3 and tries < 400:
        tries += 1
        s = rng.randrange(700, length - 700)
        if abs(s - length // 2) < 500:
            continue
        if any(abs(s - other) < 900 or abs(s - (length - other)) < 300
               for other in seams):
            continue
        seams.append(s)
    seams.sort()

    # ---- the lay, in the table's own frame ----------------------------------
    # A seam is never cut into a panel: the lay is parted at it, a hand's
    # breadth either side. In the table's frame the seam stands where the way
    # the roll was laid up puts it.
    parted = sorted(cutroom.to_lay(s, 0, length, width, tail_first)[0]
                    for s in seams)
    panels = []
    serial = 0
    at = rng.randrange(8, 15)                   # squared off at table zero
    stops = [p for p in parted] + [length]
    for stop in stops:
        limit = stop - rng.randrange(8, 13) if stop != length else length - 6
        while True:
            run = rng.randrange(80, 221, 5)
            if at + run > limit:
                break
            # panels nested across the usable width, between the selvedges
            across = cutroom.SELVEDGE_CM
            edge = width - cutroom.SELVEDGE_CM
            row = []
            while edge - across >= 25:
                take = min(edge - across, rng.randrange(25, 76))
                if edge - across - take < 25:
                    take = edge - across
                row.append((across, across + take))
                across += take
            for c0, c1 in row:
                serial += 1
                panels.append(("R%02d-P%03d" % (number, serial),
                               at, at + run, c0, c1))
            at += run
        if stop != length:
            at = stop + rng.randrange(8, 13)    # and begun again past the seam

    # ---- the faults, in the inspector's frame -------------------------------
    faults = []
    for s in seams:
        faults.append({"kind": "seam", "along": s, "across": width // 2,
                       "size": width})
    count = rng.randrange(36, 46)
    while len(faults) < count + len(seams):
        along = rng.randrange(30, length - 30)
        across = rng.randrange(4, width - 4)
        faults.append({"kind": rng.choice(KINDS), "along": along,
                       "across": across, "size": rng.randrange(1, 12)})
    faults.sort(key=lambda f: f["along"])

    for f in faults:
        x, y = cutroom.to_lay(f["along"], f["across"], length, width, tail_first)
        f["panel"] = cutroom.panel_at(panels, x, y)
        # what the fault would be traced to with the roll taken the other way
        ox, oy = cutroom.to_lay(f["along"], f["across"], length, width,
                                not tail_first)
        f["other"] = cutroom.panel_at(panels, ox, oy)
        # how far it stands from the nearest cut line of its own panel
        f["clear"] = 0
        if f["panel"]:
            _, a0, a1, c0, c1 = next(p for p in panels if p[0] == f["panel"])
            f["clear"] = min(x - a0, a1 - x, y - c0, c1 - y)

    return {"roll": "R%02d" % number, "inspector": inspector,
            "length": length, "width": width, "tail_first": tail_first,
            "seams": seams, "panels": panels, "faults": faults}


def fmt(value, places=2):
    return ("%%.%df" % places) % float(value)


def booked(roll, fault, since_seam):
    """A fault's two figures as this roll's inspector wrote them down."""
    habit = INSPECTORS[roll["inspector"]]
    along, across = Fraction(fault["along"]), Fraction(fault["across"])
    if habit == "from_seam":
        along = along - since_seam
    along_text = fmt(along / 100)
    across_text = fmt(across / 100)
    if habit == "yards":
        along_text = fmt(along / cutroom.YARD_CM)
    if habit == "inches":
        across_text = fmt(across / cutroom.INCH_CM, 1)
    if habit == "exchanged":
        along_text, across_text = across_text, along_text
    return along_text, across_text


def main() -> int:
    outdir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                          pathlib.Path(__file__).resolve().parent.parent / "yard")
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    # Which rolls were laid up tail first. A roll comes off the inspection frame
    # wound with its first-seen end at the core, so laid up straight from the
    # store it comes off the tube tail first; a roll that was re-rolled at goods
    # in - to relax it, or to re-tube it - comes off head first again. Two of
    # every inspector's three rolls were laid up tail first, so it is nobody's
    # habit and no inspector's rolls can be checked against another's.
    rolls = []
    number = 0
    for inspector in INSPECTORS:
        ways = [True, True, False]
        rng.shuffle(ways)
        for tail_first in ways:
            number += 1
            for _ in range(200):
                roll = weave(rng, number, inspector, tail_first)
                # every seam must stand INSIDE a panel with the roll taken the
                # wrong way about, so that the lay settles the matter
                wrong = [cutroom.panel_at(
                    roll["panels"],
                    *cutroom.to_lay(s, roll["width"] // 2, roll["length"],
                                    roll["width"], not tail_first))
                    for s in roll["seams"]]
                beyond = any(f["along"] * 100 > roll["length"] * cutroom.YARD_CM
                             for f in roll["faults"])
                if len(roll["seams"]) == 3 and all(wrong) and (
                        INSPECTORS[inspector] != "yards" or beyond):
                    break
            else:
                raise SystemExit("could not weave %s a roll" % inspector)
            rolls.append(roll)

    serial = 0
    for roll in sorted(rolls, key=lambda r: r["roll"]):
        for f in roll["faults"]:
            serial += 1
            f["fault"] = "F%04d" % serial

    def write(wanted):
        with open(outdir / "rolls.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["roll", "inspector", "length_m", "width_m",
                             "table"])
            for roll in sorted(rolls, key=lambda r: r["roll"]):
                writer.writerow([roll["roll"], roll["inspector"],
                                 fmt(Fraction(roll["length"], 100)),
                                 fmt(Fraction(roll["width"], 100)),
                                 "T%d" % (1 + int(roll["roll"][1:]) % 3)])

        with open(outdir / "inspection.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["fault", "roll", "kind", "along_m", "across_m",
                             "size_cm"])
            for roll in sorted(rolls, key=lambda r: r["roll"]):
                since = 0
                for f in roll["faults"]:
                    along, across = booked(roll, f, since)
                    writer.writerow([f["fault"], roll["roll"], f["kind"],
                                     along, across, f["size"]])
                    if f["kind"] == "seam":
                        since = f["along"]

        with open(outdir / "cutplans.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["roll", "panel", "along_from_m", "along_to_m",
                             "across_from_m", "across_to_m"])
            for roll in sorted(rolls, key=lambda r: r["roll"]):
                for panel, a0, a1, c0, c1 in roll["panels"]:
                    writer.writerow([roll["roll"], panel] + [
                        fmt(Fraction(v, 100)) for v in (a0, a1, c0, c1)])

        (outdir / "recall.txt").write_text(
            "".join(name + "\n" for name in sorted(wanted)), newline="\n")

        truth = {f["fault"]: f["panel"] for roll in rolls
                 for f in roll["faults"] if f["fault"] in wanted}
        (outdir / "truth.json").write_text(
            json.dumps(truth, indent=1, sort_keys=True), newline="\n")

    # Only faults that end up in a panel whichever way their roll is taken - so
    # that a solver who takes it the wrong way gets a plausible wrong panel for
    # every one of the forty and never a fault in the waste to make him wonder -
    # and that stand three centimetres clear of every cut line, so neither the
    # rule for a fault on a line nor a yard's or an inch's rounding decides an
    # answer.
    fit = {f["fault"]: f for roll in rolls for f in roll["faults"]
           if f["kind"] != "seam" and f["panel"] and f["other"]
           and f["clear"] >= 3}
    write(set(fit))

    import ref
    right = ref.run(outdir)
    wrong = [k for k in fit if right.get(k) != fit[k]["panel"]]
    if wrong:
        print("FAILED: the reference and the cutting room disagree on %d of %d"
              % (len(wrong), len(fit)))
        for k in wrong[:5]:
            print("   %s said %s was %s" % (k, right.get(k), fit[k]["panel"]))
        return 1

    moved = {k: set() for k in fit}
    for axis, other in ref.OTHERS.items():
        got = ref.run(outdir, dict(ref.TRUE_READING, **{axis: other}))
        for k in fit:
            if got.get(k) != fit[k]["panel"]:
                moved[k].add(axis)

    pool = [k for k in sorted(fit) if moved[k]]
    rng.shuffle(pool)
    cover = {axis: 0 for axis in ref.OTHERS}
    wanted = set()
    spare = [k for k in sorted(fit) if not moved[k]]
    rng.shuffle(spare)
    for pick in spare[:4]:              # a few that nothing moves
        wanted.add(pick)
    while len(wanted) < TO_TRACE and pool:
        need = min(cover, key=lambda a: cover[a])
        pick = next((k for k in pool if need in moved[k]), pool[0])
        pool.remove(pick)
        wanted.add(pick)
        for axis in moved[pick]:
            cover[axis] += 1
    if len(wanted) < TO_TRACE:
        print("FAILED: only %d faults could be chosen" % len(wanted))
        return 1

    write(wanted)
    (outdir / "laid.json").write_text(json.dumps(
        {r["roll"]: ("tail" if r["tail_first"] else "head") for r in rolls},
        indent=1, sort_keys=True), newline="\n")
    print("rolls %d  faults %d  panels %d  to trace %d"
          % (len(rolls), sum(len(r["faults"]) for r in rolls),
             sum(len(r["panels"]) for r in rolls), len(wanted)))
    print("faults each habit moves among the forty: %s" % cover)
    print("wrote %s" % outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
