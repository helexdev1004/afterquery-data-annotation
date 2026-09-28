"""Lay the site down, truth first, then write the archive as it was kept.

    python gen.py [outdir]

The deposits are laid and the pits cut before anything is recorded, and each
find is dropped into a known context. The section drawings and the finds
register are then written the way this site's five supervisors would have
written them. So every answer is exact by construction rather than a judgement
made afterwards.

Internally everything is whole centimetres in the TRENCH frame: offsets from
the trench's west end, depths below site datum. The archive is written in
metres to two places.
"""

from __future__ import annotations

import csv
import json
import pathlib
import random
import sys

import site_model as site

SEED = 20260919
TO_PHASE = 40

SUPERVISORS = {
    "T1": "Aldous",     # books find depths below his own bench mark, unreduced
    "T2": "Brandreth",  # digitised his sections with the two columns exchanged
    "T3": "Coverdale",  # digitised his drawings at twice the scale
    "T4": "Dunmore",    # books find depths as levels above Ordnance datum
    "T5": "Eskdale",    # keeps the archive as the manual says
}


# The end of each trench its zero peg stands at. A section is drawn by someone
# standing in the trench and facing it, left to right, so the north drawing
# runs from the west end and the south drawing from the east: in a trench
# pegged from the west it is the north drawing that runs from the zero peg, and
# in one pegged from the east it is the south. Nothing in the archive names the
# end. What says it is each drawing's own hand: the team that worked out from
# the zero peg drew its length of a section with a point every metre or so, and
# the team that worked in from the far end with a point every forty
# centimetres, so a drawing changes hands at the meeting point - at the taped
# figure along a drawing that runs from the peg, and at the trench's length
# less it along one that runs towards the peg.
PEG_END = {"T1": "W", "T2": "E", "T3": "E", "T4": "W", "T5": "E"}

# The team that dug towards the zero peg from the far end numbered its contexts
# a hundred above the team that dug out from the peg.
FAR_TEAM = 100

# Whether the pits run right across the trench and so stand in both of its
# drawings. They did in three builds, under one number and then under two, and
# each time cold solvers matched them up between the drawings - by number, then
# by size - saw that the drawings run opposite ways about, and went looking for
# which. Here no pit reaches both sections, and nothing in one drawing can be
# laid against the other.
PITS_CROSS = False


def half_up(num, den):
    return (2 * num + den) // (2 * den)


def value_at(poly, x):
    """The boundary's depth at x as an exact (numerator, denominator)."""
    for (x1, z1), (x2, z2) in zip(poly, poly[1:]):
        if x1 <= x <= x2:
            if x1 == x2:
                return z1, 1
            return z1 * (x2 - x1) + (z2 - z1) * (x - x1), x2 - x1
    raise ValueError("x outside the boundary")


