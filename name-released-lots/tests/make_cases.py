"""Build the store's campaigns.

    python make_cases.py worked worked.json

A campaign is a plain list of events - nothing is disguised or left in an odd
unit anywhere in it. Two sets come out of two seeds:

  * the WORKED set ships with the task, each campaign carrying its answers. Its
    campaigns plant the edges the open matters turn on, so settling one of them
    the wrong way shows up in them.
  * the GRADED set is rebuilt inside the verifier and never ships. It does not
    go looking for those edges, so an honest slip costs almost nothing there.
"""

import json
import random
import sys

MIN_FREE = 100
VALID_DAYS = 365

WORKED_SEED, WORKED_CASES = 20260922, 14
GRADED_SEED, GRADED_CASES = 7731904, 30


def make_case(rng, span=None, boundaries=True):
    if span is None:
        span = 520 if boundaries else 200
    names = ["ACC%02d" % n for n in rng.sample(range(10, 80), 3)]
    standards = {a: rng.choice([75, 80, 85, 90]) for a in names}
    events, lots, day, serial, failing, size = [], {}, 0, 0, {}, {}

    for a in names:
        for _ in range(5):
            serial += 1
            lot = "L%03d" % serial
            events.append(dict(kind="DEPOSIT", day=day, lot=lot, accession=a,
                               seeds=rng.randrange(200, 700),
                               test=rng.choice(
                                   [rng.randrange(standards[a] - 6, standards[a])] * 3 +
                                   [rng.randrange(standards[a] + 1, 100)] * 6)))
            lots.setdefault(a, []).append(lot)
            failing[lot] = events[-1]["test"] < standards[a]
            size[lot] = events[-1]["seeds"]
            day += rng.randrange(1, 6)

    while day < span:
        day += rng.randrange(4, 20)
        a = rng.choice(names)
        live = lots[a]
        lot = rng.choice(live)
        bar = standards[a]
        roll = rng.random()

        if roll < 0.14:
            result = rng.choice([bar + 1] * 2 + [rng.randrange(bar - 6, bar)] * 3 +
                                [rng.randrange(bar + 1, 100)] * 5)
            events.append(dict(kind="TEST", day=day, lot=lot, test=result))
            failing[lot] = result < bar
        elif roll < 0.44 and len(live) > 1:
            giver = rng.choice([x for x in live if x != lot and size.get(x, 0) > 120]
                               or [x for x in live if x != lot])
            moved = min(rng.randrange(60, 220), max(20, size.get(giver, 0) - 30))
            events.append(dict(kind="TOPUP", day=day, into=lot,
                               **{"from": giver}, seeds=moved))
            size[lot] = size.get(lot, 0) + moved
            size[giver] = size.get(giver, 0) - moved
        elif roll < 0.60:
            serial += 1
            child = "L%03d" % serial
            taken = (rng.choice([MIN_FREE, MIN_FREE - 1, rng.randrange(150, 320)])
                     if boundaries else rng.randrange(150, 320))
            taken = min(taken, max(20, size.get(lot, 0) - 40))
            events.append(dict(kind="SPLIT", day=day, parent=lot, child=child,
                               seeds=taken))
            size[lot] = size.get(lot, 0) - taken
            size[child] = taken
            live.append(child)
            failing[child] = failing.get(lot, False)
        elif roll < 0.68:
            serial += 1
            fresh = "L%03d" % serial
            events.append(dict(kind="REGEN", day=day, lot=lot, new_lot=fresh,
                               seeds=rng.randrange(300, 800),
                               test=rng.randrange(bar + 1, 100)))
            if not boundaries:
                events.insert(len(events) - 1,
                              dict(kind="WITHDRAW", day=day, lot=lot, seeds=10 ** 6))
            live.append(fresh)
            size[fresh] = events[-1]["seeds"]
            failing[fresh] = False
        elif roll < 0.76:
            taken = min(rng.randrange(60, 300), max(0, size.get(lot, 0) - 20))
            events.append(dict(kind="WITHDRAW", day=day, lot=lot, seeds=taken))
            size[lot] = size.get(lot, 0) - taken
        else:
            events.append(dict(kind="REQUEST", day=day, accession=a))
            if boundaries and rng.random() < 0.4:
                events.insert(len(events) - 1,
                              dict(kind="TEST", day=day, lot=lot,
                                   test=rng.choice([bar + 1, bar + 2])))

    for a in names:
        for _ in range(2):
            day += rng.randrange(4, 18)
            events.append(dict(kind="REQUEST", day=day, accession=a))
    return dict(standards=standards, events=events)


def worked_set():
    return [make_case(random.Random(WORKED_SEED + i), boundaries=True)
            for i in range(WORKED_CASES)]


def graded_set():
    return [make_case(random.Random(GRADED_SEED + i), boundaries=False)
            for i in range(GRADED_CASES)]


def main():
    import releases
    if len(sys.argv) != 3 or sys.argv[1] != "worked":
        raise SystemExit("usage: make_cases.py worked <outfile>")
    worked = [dict(campaign=c, answers=releases.play(c)) for c in worked_set()]
    with open(sys.argv[2], "w", newline=chr(10)) as handle:
        handle.write(json.dumps(worked, indent=1) + chr(10))
    print("%d worked campaigns, %d answers"
          % (len(worked), sum(len(w["answers"]) for w in worked)))


if __name__ == "__main__":
    main()
