"""Make the ground first, then book it the way five surveyors would.

    python lay_ground.py [outdir]

Truth first. Each scheme's ground is a surface in the designer's own frame -
offsets positive to the right looking up chainage - and every wanted figure is
taken off that. Only then is each field book written, in its surveyor's units
and with his hand.

Nothing ties a booked level to a side of the road through a mean. The schemes
cross no ditch, bank or hedge; the ground falls across the road whichever way
it falls; every section is booked as far one way as the other, at spacings that
have nothing to do with the land. What the land does leave is second order:
ploughed ground is rougher from one staff position to the next than pasture,
with woodland between, and here and there a gateway or a track is rough on any
land.
"""

import csv
import json
import math
import pathlib
import random
import sys

import template

SEED = 60221
WANTED_PER_SCHEME = 8
ROUGH_M = {"pasture": 0.012, "woodland": 0.035, "arable": 0.06}

SCHEMES = (
    # scheme, name, surveyor, his unit habit, offsets booked positive left?
    ("S1", "Hollin Lane link", "Varley", "levels_feet", False),
    ("S2", "Carr Bottom bypass", "Wadsworth", None, True),
    ("S3", "Moor End junction", "Yeadon", "chainage_km", False),
    ("S4", "Station Road diversion", "Ackroyd", "offsets_feet", True),
    ("S5", "Quarry Hill access", "Binns", "levels_mm", False),
)


