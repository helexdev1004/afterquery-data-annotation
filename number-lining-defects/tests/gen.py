"""Drive the tunnels, truth first, then write the records as they were kept.

    python gen.py [outdir]

Every tunnel is driven from both portals and lined ring by ring before anything
is surveyed, so every ring has its painted number and its place in the ground.
The joint survey and the walk-through inspection are written afterwards, the
way the survey team and five inspectors would have kept them. So every answer
is exact by construction rather than a judgement made afterwards.

Internally everything is whole millimetres along the tunnel from portal A.
"""

from __future__ import annotations

import csv
import json
import pathlib
import random
import sys
from fractions import Fraction

import lining

SEED = 20260923
WANTED = 40

INSPECTORS = {
    "T1": "Ainsley",    # books chainage in feet
    "T2": "Braddock",   # books the clock position before the chainage
    "T3": "Corrigan",   # books chainage in yards
    "T4": "Dunstan",    # books chainage in kilometres
    "T5": "Everard",    # keeps to the note
}
HABITS = {"Ainsley": "feet", "Braddock": "exchanged", "Corrigan": "yards",
          "Dunstan": "kilometres", "Everard": None}

# The portal each tunnel's survey tape was begun from. The survey team started
# from whichever portal had the access that week, and nothing in the records
# says which. Three of the five were taped from portal B.
TAPED_FROM_A = {"T1": False, "T2": True, "T3": False, "T4": True, "T5": False}

# Both drives were lined with rings a metre and a half wide, but under two
# contracts from two casting yards: drive A's rings were cast to two
# millimetres and drive B's to nine. The note does not say so. It is what
# shows, in the joint survey itself, where along the tape the two drives met -
# and so which portal the tape was begun from, because the two drives did not
# build the same number of rings. An earlier build gave the two drives rings
# of two widths, and every cold solver worked out the ring widths as a matter
# of course, saw two runs, and matched their lengths to the drives' ring
# counts in a minute.
RING_MM = 1500
CAST_TO_MM = {"A": 2, "B": 9}

KINDS = ("crack", "spall", "seepage", "loose bolt", "stained joint",
         "damaged gasket")


def drive(rng, name):
    """One tunnel: every ring's painted number and its place in the ground."""
    while True:
        rings_a = rng.randrange(170, 320)
        rings_b = rng.randrange(170, 320)
        if abs(rings_a - rings_b) >= 45:
            break
    rings = []                      # from portal A to portal B
    for n in range(1, rings_a + 1):
        rings.append(("%s-A-%04d" % (name, n), "A"))
    for n in range(rings_b, 0, -1):
        rings.append(("%s-B-%04d" % (name, n), "B"))

    widths = []
    for _, which in rings:
        widths.append(RING_MM + rng.randint(-CAST_TO_MM[which],
                                            CAST_TO_MM[which]))
    return {"tunnel": name, "rings_a": rings_a, "rings_b": rings_b,
            "rings": rings, "widths": widths}


def tape(tunnel, from_a):
    """The tape chainage of every joint, the portal face the tape began at first."""
    widths = tunnel["widths"] if from_a else tunnel["widths"][::-1]
    joints = [0]
    for wide in widths:
        joints.append(joints[-1] + wide)
    return joints