def dig_pits(rng, length, meet):
    """A trench's pits, or nothing if they will not fit.

    With PITS_CROSS unset, as it ships, there are four and each stands in one
    section only, two to a section. Builds that let a pit stand in both
    drawings - under one number, and then under two - were phased by cold
    solvers in minutes: they matched the pits up between the drawings, by
    number and then by size, and saw that the drawings run opposite ways
    about. Kept clear of the meeting point both ways about, so each pit was
    one team's to dig.
    """
    pits = []
    tries = 0
    want = 3 if PITS_CROSS else 4
    while len(pits) < want and tries < 600:
        tries += 1
        width = rng.randrange(90, 210)
        xa = rng.randrange(130, length - 130 - width)
        mid = xa + width // 2
        if abs(mid - length // 2) < 150:
            continue
        apart = 120 if PITS_CROSS else 80
        if any(xa < p["xb"] + apart and p["xa"] < xa + width + apart
               for p in pits):
            continue
        if any(xa - 70 < spot < xa + width + 70
               for spot in (meet, length - meet)):
            continue
        if any(abs(width - p["xb"] + p["xa"]) < 12 for p in pits):
            continue            # no two pits of a trench alike in size
        pits.append({"xa": xa, "xb": xa + width,
                     "from": rng.randint(1, 3),
                     "deep": rng.randrange(70, 150),
                     "skew": rng.choice((-1, 1)) * rng.randrange(10, 41)})
    if len(pits) < want:
        return None
    pits.sort(key=lambda p: p["xa"])
    # Where the pits do not cross the trench each stands in one section only,
    # two to a section.
    sides = ["NS"] * 3 if PITS_CROSS else rng.sample(["N", "N", "S", "S"], 4)
    for p, side in zip(pits, sides):
        p["sides"] = side
    return pits


def lay_trench(rng, name):
    """One trench: two facing sections of the same deposits, in trench frame."""
    number = int(name[1:])
    length = rng.randrange(1500, 2100, 50)
    west = rng.randrange(20, 46)
    # The site is level. On a sloping site the two facing drawings of a trench
    # show the ground falling opposite ways, and a cold solver saw in its first
    # look at the file that one of each pair was turned round. On a level site
    # the two drawings look alike.
    east = west + rng.randint(-4, 4)

    # Two teams dug every trench, one out from the zero peg and one in from the
    # far end, and where they met is taped from the zero peg. Kept off the
    # middle, where it would fall at much the same offset whichever end a
    # drawing runs from and would decide nothing.
    for _ in range(200):
        meet = rng.choice((rng.randrange(length * 30 // 100, length * 42 // 100),
                           rng.randrange(length * 58 // 100, length * 70 // 100)))
        pits = dig_pits(rng, length, meet)
        if pits:
            break
    else:
        raise SystemExit("could not fit three pits into %s" % name)
    meet_w = meet if PEG_END[name] == "W" else length - meet


    bands = rng.randint(6, 8)
    coarse = list(range(0, length + 100, 100))

    def lay_base():
        base = []
        for _ in range(bands):
            thick, run = rng.randrange(22, 48), []
            for _ in coarse:
                thick = max(0, min(70, thick + rng.randint(-9, 9)))
                run.append(thick)
            base.append(run)
        return base

    sections = {}
    for side in ("N", "S"):
        # The layers run right across the trench but are not the same
        # thickness on both sides of it: each section has its own. Where the
        # two sections were given one thickness between them, a cold solver
        # laid one drawing over the other, saw they agreed only with one turned
        # round, and had the direction of every drawing in a minute.
        base = lay_base()

        def base_thick(band, x, base=base):
            i = min(x // 100, len(coarse) - 2)
            a, b = base[band][i], base[band][i + 1]
            return a + (b - a) * (x - coarse[i]) // 100

        shift = {}
        for p in pits:
            skew = 0 if side == "N" else p["skew"]
            shift[id(p)] = (skew + rng.randint(-3, 3), skew + rng.randint(-3, 3),
                            rng.randint(-6, 6))
        edges = set()
        for p in pits:
            if side in p["sides"]:
                da, db, _ = shift[id(p)]
                edges.update((p["xa"] + da, p["xb"] + db))
        grid = {0, length} | edges
        x = 0
        while x < length - 30:
            # each team's own hand: the near team's points stand a metre or so
            # apart, the far team's forty centimetres
            near_team = (x < meet_w) == (PEG_END[name] == "W")
            x += rng.randrange(85, 135) if near_team else rng.randrange(34, 58)
            # a point that would crowd a pit's edge, or stand on the meeting
            # point, is set a little further on rather than left out, so a
            # team's hand is not broken by a gap that is not its own
            while any(abs(x - e) <= 12 for e in edges) \
                    or min(abs(x - meet), abs(x - (length - meet))) <= 3:
                x += 5
            if x < length - 20:
                grid.add(x)
        grid = sorted(grid)

        bounds = [[(gx, west + (east - west) * gx // length
                    + rng.randint(-2, 2)) for gx in grid]]
        for band in range(bands):
            prev = bounds[-1]
            bounds.append([(gx, pz + max(0, base_thick(band, gx)
                                         + rng.randint(-7, 7)))
                           for (gx, pz) in prev])

        layers = [(number * 1000 + band + 1, bounds[band], bounds[band + 1])
                  for band in range(bands)]

        features = []
        # numbered along the drawing as the draughtsman came to them: the
        # north drawing's from 51, working from the zero peg; the south
        # drawing's from 61, working the other way
        ordered = [p for p in (pits if side == "N" else pits[::-1])
                   if side in p["sides"]]
        for index, p in enumerate(ordered):
            da, db, dd = shift[id(p)]
            xa, xb = p["xa"] + da, p["xb"] + db
            top = [(gx, gz) for gx, gz in bounds[p["from"]] if xa <= gx <= xb]
            za, zb = top[0][1], top[-1][1]
            deep = p["deep"] + dd
            quarter = (xb - xa) // 4
            bottom = [(xa, za),
                      (xa + quarter, max(za, zb) + deep * 7 // 10),
                      ((xa + xb) // 2, max(za, zb) + deep),
                      (xb - quarter, max(za, zb) + deep * 7 // 10),
                      (xb, zb)]
            features.append((number * 1000 + (51 if side == "N" else 61)
                             + index, top, bottom))

        sections[side] = {"layers": layers, "features": features,
                          "surface": bounds[0], "floor": bounds[-1]}

    return {"trench": name, "length": length, "west": west, "east": east,
            "tbm": rng.randrange(70, 131), "sections": sections,
            "meet": meet, "peg": PEG_END[name]}


def drop_finds(rng, trench, count, first):
    """Finds in known contexts, anywhere a find could really have lain.

    The first build kept EVERY find four centimetres clear of every boundary,
    so that no rule about boundaries could decide an answer. A cold solver
    found that regularity and used it as an answer key: any wrong reading of
    the archive put finds near boundaries, the right one never did, and four
    hundred finds made the test decisive. So finds now fall wherever they fall -
    right down to the turf and up against the lines - and only the forty that
    are asked for are held off a boundary, and then only by the centimetre that
    exactness needs.
    """
    # A find is plotted onto the drawing of the section it lay nearer, so its
    # offset is in that drawing's own frame and the find can be located on the
    # drawing with no thought for which way the drawing runs. Eight builds that
    # taped the finds from the zero peg instead were all phased by cold solvers
    # in two minutes: they tried the drawings both ways about and kept the way
    # that put the finds in the pits. What the direction of a drawing decides
    # here is only which TEAM dug a find - and that is a question a solver has
    # to think to ask, because nothing goes visibly wrong if he does not. It is
    # the shape of the one task of mine that the probes did not walk through:
    # there, a board's second face was booked from the other edge, each face
    # looked self-contained, and a fast solver who saw the evidence still did
    # not see that it mattered.
    length = trench["length"]
    top = max(z for s in trench["sections"].values() for _, z in s["surface"])
    low = min(z for s in trench["sections"].values() for _, z in s["floor"])
    finds = []
    tries = 0
    while len(finds) < count and tries < 40000:
        tries += 1
        side = rng.choice(("N", "S"))
        section = trench["sections"][side]
        if rng.random() < 0.6 and section["features"]:
            _, pit_top, pit_bottom = rng.choice(section["features"])
            x = rng.randrange(pit_top[0][0] + 4, pit_top[-1][0] - 4)
            num, den = value_at(pit_top, x)
            upper = max(top + 6, -(-num // den) + 1)
            num, den = value_at(pit_bottom, x)
            lower = min(low - 6, num // den - 1)
            if lower - upper < 4:
                continue
            z = rng.randrange(upper, lower)
        else:
            x = rng.randrange(25, length - 25)
            z = rng.randrange(top + 6, low - 6)
        context = site.locate(section, x, z)
        if context is None:
            continue
        gap = site.nearest_boundary(section, x, z)
        # which team dug it: the one working out from the zero peg, or the one
        # working in from the far end, whose numbers stand a hundred higher
        from_peg = x if trench["peg"] == "W" else length - x
        if from_peg > trench["meet"]:
            context += FAR_TEAM
        finds.append({"find": "SF%04d" % (first + len(finds)),
                      "trench": trench["trench"], "section": side,
                      "x": x, "z": z, "context": context,
                      "gap": gap or 0,
                      # clear of the meeting point whichever way its drawing
                      # is taken to run, so no answer turns on a centimetre
                      "clear": min(abs(from_peg - trench["meet"]),
                                   abs(length - from_peg - trench["meet"])) >= 5,
                      # deep enough that no way of reading the drawings can
                      # put it above the turf or under the trench floor
                      "deep": top + 6 <= z <= low - 6})
    return finds


def fmt(cm):
    sign = "-" if cm < 0 else ""
    cm = abs(cm)
    return "%s%d.%02d" % (sign, cm // 100, cm % 100)


def write(outdir, trenches, finds, wanted):
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    with open(out / "trenches.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["trench", "supervisor", "length_m", "tbm_m",
                         "meeting_m"])
        for t in trenches:
            # Nothing here says which end of a drawing the zero peg stands at.
            # That has to come from where each drawing changes hands.
            writer.writerow([t["trench"], SUPERVISORS[t["trench"]],
                             fmt(t["length"]), fmt(t["tbm"]), fmt(t["meet"])])

    with open(out / "sections.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["trench", "section", "context", "kind", "boundary",
                         "point", "offset_m", "depth_m"])
        for t in trenches:
            name, length = t["trench"], t["length"]
            for side in ("N", "S"):
                section = t["sections"][side]
                rows = [("layer", c, a, b) for c, a, b in section["layers"]]
                rows += [("cut", c, a, b) for c, a, b in section["features"]]
                for kind, context, top, bottom in rows:
                    for label, poly in (("top", top), ("bottom", bottom)):
                        # A section is drawn as it is seen. Standing in the
                        # trench facing the south section, the west end is on
                        # the right hand: that drawing runs the other way.
                        if side == "S":
                            poly = [(length - x, z) for x, z in reversed(poly)]
                        for index, (x, z) in enumerate(poly, 1):
                            if name == "T3":        # drawn at twice the scale
                                x, z = 2 * x, 2 * z
                            if name == "T2":        # the two columns exchanged
                                x, z = z, x
                            writer.writerow([name, side, context, kind, label,
                                             index, fmt(x), fmt(z)])

    surfaces = {t["trench"]: t for t in trenches}
    with open(out / "finds.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["find", "trench", "section", "offset_m", "depth_m"])
        for find in finds:
            z = find["z"]
            if find["trench"] == "T1":
                # booked below his own bench mark and never reduced to datum
                z = z - surfaces["T1"]["tbm"]
            elif find["trench"] == "T4":
                z = site.DATUM_LEVEL_CM - z         # a level above Ordnance
            # plotted onto its section's drawing, and so in that drawing's frame
            t = surfaces[find["trench"]]
            drawn = (find["x"] if find["section"] == "N"
                     else t["length"] - find["x"])
            writer.writerow([find["find"], find["trench"], find["section"],
                             fmt(drawn), fmt(z)])

    with open(out / "to_phase.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["find"])
        for name in sorted(wanted):
            writer.writerow([name])

    truth = {f["find"]: str(f["context"]) for f in finds if f["find"] in wanted}
    (out / "truth.json").write_text(json.dumps(truth, indent=1, sort_keys=True),
                                    newline="\n")


def main() -> int:
    outdir = sys.argv[1] if len(sys.argv) > 1 else str(
        pathlib.Path(__file__).resolve().parent.parent / "yard")
    rng = random.Random(SEED)

    trenches = [lay_trench(rng, name) for name in sorted(SUPERVISORS)]
    finds = []
    for t in trenches:
        finds.extend(drop_finds(rng, t, 80, len(finds) + 1))

    # Write the whole register with every find down for phasing, so the forty
    # that go out can be chosen on what the archive's habits actually do to
    # them rather than on hope.
    write(outdir, trenches, finds, {f["find"] for f in finds})

    import ref
    right = ref.run(outdir)
    truth = {f["find"]: str(f["context"]) for f in finds}
    wrong = [k for k in truth if right.get(k) != truth[k]]
    if wrong:
        print("FAILED: the reference and the site disagree on %d of %d finds"
              % (len(wrong), len(truth)))
        for k in wrong[:5]:
            print("   %s said %s was %s" % (k, right.get(k), truth[k]))
        return 1

    moved = {k: set() for k in truth}
    for axis, other in ref.OTHERS.items():
        reading = dict(ref.TRUE_READING)
        reading[axis] = other
        got = ref.run(outdir, reading)
        for k in truth:
            if got.get(k) != truth[k]:
                moved[k].add(axis)

    # The forty: every one moved by something, a good share of them by the way
    # the facing section runs, and no tidy spread for a solver to check against.
    # Chosen so that EVERY habit bites on a fair share of them. Left to chance
    # the forty came out lopsided - seventeen from the trench with the
    # exchanged columns and five from the one booked below ground - and a
    # solver could miss a habit altogether and still come within a find of the
    # pass mark.
    # Only finds that stand a centimetre clear of every line, so neither the
    # rule for a find on a boundary nor anyone's rounding decides an answer;
    # and only DEEP ones, so that a solver who reads the drawings the wrong way
    # about gets a plausible wrong context for every one of the forty rather
    # than a find hanging in the air that tells him something is amiss.
    detail = {f["find"]: f for f in finds}
    pool = [k for k in sorted(truth)
            if moved[k] and detail[k]["gap"] >= 1 and detail[k]["deep"]
            and detail[k]["clear"]]
    rng.shuffle(pool)
    cover = {axis: 0 for axis in ref.OTHERS}
    wanted = set()
    # A few from the trench that was kept to the manual, so the forty are not
    # conspicuously drawn from the four that were not.
    for pick in [k for k in pool if detail[k]["trench"] == "T5"][:5]:
        pool.remove(pick)
        wanted.add(pick)
        for axis in moved[pick]:
            cover[axis] += 1
    while len(wanted) < TO_PHASE and pool:
        need = min(cover, key=lambda a: cover[a])
        pick = next((k for k in pool if need in moved[k]), pool[0])
        pool.remove(pick)
        wanted.add(pick)
        for axis in moved[pick]:
            cover[axis] += 1
    if len(wanted) < TO_PHASE:
        print("FAILED: only %d finds are moved by anything" % len(wanted))
        return 1
    print("finds each habit moves among the forty: %s" % cover)

    write(outdir, trenches, finds, wanted)
    by_trench = {}
    for k in wanted:
        t = next(f["trench"] for f in finds if f["find"] == k)
        by_trench[t] = by_trench.get(t, 0) + 1
    print("trenches %d  finds %d  to phase %d  (given to the wrong team if the "
          "meeting point is read along the drawing: %d)"
          % (len(trenches), len(finds), len(wanted),
             sum(1 for k in wanted if "meeting" in moved[k])))
    print("by trench: %s" % dict(sorted(by_trench.items())))
    print("wrote %s" % outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
