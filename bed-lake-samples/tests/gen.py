"""Lay the beds down, truth first, then write the records as they were kept.

    python gen.py [outdir]

Every hole's beds are laid down flood by flood before anything is cored, so
every bed has its number down the hole. The holes are then cored in sections,
the sections labelled and logged, and the samples cut and booked the way five
curators would have done it. So every answer is exact by construction rather
than a judgement made afterwards.

Internally everything is whole millimetres down the hole from the lake floor.
"""

from __future__ import annotations

import csv
import json
import pathlib
import random
import sys
from fractions import Fraction

import coring

SEED = 20260927
WANTED = 40

CURATORS = {
    "H1": "Arkwright",  # books a sample's place in millimetres
    "H2": "Bannister",  # books a sample's place in inches
    "H3": "Copley",     # books a sample's depth down the hole, in metres
    "H4": "Dugdale",    # books the volume before the place
    "H5": "Entwistle",  # keeps to the note
}
HABITS = {"Arkwright": "millimetres", "Bannister": "inches",
          "Copley": "hole_depth", "Dugdale": "exchanged", "Entwistle": None}

# The beds are flood layers. Each was laid down by one flood as it waned, so it
# is coarsest at its base and fines upward - which the core scanner's grain
# track shows, centimetre by centimetre, as a saw with its teeth one way. A
# section pushed out of the barrel is labelled top and bottom at the rig, and
# about a third of them were labelled the wrong way up. Nothing says which.
# In those sections the saw's teeth point the other way. An earlier build had
# the loggers write the grain at each bed's top and base into the bed log, and
# every cold solver saw at a glance which sections had it backwards.


def lay_hole(rng, site):
    """One hole: its beds down from the lake floor, and the sections cored."""
    sections = []
    depth = 0
    number = 0
    for index in range(1, rng.randint(11, 13) + 1):
        length = rng.randrange(1300, 1560, 10)
        beds, at = [], 0
        while at < length:
            thick = rng.randrange(60, 420, 5)
            base = min(length, at + thick)
            if length - base < 60:
                base = length
            number += 1
            coarse = rng.randint(2, 5)
            fine = rng.randint(0, coarse - 1) if rng.random() > 0.15 else coarse
            beds.append({"number": number, "top": at, "base": base,
                         "grain_top": fine, "grain_base": coarse})
            at = base
        sections.append({"section": "%s-S%02d" % (site, index),
                         "top_depth": depth, "length": length, "beds": beds,
                         "right_way_up": True})
        depth += length + rng.randrange(20, 90, 5)     # core lost at the shoe
    return sections


