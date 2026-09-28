"""Level the paths and take the probes first, then log the walks the way five
fieldworkers would.

    python gen.py [outdir]

Truth first: every probe is given its place on its path, and so its altitude
and the surface it was taken on, before any walk is logged, so every answer is
exact by construction.

Four of the five fieldworkers did not log as the protocol says - one wheel
counted feet, one miles, one logger wrote the distance rolled in each ten
seconds and not the running total, one wrote the seconds since the walk began
and not the time of day. Each of those cannot be right against the protocol and
shows at once, and each is a matter of units, never of direction.

The fifth thing is not like them. The protocol says a walk begins at the foot
of the path, where station distances are reckoned from. Two of the five walks
were made from the top down. Nothing says so, and nothing breaks: the wheel
rolls the same length either way and every reading still falls on the path.

On a hillside a walker's pace follows the grade as he meets it, and pace
against slope would give the end away to the first check anyone makes: a
relation between two means. So these are old railway paths, graded
for locomotives: nobody's pace changes on one in a hundred, and the pace here
depends on nothing in the records at all. What says which end a walk began at
is second order. A measuring wheel runs true on tarmac and chatters on ballast,
so the ground it covers from one ten seconds to the next is steady on one and
ragged on the other; its running total is right on both. Read from the wrong
end, the ragged stretches of the log fall on the tarmac. The paths are all
different, so no walk can be laid against another.
"""

from __future__ import annotations

import csv
import json
import pathlib
import random
import sys

import survey

SEED = 20261015
WANTED = 40

# path, name, fieldworker, habit, walked from the top?
PATHS = (
    ("P1", "Harter Incline", "Ormerod", "feet", False),
    ("P2", "Black Sail Tramway", "Pickup", "elapsed", False),
    ("P3", "Rossett Mineral Line", "Quarmby", "miles", True),
    ("P4", "Swirl Quarry Branch", "Riddle", "increments", False),
    ("P5", "Stake Moor Railway", "Sugden", None, True),
)
SAID = ("depth %d cm", "%d cm", "probe %d cm", "soil %d cm")


def level(rng):
    """A path's stations: (distance mm, altitude mm), a railway's steady
    climb from foot to top."""
    length = rng.randrange(8200, 11800) * 1000
    stations = [(0, rng.randrange(90, 260) * 1000)]
    grade = rng.uniform(0.6, 1.4)
    while stations[-1][0] < length:
        leg = rng.randrange(60, 300) * 1000 + rng.randrange(10) * 100
        grade = min(1.9, max(0.2, 0.8 * grade + rng.gauss(0.2, 0.25)))
        at, alt = stations[-1]
        rise = int(round(leg * grade / 100.0, -2))       # to the decimetre
        stations.append((at + leg, alt + rise))
    return stations


def surface(rng, length):
    """The surface schedule: (from mm, to mm, surface), whole metres."""
    out, at, last = [], 0, None
    while at < length:
        run = rng.randrange(300, 1500) * 1000
        kind = rng.choice([k for k in survey.CHATTER if k != last])
        end = length if length - (at + run) < 300000 else at + run
        out.append((at, end, kind))
        at, last = end, kind
    return out


def altitude(stations, chainage):
    for (a, low), (b, high) in zip(stations, stations[1:]):
        if a <= chainage <= b:
            return low + (high - low) * (chainage - a) / (b - a)
    raise ValueError(chainage)


