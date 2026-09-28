"""Lay the routes and sound the alarms first, then log the blows the way five
crews would.

    python gen.py [outdir]

Truth first: every alarm is given the place on its route where the cable head
stood when it sounded, and so its distance from the A chamber and the duct it
was in, before any blow is logged, so every answer is exact by construction.

Four of the five crews did not log as the procedure says - one machine counts
feet, one centimetres, one writes the length paid out in each second and not
the running total, one writes the seconds since the blow began and not the time
of day. Each of those cannot be right against the procedure and shows at once,
and each is a matter of units, never of direction.

The fifth thing is not like them. The procedure sets the machine up at the A
chamber, where a route's distances are reckoned from. Two of the five routes
were blown from the far chamber - a crew blows from wherever it can park the
compressor. Nothing says so, and nothing breaks: the cable runs the length of
its route either way and every alarm still falls on it.

No mean says it. The machine holds a set speed whatever duct the cable head is
in, so the speed in the logs follows nothing in the schedule, from either end.
What says it is second order. Cable runs sweetly into smoothwall duct and
raggedly into old earthenware, so the length paid out from one second to the
next is steady in the one and ragged in the other; the running total is right
in both. Read from the wrong end, the ragged stretches of the log fall in the
smoothwall. A crew's speed also wanders a little over minutes, and every so
often there is half a minute of fuss with the air or the pusher, wherever the
head happens to be, so that a table of mean and spread by kind of duct says
nothing either way. The routes are all different, so no blow can be laid
against another.
"""

from __future__ import annotations

import csv
import json
import pathlib
import random
import sys

import blowing

SEED = 20261201
WANTED = 40

# route, from-to, crew, habit, blown from the far chamber?
ROUTES = (
    ("R1", "Exchange to Mill Lane", "Crew 4", "centimetres", False),
    ("R2", "Mill Lane to Quarry Rd", "Crew 7", "per_second", True),
    ("R3", "Station Yard to Ings", "Crew 2", "feet", False),
    ("R4", "Ings to Water Tower", "Crew 5", None, True),
    ("R5", "Exchange to Canal Head", "Crew 9", "elapsed", False),
)


def schedule(rng):
    """A route's duct schedule: (from mm, to mm, kind), whole metres."""
    length = rng.randrange(1500, 2600) * 1000
    out, at, last = [], 0, None
    while at < length:
        run = rng.randrange(60, 320) * 1000
        kind = rng.choice([k for k in blowing.RAGGED if k != last])
        end = length if length - (at + run) < 60000 else at + run
        out.append((at, end, kind))
        at, last = end, kind
    return out


def blow(rng, length, ducts, alarms, from_far):
    """The counter's running total, mm, every second; and for every alarm the
    second of the blow at which it sounded."""
    stops = sorted((length - c if from_far else c) for c in alarms)
    set_speed = rng.uniform(0.85, 1.15) * 1000           # mm a second
    mood, fuss = 0.0, 0
    paid, tick, log, sounded = 0, 0, [0], {}
    while paid < length:
        head = length - paid if from_far else paid
        kind = next(k for a, b, k in ducts if a <= min(head, length - 1) < b)
        mood = 0.97 * mood + rng.gauss(0, 0.012)
        if fuss:
            fuss -= 1
        elif rng.random() < 1 / 110.0:
            fuss = rng.randrange(10, 35)
        step = set_speed * (1 + mood) \
            * (1 + rng.gauss(0, blowing.RAGGED[kind])) \
            * (1 + (rng.gauss(0, 0.13) if fuss else 0.0))
        paid = min(length, paid + max(200, int(step)))
        if stops and paid >= stops[0]:
            paid = stops.pop(0)
            tick += 1
            log.append(paid)
            wait = rng.randrange(25, 90)                  # seconds stopped
            sounded[paid] = tick + rng.randrange(0, 3)
            for _ in range(wait):
                tick += 1
                log.append(paid)
            continue
        tick += 1
        log.append(paid)
    return log, sounded