def main() -> int:
    outdir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                          pathlib.Path(__file__).resolve().parent.parent / "yard")
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    holes = {site: lay_hole(rng, site) for site in CURATORS}
    for site, sections in holes.items():
        # four of every hole's sections labelled the wrong way up, so it is
        # nobody's habit and no curator's sections can be checked against
        # another's; never a section with fewer than four graded beds, whose
        # grading would not say which way up it lies
        able = [s for s in sections
                if sum(1 for b in s["beds"]
                       if b["grain_top"] != b["grain_base"]) >= 4]
        for s in rng.sample(able, 4):
            s["right_way_up"] = False

    # the scanner's grain track, every centimetre along the section AS
    # LABELLED: each bed coarsest at its base and fining to its top, with the
    # scatter a scanner has
    for site, sections in holes.items():
        for s in sections:
            track = []
            for at in range(5, s["length"], 10):
                bed = next(b for b in s["beds"]
                           if b["top"] <= at < b["base"])
                up = Fraction(bed["base"] - at, bed["base"] - bed["top"])
                grain = bed["grain_base"] - up * (bed["grain_base"]
                                                  - bed["grain_top"])
                value = int(grain * 20) + 12 + rng.randint(-6, 6)
                labelled = at if s["right_way_up"] else s["length"] - at
                track.append((labelled // 10, value))
            s["scan"] = sorted(track)

    samples = []
    for site, sections in holes.items():
        for s in sections:
            for _ in range(rng.randint(6, 9)):
                true_offset = rng.randrange(15, s["length"] - 15)
                bed = next(b for b in s["beds"]
                           if b["top"] <= true_offset < b["base"])
                # the offset along the section AS LABELLED
                offset = true_offset if s["right_way_up"] \
                    else s["length"] - true_offset
                clear = min(true_offset - bed["top"], bed["base"] - true_offset)
                samples.append({"site": site, "section": s, "offset": offset,
                                "bed": "%s-B%03d" % (site, bed["number"]),
                                "clear": clear,
                                "volume": rng.choice((2, 5, 8, 10))})
    rng.shuffle(samples)
    for index, sample in enumerate(samples, 1):
        sample["sample"] = "G%04d" % index
    samples.sort(key=lambda s: s["sample"])

    def fmt(value, places):
        return ("%%.%df" % places) % float(value)

    def booked(sample):
        habit = HABITS[CURATORS[sample["site"]]]
        place = fmt(Fraction(sample["offset"], 10), 1)
        volume = str(sample["volume"])
        if habit == "millimetres":
            place = str(sample["offset"])
        elif habit == "inches":
            place = fmt(Fraction(sample["offset"]) / coring.INCH_MM, 2)
        elif habit == "hole_depth":
            place = fmt(Fraction(sample["section"]["top_depth"]
                                 + sample["offset"], 1000), 3)
        elif habit == "exchanged":
            place, volume = volume, place
        return place, volume

    def write(wanted):
        with open(outdir / "sections.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["hole", "section", "curator", "top_depth_m",
                             "length_cm"])
            for site, sections in holes.items():
                for s in sections:
                    writer.writerow([site, s["section"], CURATORS[site],
                                     fmt(Fraction(s["top_depth"], 1000), 3),
                                     fmt(Fraction(s["length"], 10), 1)])

        with open(outdir / "beds.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["section", "bed", "top_cm", "base_cm"])
            for site, sections in holes.items():
                for s in sections:
                    # logged along the section as labelled, from its labelled
                    # top: a section labelled upside down is logged upside down
                    logged = s["beds"]
                    if not s["right_way_up"]:
                        logged = [{"top": s["length"] - b["base"],
                                   "base": s["length"] - b["top"],
                                   "grain_top": b["grain_base"],
                                   "grain_base": b["grain_top"]}
                                  for b in reversed(s["beds"])]
                    for index, b in enumerate(logged, 1):
                        writer.writerow([
                            s["section"], "b%02d" % index,
                            fmt(Fraction(b["top"], 10), 1),
                            fmt(Fraction(b["base"], 10), 1)])

        with open(outdir / "scan.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["section", "at_cm", "grain_index"])
            for site, sections in holes.items():
                for s in sections:
                    for at, value in s["scan"]:
                        writer.writerow([s["section"], at, value])

        with open(outdir / "samples.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["sample", "section", "place_cm", "volume_cc"])
            for sample in samples:
                place, volume = booked(sample)
                writer.writerow([sample["sample"], sample["section"]["section"],
                                 place, volume])

        (outdir / "paper.txt").write_text(
            "".join(name + "\n" for name in sorted(wanted)), newline="\n")
        (outdir / "truth.json").write_text(json.dumps(
            {s["sample"]: s["bed"] for s in samples if s["sample"] in wanted},
            indent=1, sort_keys=True), newline="\n")

    # Only samples cut a centimetre and a half clear of a bed boundary, so that
    # neither the rule for a sample on a boundary nor an inch's rounding
    # decides an answer.
    fit = {s["sample"]: s for s in samples if s["clear"] >= 15}
    write(set(fit))

    import ref
    right = ref.run(outdir)
    wrong = [k for k in fit if right.get(k) != fit[k]["bed"]]
    if wrong:
        print("FAILED: the reference and the holes disagree on %d of %d"
              % (len(wrong), len(fit)))
        for k in wrong[:5]:
            print("   %s said %s was %s" % (k, right.get(k), fit[k]["bed"]))
        return 1

    moved = {k: set() for k in fit}
    for axis, other in ref.OTHERS.items():
        got = ref.run(outdir, dict(ref.TRUE_READING, **{axis: other}))
        for k in fit:
            if got.get(k) != fit[k]["bed"]:
                moved[k].add(axis)

    # Eight from every hole, and in every hole as many as can be found that lie
    # in a section labelled upside down, up to five, so that the labelling
    # matters and the forty are still not all drawn from such sections.
    wanted = set()
    for site in CURATORS:
        mine = [k for k in sorted(fit) if fit[k]["site"] == site]
        rng.shuffle(mine)
        habits = set(ref.OTHERS) - {"way_up"}
        # those the curator's own habit moves come first, so that no habit is
        # decoration; a hole whose curator kept to the note has none
        mine.sort(key=lambda k: not (moved[k] & habits))
        turned = [k for k in mine if "way_up" in moved[k]][:5]
        if HABITS[CURATORS[site]] == "hole_depth":
            # a depth booked for a sample in a section labelled upside down
            # could be read two ways - the label's depth or the true one - and
            # three cold solvers said so; none of the forty asks it
            turned = []
            mine = [k for k in mine if fit[k]["section"]["right_way_up"]]
        rest = [k for k in mine if k not in turned][:WANTED // len(CURATORS)
                                                    - len(turned)]
        wanted.update(turned + rest)
    cover = {axis: sum(1 for k in wanted if axis in moved[k])
             for axis in ref.OTHERS}

    write(wanted)
    (outdir / "labelled.json").write_text(json.dumps(
        {s["section"]: ("up" if s["right_way_up"] else "down")
         for sections in holes.values() for s in sections},
        indent=1, sort_keys=True), newline="\n")
    print("holes %d  sections %d  beds %d  samples %d  wanted %d"
          % (len(holes), sum(len(v) for v in holes.values()),
             sum(len(s["beds"]) for v in holes.values() for s in v),
             len(samples), len(wanted)))
    print("samples each habit moves among the forty: %s" % cover)
    print("wrote %s" % outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