def walk(rng, length, surfaces, probes, from_top):
    """The wheel's running total, mm, every ten seconds; and for every probe
    the second of the walk at which its reading was spoken."""
    stops = sorted((length - c if from_top else c) for c in probes)
    best = rng.uniform(3.4, 4.3) / 3.6 * 1000            # mm a second
    mood, fuss = 0.0, 0
    rolled, tick, log, spoken = 0, 0, [0], {}
    while rolled < length:
        chainage = length - rolled if from_top else rolled
        kind = next(k for a, b, k in surfaces
                    if a <= min(chainage, length - 1) < b)
        # A walker's pace wanders a little over minutes, and every so often he
        # has a minute or two of fuss - a gate, a puddle, a dog - wherever he
        # happens to be. The plain spread of his pace is mostly that, on every
        # surface, and a table of mean and spread by surface says nothing
        # either way. The wheel's chatter is what is left in the ordinary ten
        # seconds when the ten seconds either side are taken away.
        mood = 0.97 * mood + rng.gauss(0, 0.012)
        if fuss:
            fuss -= 1
        elif rng.random() < 1 / 70.0:
            fuss = rng.randrange(6, 18)
        step = best * (1 + mood) * survey.TICK_S \
            * (1 + rng.gauss(0, survey.CHATTER[kind])) \
            * (1 + (rng.gauss(0, 0.13) if fuss else 0.0))
        rolled = min(length, rolled + max(2000, int(step)))
        if stops and rolled >= stops[0]:
            rolled = stops.pop(0)
            tick += 1
            log.append(rolled)
            wait = rng.randrange(7, 22)                   # ticks standing still
            spoken[rolled] = tick * survey.TICK_S + rng.randrange(
                15, wait * survey.TICK_S - 15)
            for _ in range(wait):
                tick += 1
                log.append(rolled)
            continue
        tick += 1
        log.append(rolled)
    return log, spoken


