"""Run five junctions for a week, then write what the signals team holds.

    python run_week.py [outdir]

The week happens first, on one clock: the control system changes each
junction's plan when the wider network calls for it, traffic arrives at each
count site as that street's day dictates, and a plan run's vehicles are counted
from that. Then each count site's log is written the way its counter writes
one - and stamped by that counter's own clock, which at two sites was set by
hand from somebody's watch and is most of an hour out.

Nothing a count can show in the mean says so. A plan is chosen for the network,
not for the street, so a street's flow neither rises nor falls when its plan
changes; every street has its own day, so no two sites' peaks are there to be
compared; and plans change on the run. What a plan does change is how the
traffic is bunched when it reaches the counter: a long cycle sends it down in
tight platoons and a short one smooths it out. Twenty seconds to the next, the
counts are more ragged under one plan than another, and that steps when the
plan does.
"""

import csv
import json
import math
import pathlib
import random
import sys

SEED = 1414213
START = "2026-10-12 00:00:00"
DAYS = 7
EVERY_S = 20
WANTED_EACH = 8

SITES = (
    # junction, street of its count site, how the counter writes, minutes fast
    ("J1", "commercial-street", "plain", 0),
    ("J2", "wharf-road", "plain", 47),
    ("J3", "northgate", "hourly rate", 0),
    ("J4", "station-approach", "by lane", -58),
    ("J5", "mill-lane", "day first", 0),
)
BUNCHING = {"P1": 0.03, "P2": 0.30, "P3": 1.00}   # extra spread, by plan


def stamp(seconds):
    days, rest = divmod(int(seconds), 86400)
    return "2026-10-%02d %02d:%02d:%02d" % (12 + days, rest // 3600,
                                            rest % 3600 // 60, rest % 60)


def stamp12(seconds):
    days, rest = divmod(int(seconds), 86400)
    hour = rest // 3600
    return "2026-10-%02d %02d:%02d:%02d %s" % (
        12 + days, (hour + 11) % 12 + 1, rest % 3600 // 60, rest % 60,
        "AM" if hour < 12 else "PM")


def poisson(rng, mean):
    if mean > 30:
        return max(0, int(round(rng.gauss(mean, math.sqrt(mean)))))
    limit, k, p = math.exp(-mean), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "town"
    (outdir / "detectors").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    span = DAYS * 86400
    changes_out, sealed, offsets, candidates = [], {}, {}, {}

    for site, street, way, fast_min in SITES:
        # the plan runs, on the true clock
        changes, at, last = [], -rng.uniform(1, 3) * 3600, None
        while at < span:
            last = rng.choice([p for p in BUNCHING if p != last])
            changes.append((int(at // 60) * 60, last))
            at += rng.uniform(1.6, 4.2) * 3600
        # this street's day: two or three humps at hours of its own
        humps = [(rng.uniform(5.5, 21.0) * 3600, rng.uniform(1.0, 2.6) * 3600,
                  rng.uniform(0.5, 1.2)) for _ in range(rng.randrange(2, 4))]
        base = rng.uniform(1.3, 2.2)                  # vehicles in 20 s, by day
        began = rng.uniform(1.0, 5.0) * 3600 + rng.randrange(0, 1200)
        ended = span - rng.uniform(1.0, 5.0) * 3600
        began, ended = int(began // EVERY_S) * EVERY_S, \
            int(ended // EVERY_S) * EVERY_S
        wander, upset, counts, k = 0.0, 0, [], 0
        for t in range(began, ended, EVERY_S):
            while k + 1 < len(changes) and changes[k + 1][0] <= t:
                k += 1
            of_day = t % 86400
            # a day runs into the next: a hump late in the evening is still
            # falling away after midnight, so the day's shape has no seam
            level = 0.25 + sum(
                h * math.exp(-0.5 * (((of_day - c + 43200) % 86400 - 43200)
                                     / w) ** 2) for c, w, h in humps)
            wander = 0.995 * wander + rng.gauss(0, 0.012)
            if upset:
                upset -= 1
            elif rng.random() < 1 / 1500.0:
                upset = rng.randrange(20, 90)         # a bus, a delivery, a shunt
            mean = base * 4.0 * level * (1 + wander)
            shape = 1.0 / BUNCHING[changes[k][1]]
            mean *= rng.gammavariate(shape, 1.0 / shape)
            if upset:
                mean *= rng.choice((0.2, 0.5, 1.6))
            counts.append((t, poisson(rng, mean)))

        # a plan run's vehicles: every twenty seconds that began inside it
        runs = []
        for n, ((a, plan), (b, _)) in enumerate(zip(changes, changes[1:]), 1):
            if a >= began + 5400 and b <= ended - 5400:
                true = sum(c for t, c in counts if a <= t < b)
                slid = sum(c for t, c in counts
                           if a <= t + fast_min * 60 < b)
                runs.append(("%s-%03d" % (site, n), true, slid))
        candidates[site] = runs
        for n, (a, plan) in enumerate(changes, 1):
            if a >= 0:
                changes_out.append((a, site, "%s-%03d" % (site, n), plan))

        with open(outdir / "detectors" / (street + ".csv"), "w",
                  newline="") as handle:
            if way == "day first":
                out = csv.writer(handle, delimiter=";", lineterminator="\n")
            else:
                out = csv.writer(handle, lineterminator="\n")
            out.writerow(["interval_start", "nearside", "offside"]
                         if way == "by lane" else ["interval_start", "count"])
            for t, c in counts:
                shown = stamp(t + fast_min * 60)
                if way == "hourly rate":
                    out.writerow([shown, c * 3600 // EVERY_S])
                elif way == "by lane":
                    near = sum(1 for _ in range(c) if rng.random() < 0.62)
                    out.writerow([shown, near, c - near])
                elif way == "day first":
                    out.writerow(["%s/%s/%s %s" % (shown[8:10], shown[5:7],
                                                   shown[:4], shown[11:]), c])
                else:
                    out.writerow([shown, c])
        offsets[site] = dict(fast_min=fast_min, way=way, street=street)

    for site, street, way, fast_min in SITES:
        runs = candidates[site]
        if fast_min:            # only runs the wrong clock really gets wrong
            runs = [r for r in runs if abs(r[2] - r[1]) > 0.06 * r[1]]
        rng.shuffle(runs)
        for run, true, _ in runs[:WANTED_EACH]:
            sealed[run] = true

    # the control system's own event log, one line for every change of plan
    (outdir / "controller.log").write_bytes("".join(
        "%s | %s | run %s | plan %s selected\n" % (stamp(a).replace(" ", "T"),
                                                  site, run, plan)
        for a, site, run, plan in sorted(changes_out)).encode())
    (outdir / "COUNTS.md").write_bytes(
        (pathlib.Path(__file__).resolve().parent / "parts"
         / "COUNTS.md").read_bytes())
    (outdir / "runs_wanted.txt").write_bytes(
        "".join(r + "\n" for r in sorted(sealed)).encode())
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "clocks.json").write_bytes(json.dumps(offsets, indent=1).encode())
    print("junctions %d  changes %d  runs wanted %d"
          % (len(SITES), len(changes_out), len(sealed)))
    return 0 if len(sealed) == WANTED_EACH * len(SITES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