def schedule_land(rng, length):
    """Strips of land across the scheme, in two or three chainage blocks; never
    a block that reads much the same from the other side of the road."""
    blocks, start = [], 0
    cuts = sorted(rng.sample(range(100, length - 60, 20), rng.choice((1, 2))))
    for end in cuts + [length + 20]:
        while True:
            strips, at, last = [], -45.0, None
            while at < 45.0:
                wide = rng.choice((14, 18, 22, 27, 33))
                to = 45.0 if 45.0 - (at + wide) < 10 else at + wide
                kind = rng.choice([k for k in ROUGH_M if k != last])
                strips.append((at, to, kind))
                at, last = to, kind
            rank = [template.ROUGHEST_LAST.index(k) for x in range(-44, 45)
                    for a, b, k in strips if a <= x < b]
            mean = sum(rank) / len(rank)
            spread = sum((v - mean) ** 2 for v in rank)
            turned = sum((v - mean) * (w - mean)
                         for v, w in zip(rank, reversed(rank)))
            if spread and turned / spread < -0.2:
                break
        blocks += [(start, end, a, b, k) for a, b, k in strips]
        start = end
    return blocks


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "yard"
    (outdir / "sections").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    job, candidates = {}, []
    for name, title, surveyor, habit, left_positive in SCHEMES:
        length = rng.randrange(440, 820, 20)
        land = schedule_land(rng, length)
        base = rng.uniform(70, 150)
        grade = rng.uniform(-0.03, 0.03)
        cross0, cross1 = rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12)
        # long undulations only: a wave's height goes with its length, so that
        # the ground's own curvature over a few metres stays under the pasture's
        # roughness
        waves = []
        for _ in range(6):
            wavelength = rng.uniform(45, 160)
            waves.append((wavelength / rng.uniform(180, 320), wavelength,
                          rng.uniform(0, 6.3), rng.uniform(0, 3.14)))
        tracks = [(rng.uniform(0, length), rng.uniform(-40, 40),
                   rng.uniform(15, 50), rng.uniform(4, 8))
                  for _ in range(int(length / 45))]
        scheme = dict(title=title, surveyor=surveyor, habit=habit,
                      left_positive=left_positive, land=land,
                      left=rng.choice((4.0, 4.5, 5.0, 5.5)),
                      right=rng.choice((8.0, 8.75, 9.5, 10.25)),
                      cut_slope=2.0, fill_slope=2.5, formation={},
                      sections={})

        def kind_at(chainage, x):
            for c0, c1, a, b, k in land:
                if c0 <= chainage < c1 and a <= x < b:
                    return k
            return land[-1][4]

        for chainage in range(0, length + 1, 10):
            cross = cross0 + (cross1 - cross0) * chainage / length
            reach_l, reach_r = rng.uniform(33, 41), rng.uniform(33, 41)
            # staff positions run on from well outside the section, and only those
            # inside it are booked, so that one end of a section is no different
            # from the other: an earlier build began every section exactly at its
            # left reach, and a cold solver read the hand off the first offsets
            xs, x = [], -reach_l - rng.uniform(8, 12)
            while x < reach_r:
                if x >= -reach_l:
                    xs.append(round(x, 1))
                x += rng.uniform(1.2, 3.2)
            points = []
            for x in xs:
                z = base + grade * chainage + cross * x
                for height, wavelength, phase, bearing in waves:
                    z += height * math.sin(
                        2 * math.pi * (chainage * math.cos(bearing)
                                       + x * math.sin(bearing)) / wavelength
                        + phase)
                z += rng.gauss(0, ROUGH_M[kind_at(chainage, x)])
                if any(abs(chainage - c) < run and abs(x - o) < wide
                       for c, o, run, wide in tracks):
                    z += rng.gauss(0, 0.08)
                points.append((x, round(z + rng.gauss(0, 0.004), 2)))
            centre = template.ground_at(points, 0.0)
            formation = round(centre + rng.uniform(-1.6, 1.6), 2)
            scheme["formation"][chainage] = formation
            scheme["sections"][chainage] = points

            strips = [(a, b, k) for c0, c1, a, b, k in land
                      if c0 <= chainage < c1]
            both = []
            for flipped in (False, True):
                seen = sorted((-px, pz) for px, pz in points) if flipped \
                    else points
                try:
                    areas = template.take_off(
                        seen, formation, scheme["left"], scheme["right"],
                        scheme["cut_slope"], scheme["fill_slope"], strips)
                except ValueError:
                    areas = None
                edges = [abs(template.ground_at(seen, e) - formation)
                         for e in (-scheme["left"], scheme["right"])]
                both.append((areas, min(edges)))
            (true_areas, firm_a), (turned_areas, firm_b) = both
            if true_areas and turned_areas and min(firm_a, firm_b) >= 0.25 \
                    and max(true_areas[0], true_areas[1]) < 60:
                candidates.append(dict(
                    scheme=name, key="%s/%04d" % (name, chainage),
                    areas=[round(v, 1) for v in true_areas],
                    turned=[round(v, 1) for v in turned_areas]))
        job[name] = scheme

    def write(wanted):
        with open(outdir / "schemes.csv", "w", newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            out.writerow(["scheme", "name", "levelled_by", "left_width_m",
                          "right_width_m", "cut_slope_1_in",
                          "fill_slope_1_in"])
            for name, s in job.items():
                out.writerow([name, s["title"], s["surveyor"], s["left"],
                              s["right"], s["cut_slope"], s["fill_slope"]])
        with open(outdir / "formation.csv", "w", newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            out.writerow(["scheme", "chainage_m", "formation_level_m"])
            for name, s in job.items():
                for chainage, level in sorted(s["formation"].items()):
                    out.writerow([name, chainage, "%.2f" % level])
        with open(outdir / "land.csv", "w", newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            out.writerow(["scheme", "from_chainage_m", "to_chainage_m",
                          "from_offset_m", "to_offset_m", "land"])
            for name, s in job.items():
                for c0, c1, a, b, kind in s["land"]:
                    out.writerow([name, c0, c1, "%.1f" % a, "%.1f" % b, kind])
        for name, s in job.items():
            with open(outdir / "sections" / (name + ".csv"), "w",
                      newline="") as handle:
                out = csv.writer(handle, lineterminator="\n")
                out.writerow(["chainage_m", "offset_m", "level_m"])
                for chainage, points in sorted(s["sections"].items()):
                    booked = [(-x, z) for x, z in points] \
                        if s["left_positive"] else points
                    for x, z in sorted(booked):
                        where = "%.3f" % (chainage / 1000.0) \
                            if s["habit"] == "chainage_km" else str(chainage)
                        offset = "%.1f" % (x / template.FOOT_M) \
                            if s["habit"] == "offsets_feet" else "%.1f" % x
                        if s["habit"] == "levels_feet":
                            level = "%.2f" % (z / template.FOOT_M)
                        elif s["habit"] == "levels_mm":
                            level = "%d" % round(z * 1000)
                        else:
                            level = "%.2f" % z
                        out.writerow([where, offset, level])
        (outdir / "wanted.txt").write_text(
            "".join(k + "\n" for k in sorted(wanted)), newline="\n")
        (outdir / "sealed.json").write_text(json.dumps(
            {c["key"]: c["areas"] for c in candidates if c["key"] in wanted},
            indent=1, sort_keys=True), newline="\n")

    write({c["key"] for c in candidates})
    (outdir / "hands.json").write_text(json.dumps(
        {name: ("left_positive" if s["left_positive"] else "right_positive")
         for name, s in job.items()}, indent=1), newline="\n")

    import take_off

    # the reference works from what was BOOKED (feet and rounding and all), so
    # the sealed figures are the reference's own, and must agree with the true
    # ground's to within the rounding of a field book
    said = take_off.figures(outdir)
    adrift = [c["key"] for c in candidates
              if not template.agree(said.get(c["key"], ()), c["areas"], 0.35)]
    firm = [c for c in candidates if c["key"] not in adrift]
    for c in firm:
        c["areas"] = said[c["key"]]

    wanted = set()
    for name, s in job.items():
        mine = [c for c in firm if c["scheme"] == name
                and max(abs(a - b) for a, b in zip(c["areas"], c["turned"]))
                >= 1.5]
        rng.shuffle(mine)
        wanted.update(c["key"] for c in mine[:WANTED_PER_SCHEME])
    write(wanted)
    print("schemes %d  sections %d  booked points %d  candidates %d (adrift "
          "%d)  wanted %d"
          % (len(job), sum(len(s["sections"]) for s in job.values()),
             sum(len(p) for s in job.values() for p in s["sections"].values()),
             len(candidates), len(adrift), len(wanted)))
    return 0 if len(wanted) == WANTED_PER_SCHEME * len(job) else 1


if __name__ == "__main__":
    raise SystemExit(main())