def main() -> int:
    outdir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                          pathlib.Path(__file__).resolve().parent.parent / "yard")
    (outdir / "blows").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    routes, alarms = {}, []
    for route, where, crew, habit, from_far in ROUTES:
        # never a schedule that reads much the same from either end, or the
        # raggedness would fit both and settle nothing
        while True:
            ducts = schedule(rng)
            length = ducts[-1][1]
            along = [blowing.ROUGHNESS[next(k for a, b, k in ducts
                                            if a <= c < b)]
                     for c in range(0, length, 20000)]
            mean = sum(along) / len(along)
            spread = sum((v - mean) ** 2 for v in along)
            mirror = sum((v - mean) * (w - mean)
                         for v, w in zip(along, reversed(along)))
            if spread and mirror / spread < -0.25:
                break
        places = set()
        while len(places) < rng.randrange(28, 36):
            c = rng.randrange(40, length // 1000 - 40) * 1000 \
                + rng.randrange(10) * 100
            if all(abs(c - other) > 20000 for other in places):
                places.add(c)
        began = blowing.clock("%02d:%02d:00" % (rng.randrange(7, 15),
                                                rng.randrange(0, 60)))
        log, sounded = blow(rng, length, ducts, places, from_far)
        routes[route] = {"where": where, "crew": crew, "habit": habit,
                         "from_far": from_far, "ducts": ducts,
                         "began": began, "log": log, "length": length}
        for c in places:
            paid = length - c if from_far else c
            a, b, kind = next(d for d in ducts if d[0] <= c < d[1])
            # how clear of a joint between kinds it stands, from either end
            turned = min(abs(length - c - edge) for d in ducts for edge in d[:2])
            alarms.append({"route": route, "time": began + sounded[paid],
                           "clear": min(c - a, b - c, turned),
                           "answer": "%.1f %s" % (c / 1000.0, kind)})
    rng.shuffle(alarms)
    for number, alarm in enumerate(alarms, 1):
        alarm["alarm"] = "A%03d" % number

    def write(wanted):
        with open(outdir / "routes.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["route", "from_a_to_b", "crew", "blow_began"])
            for route, r in routes.items():
                writer.writerow([route, r["where"], r["crew"],
                                 blowing.as_clock(r["began"])])
        with open(outdir / "ducts.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["route", "from_m", "to_m", "duct"])
            for route, r in routes.items():
                for a, b, kind in r["ducts"]:
                    writer.writerow([route, "%.1f" % (a / 1000.0),
                                     "%.1f" % (b / 1000.0), kind])
        for route, r in routes.items():
            with open(outdir / "blows" / (route + ".csv"), "w",
                      newline="") as fh:
                writer = csv.writer(fh, lineterminator="\n")
                writer.writerow(["time", "paid_out_m"])
                before = 0
                for tick, paid in enumerate(r["log"]):
                    time = blowing.as_clock(r["began"] + tick)
                    shown = "%.2f" % (paid / 1000.0)
                    if r["habit"] == "feet":
                        shown = "%.2f" % (paid / float(blowing.FOOT_MM))
                    elif r["habit"] == "centimetres":
                        shown = str(int(round(paid / 10.0)))
                    elif r["habit"] == "per_second":
                        now = int(round(paid / 10.0))
                        shown = "%.2f" % ((now - before) / 100.0)
                        before = now
                    elif r["habit"] == "elapsed":
                        time = str(tick)
                    writer.writerow([time, shown])
        with open(outdir / "alarms.csv", "w", newline="") as fh:
            writer = csv.writer(fh, lineterminator="\n")
            writer.writerow(["alarm", "route", "time"])
            for a in sorted(alarms, key=lambda a: a["alarm"]):
                writer.writerow([a["alarm"], a["route"],
                                 blowing.as_clock(a["time"])])
        (outdir / "follow_up.txt").write_text(
            "".join(name + "\n" for name in sorted(wanted)), newline="\n")
        (outdir / "truth.json").write_text(json.dumps(
            {a["alarm"]: a["answer"] for a in alarms if a["alarm"] in wanted},
            indent=1, sort_keys=True), newline="\n")

    by_name = {a["alarm"]: a for a in alarms}
    write(set(by_name))

    import ref

    right = ref.run(outdir)
    wrong = [k for k in by_name
             if not blowing.agrees(right.get(k), by_name[k]["answer"])]
    if wrong:
        print("FAILED: the reference and the routes disagree on %d of %d"
              % (len(wrong), len(by_name)))
        for k in wrong[:5]:
            print("   %s said %s was %s" % (k, right.get(k),
                                            by_name[k]["answer"]))
        return 1

    moved = {k: set() for k in by_name}
    for axis, other in ref.OTHERS.items():
        got = ref.run(outdir, dict(ref.TRUE_READING, **{axis: other}))
        for k, a in by_name.items():
            # moved well clear of the two metres, so nothing scrapes through
            if not blowing.agrees(got.get(k), a["answer"], slack=30.0,
                                  duct=False):
                moved[k].add(axis)

    # Eight from every route, each one moved by everything that applies to its
    # blow, and each ten metres clear of a change of duct, from either end.
    wanted = set()
    for route, r in routes.items():
        need = {"blown_from"} if r["from_far"] else set()
        if r["habit"]:
            need.add(r["habit"])
        mine = [k for k in sorted(by_name) if by_name[k]["route"] == route
                and need <= moved[k] and by_name[k]["clear"] >= 10000]
        rng.shuffle(mine)
        wanted.update(mine[:WANTED // len(ROUTES)])
    cover = {axis: sum(1 for k in wanted if axis in moved[k])
             for axis in ref.OTHERS}

    write(wanted)
    (outdir / "blown.json").write_text(json.dumps(
        {route: ("far" if r["from_far"] else "a")
         for route, r in routes.items()}, indent=1, sort_keys=True),
        newline="\n")
    print("routes %d  duct lengths %d  log rows %d  alarms %d  wanted %d"
          % (len(routes), sum(len(r["ducts"]) for r in routes.values()),
             sum(len(r["log"]) for r in routes.values()), len(alarms),
             len(wanted)))
    print("alarms each habit moves among the forty: %s" % cover)
    print("wrote %s" % outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