def main() -> int:
    outdir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                          pathlib.Path(__file__).resolve().parent.parent / "yard")
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    tunnels = [drive(rng, name) for name in sorted(INSPECTORS)]
    defects = []
    for t in tunnels:
        from_a = TAPED_FROM_A[t["tunnel"]]
        joints = tape(t, from_a)
        order = t["rings"] if from_a else t["rings"][::-1]
        for _ in range(rng.randrange(70, 90)):
            chainage = rng.randrange(300, joints[-1] - 300)
            along = lining.ring_along(joints, chainage)
            clear = min(chainage - joints[along - 1], joints[along] - chainage)
            defects.append({"tunnel": t["tunnel"], "chainage": chainage,
                            "along": along, "ring": order[along - 1][0],
                            "clear": clear, "kind": rng.choice(KINDS),
                            "clock": rng.randint(1, 12),
                            "extent": rng.randrange(5, 120)})
    defects.sort(key=lambda d: (d["tunnel"], d["chainage"]))
    for index, d in enumerate(defects, 1):
        d["defect"] = "D%04d" % index

    def fmt(value, places):
        return ("%%.%df" % places) % float(value)

    def booked(d, joints):
        habit = HABITS[INSPECTORS[d["tunnel"]]]
        chainage = fmt(Fraction(d["chainage"], 1000), 3)
        clock = str(d["clock"])
        if habit == "feet":
            chainage = fmt(Fraction(d["chainage"]) / lining.FOOT_MM, 2)
        elif habit == "kilometres":
            chainage = fmt(Fraction(d["chainage"], 1000000), 6)
        elif habit == "yards":
            chainage = fmt(Fraction(d["chainage"]) / lining.YARD_MM, 2)
        elif habit == "exchanged":
            chainage, clock = clock, chainage
        return chainage, clock

    def write(wanted):
        with open(outdir / "tunnels.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["tunnel", "inspector", "rings_drive_a",
                             "rings_drive_b"])
            for t in tunnels:
                writer.writerow([t["tunnel"], INSPECTORS[t["tunnel"]],
                                 t["rings_a"], t["rings_b"]])

        tapes = {}
        with open(outdir / "joints.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["tunnel", "joint", "tape_m"])
            for t in tunnels:
                tapes[t["tunnel"]] = tape(t, TAPED_FROM_A[t["tunnel"]])
                for index, at in enumerate(tapes[t["tunnel"]]):
                    writer.writerow([t["tunnel"], index,
                                     fmt(Fraction(at, 1000), 3)])

        with open(outdir / "defects.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["defect", "tunnel", "kind", "tape_m", "clock",
                             "extent_m"])
            for d in defects:
                chainage, clock = booked(d, tapes[d["tunnel"]])
                writer.writerow([d["defect"], d["tunnel"], d["kind"], chainage,
                                 clock, fmt(Fraction(d["extent"], 100), 2)])

        (outdir / "wanted.txt").write_text(
            "".join(name + "\n" for name in sorted(wanted)), newline="\n")
        (outdir / "truth.json").write_text(json.dumps(
            {d["defect"]: d["ring"] for d in defects if d["defect"] in wanted},
            indent=1, sort_keys=True), newline="\n")

    # Only defects that stand five centimetres clear of a joint, so that neither
    # the rule for a defect on a joint nor a foot's rounding decides an answer.
    fit = {d["defect"]: d for d in defects if d["clear"] >= 50}
    write(set(fit))

    import ref
    right = ref.run(outdir)
    wrong = [k for k in fit if right.get(k) != fit[k]["ring"]]
    if wrong:
        print("FAILED: the reference and the tunnels disagree on %d of %d"
              % (len(wrong), len(fit)))
        for k in wrong[:5]:
            print("   %s said %s was %s" % (k, right.get(k), fit[k]["ring"]))
        return 1

    moved = {k: set() for k in fit}
    for axis, other in ref.OTHERS.items():
        got = ref.run(outdir, dict(ref.TRUE_READING, **{axis: other}))
        for k in fit:
            if got.get(k) != fit[k]["ring"]:
                moved[k].add(axis)

    # Eight from every tunnel, so that no inspector's habit is decoration and
    # the forty are not conspicuously drawn from the tunnels taped from the far
    # portal.
    wanted = set()
    for t in tunnels:
        mine = [k for k in sorted(fit) if fit[k]["tunnel"] == t["tunnel"]]
        rng.shuffle(mine)
        wanted.update(mine[:WANTED // len(tunnels)])
    cover = {axis: sum(1 for k in wanted if axis in moved[k])
             for axis in ref.OTHERS}

    write(wanted)
    (outdir / "taped.json").write_text(json.dumps(
        {name: ("A" if way else "B") for name, way in TAPED_FROM_A.items()},
        indent=1, sort_keys=True), newline="\n")
    print("tunnels %d  rings %d  defects %d  wanted %d"
          % (len(tunnels), sum(len(t["rings"]) for t in tunnels), len(defects),
             len(wanted)))
    print("defects each habit moves among the forty: %s" % cover)
    print("wrote %s" % outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
