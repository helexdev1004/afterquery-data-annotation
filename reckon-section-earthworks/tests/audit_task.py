"""Measure, against the sealed figures, every way round the work.

    python audit_task.py

  ways      every way of reading the five field books, scored
  constant  one row given for every section
  decided   does the ground's roughness really say which hand a book was kept in
  quietly   does the office note's own reading fail without any sign
  apart     is a surveyor's hand independent of his units
"""

import itertools
import json

import take_off
import template

YARD = take_off.where()
ROWS_ALLOWED_WRONG = 4


def marks(said, sealed):
    return sum(1 for k in sealed if template.agree(said.get(k, ()), sealed[k]))


def main():
    sealed = json.loads((YARD / "sealed.json").read_text())
    total, snags = len(sealed), []

    names = list(take_off.PROPERLY)
    choices = [[take_off.PROPERLY[n], take_off.AS_BOOKED[n]]
               + (list(take_off.OTHER_HANDS) if n == "hand" else [])
               for n in names]
    table = {}
    for combo in itertools.product(*choices):
        table[combo] = marks(take_off.figures(YARD, dict(zip(names, combo))),
                             sealed)
    proper = tuple(take_off.PROPERLY[n] for n in names)
    booked = tuple(take_off.AS_BOOKED[n] for n in names)
    second = max(v for k, v in table.items() if k != proper)
    print("ways: %d" % len(table))
    for combo, got in sorted(table.items(), key=lambda kv: -kv[1])[:6]:
        print("  %2d  %s%s" % (got, " | ".join(combo),
                               "   <- read properly" if combo == proper else ""))
    print("  %2d  all as booked" % table[booked])
    lacking = {}
    for i, n in enumerate(names):
        combo = list(proper)
        combo[i] = take_off.AS_BOOKED[n]
        lacking[n] = table[tuple(combo)]
        print("  %2d  proper except %s" % (lacking[n], n))
    every_left = tuple("left_positive" if n == "hand" else take_off.PROPERLY[n]
                       for n in names)
    print("  %2d  every book taken as positive to the left" % table[every_left])
    if table[proper] != total:
        snags.append("the proper reading does not get every section")
    if second >= total - ROWS_ALLOWED_WRONG:
        snags.append("a wrong reading is within the allowance")

    rows = list(sealed.values())
    constant = max(sum(1 for r in rows if template.agree(c, r)) for c in rows)
    print("constant\n  %2d  the best single row" % constant)

    job = take_off.read_job(YARD, take_off.PROPERLY)
    truth = json.loads((YARD / "hands.json").read_text())
    print("decided")
    weakest, strongest_wrong, lefts = None, 0.0, 0
    for name, s in sorted(job.items()):
        right = truth[name]
        wrong = [h for h in s["contrast"] if h != right][0]
        lefts += right == "left_positive"
        print("  %s  ploughed over pasture, staff position to staff position: "
              "%.1f in his true hand, %.1f in the other  (%s)"
              % (name, s["contrast"][right], s["contrast"][wrong],
                 ", ".join(s["book"].units) or "units as the note says"))
        weakest = s["contrast"][right] if weakest is None \
            else min(weakest, s["contrast"][right])
        strongest_wrong = max(strongest_wrong, s["contrast"][wrong])
        if s["hand"] != right:
            snags.append("the ground misreads %s" % name)
    if weakest < 2.5 or strongest_wrong > 1.6:
        snags.append("the ground does not decide a surveyor's hand")

    natural = take_off.figures(YARD, dict(take_off.PROPERLY,
                                          hand="right_positive"))
    print("quietly\n  %2d  of the wanted sections get figures under the note's "
          "own reading" % len(natural))
    if len(natural) != total:
        snags.append("the note's own reading loses sections")

    odd = {truth[name] for name, s in job.items() if s["book"].units}
    if len(odd) < 2:
        snags.append("a surveyor's hand goes with his units")

    print()
    if snags:
        for snag in snags:
            print("SNAG: %s" % snag)
        return 1
    print("bar %d of %d; best wrong reading %d" % (total - ROWS_ALLOWED_WRONG,
                                                   total, second))
    (YARD / "audit.json").write_text(json.dumps(dict(
        total=total, allowed=ROWS_ALLOWED_WRONG, second=second,
        as_booked=table[booked], constant=constant, lacking=lacking,
        every_left=table[every_left], ways=len(table), lefts=lefts,
        schemes=len(job), weakest=round(weakest, 1),
        strongest_wrong=round(strongest_wrong, 1),
        sections=sum(len(s["book"].sections) for s in job.values()),
        points=sum(len(p) for s in job.values()
                   for p in s["book"].sections.values())), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