def main() -> int:
    outdir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                          pathlib.Path(__file__).resolve().parent.parent / "yard")
    (outdir / "wheel").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    paths, readings = {}, []
    for path, name, who, habit, from_top in PATHS:
        stations = level(rng)
        length = stations[-1][0]
        # never a schedule that reads much the same from either end, or the
        # chatter would fit both and settle nothing
        while True:
            surfaces = surface(rng, length)
            along = [survey.ROUGHNESS[next(k for a, b, k in surfaces
                                           if a <= c < b)]
                     for c in range(0, length, 50000)]
            mean = sum(along) / len(along)
            spread = sum((v - mean) ** 2 for v in along)
            mirror = sum((v - mean) * (w - mean)
                         for v, w in zip(along, reversed(along)))
            if spread and mirror / spread < -0.25:
                break
        probes = set()
        while len(probes) < rng.randrange(52, 68):
            c = rng.randrange(300, length // 1000 - 300) * 1000 \
                + rng.randrange(10) * 100
            if all(abs(c - other) > 45000 for other in probes):
                probes.add(c)
        began = survey.clock("%02d:%02d:00" % (rng.randrange(7, 10),
                                               rng.randrange(0, 60)))
        log, spoken = walk(rng, length, surfaces, probes, from_top)
        paths[path] = {"name": name, "who": who, "habit": habit,
                       "from_top": from_top, "stations": stations,
                       "surfaces": surfaces, "began": began, "log": log}
        for c in probes:
            rolled = length - c if from_top else c
            a, b, kind = next(s for s in surfaces if s[0] <= c < s[1])
            # ... and how clear of a change of surface it stands read from
            # the other end: a cold solver took a probe that fell exactly
            # on a change, read the wrong way, as a sign he had it right
            turned = min(abs(length - c - edge)
                         for s in surfaces for edge in s[:2])
            readings.append({"path": path, "chainage": c,
                             "time": began + spoken[rolled],
                             "said": rng.choice(SAID) % rng.randrange(3, 41),
                             "clear": min(c - a, b - c, turned),
                             "answer": "%.1f %s" % (altitude(stations, c)
                                                    / 1000.0, kind)})
    rng.shuffle(readings)
    for number, reading in enumerate(readings, 1):
        reading["reading"] = "Q%03d" % number

    def write(wanted):
        with open(outdir / "paths.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["path", "name", "walked_by", "walk_began"])
            for path, p in paths.items():
                writer.writerow([path, p["name"], p["who"],
                                 survey.as_clock(p["began"])])
        with open(outdir / "stations.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["path", "station", "distance_m", "altitude_m"])
            for path, p in paths.items():
                for index, (at, alt) in enumerate(p["stations"], 1):
                    writer.writerow([path, "%s-%03d" % (path, index),
                                     "%.1f" % (at / 1000.0),
                                     "%.1f" % (alt / 1000.0)])
        with open(outdir / "surfaces.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["path", "from_m", "to_m", "surface"])
            for path, p in paths.items():
                for a, b, kind in p["surfaces"]:
                    writer.writerow([path, "%.1f" % (a / 1000.0),
                                     "%.1f" % (b / 1000.0), kind])
        for path, p in paths.items():
            with open(outdir / "wheel" / (path + ".csv"), "w",
                      newline="") as fh:
                writer = csv.writer(fh, lineterminator="\n")
                writer.writerow(["time", "distance_m"])
                before = 0
                for tick, rolled in enumerate(p["log"]):
                    time = survey.as_clock(p["began"] + tick * survey.TICK_S)
                    shown = "%.1f" % (rolled / 1000.0)
                    if p["habit"] == "feet":
                        shown = "%.1f" % (rolled / float(survey.FOOT_MM))
                    elif p["habit"] == "miles":
                        shown = "%.4f" % (rolled / float(survey.MILE_MM))
                    elif p["habit"] == "increments":
                        now = int(round(rolled / 100.0))
                        shown = "%.1f" % ((now - before) / 10.0)
                        before = now
                    elif p["habit"] == "elapsed":
                        time = str(tick * survey.TICK_S)
                    writer.writerow([time, shown])
        with open(outdir / "readings.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["reading", "path", "time", "said"])
            for r in sorted(readings, key=lambda r: r["reading"]):
                writer.writerow([r["reading"], r["path"],
                                 survey.as_clock(r["time"]), r["said"]])
        (outdir / "paper.txt").write_text(
            "".join(name + "\n" for name in sorted(wanted)), newline="\n")
        (outdir / "truth.json").write_text(json.dumps(
            {r["reading"]: r["answer"] for r in readings
             if r["reading"] in wanted}, indent=1, sort_keys=True),
            newline="\n")

    by_name = {r["reading"]: r for r in readings}
    write(set(by_name))

    import ref

    right = ref.run(outdir)
    wrong = [k for k in by_name
             if not survey.agrees(right.get(k), by_name[k]["answer"])]
    if wrong:
        print("FAILED: the reference and the paths disagree on %d of %d"
              % (len(wrong), len(by_name)))
        for k in wrong[:5]:
            print("   %s said %s was %s" % (k, right.get(k),
                                            by_name[k]["answer"]))
        return 1

    moved = {k: set() for k in by_name}
    for axis, other in ref.OTHERS.items():
        got = ref.run(outdir, dict(ref.TRUE_READING, **{axis: other}))
        for k, r in by_name.items():
            # moved well clear of the half metre, so nothing scrapes through
            if not survey.agrees(got.get(k), r["answer"], slack=5.0,
                                 surface=False):
                moved[k].add(axis)

    # Eight from every path, each one moved by everything that applies to its
    # walk, so that no habit is decoration and the end a walk began at matters;
    # and each fifteen metres clear of a change of surface, from either end.
    wanted = set()
    for path, p in paths.items():
        need = {"walked_from"} if p["from_top"] else set()
        if p["habit"]:
            need.add(p["habit"])
        mine = [k for k in sorted(by_name) if by_name[k]["path"] == path
                and need <= moved[k] and by_name[k]["clear"] >= 15000]
        rng.shuffle(mine)
        wanted.update(mine[:WANTED // len(PATHS)])
    cover = {axis: sum(1 for k in wanted if axis in moved[k])
             for axis in ref.OTHERS}

    write(wanted)
    (outdir / "walked.json").write_text(json.dumps(
        {path: ("top" if p["from_top"] else "foot")
         for path, p in paths.items()}, indent=1, sort_keys=True),
        newline="\n")
    print("paths %d  stations %d  log rows %d  readings %d  wanted %d"
          % (len(paths), sum(len(p["stations"]) for p in paths.values()),
             sum(len(p["log"]) for p in paths.values()), len(readings),
             len(wanted)))
    print("readings each habit moves among the forty: %s" % cover)
    print("wrote %s" % outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
