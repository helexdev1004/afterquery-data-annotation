"""Measure every shortcut before the bundle ships.

    python proof.py

  readings   every way of reading the five logs, scored against the sealed table
  guessing   the best a constant answer can do
  settled    does the cycle's waver really put each controller's clock right
  means      does any plain figure - mean cycle, plain spread - say the same thing
  silent     does the procedure's own reading go wrong without a sign
  untied     is a slow clock independent of a controller's way with a time
"""

import itertools
import json
import statistics

import dryrules
import reckon

YARD = reckon.records_dir()
MAY_BE_WRONG = 4


def score(table, sealed):
    return sum(1 for h in sealed if dryrules.same(table.get(h), sealed[h]))


def main():
    sealed = json.loads((YARD / "sealed.json").read_text())
    total, faults = len(sealed), []

    # ---- readings ------------------------------------------------------------
    axes = list(reckon.AS_IT_IS)
    options = [[reckon.AS_IT_IS[a], reckon.AS_WRITTEN[a]]
               + (list(reckon.OTHER_CLOCKS) if a == "clock" else [])
               for a in axes]
    marks = {combo: score(reckon.reckon(YARD, dict(zip(axes, combo))), sealed)
             for combo in itertools.product(*options)}
    right = tuple(reckon.AS_IT_IS[a] for a in axes)
    written = tuple(reckon.AS_WRITTEN[a] for a in axes)
    next_best = max(v for k, v in marks.items() if k != right)
    print("readings (%d of them)" % len(marks))
    for combo, mark in sorted(marks.items(), key=lambda kv: -kv[1])[:7]:
        print("   %2d  %s%s" % (mark, ", ".join(combo),
                                "   <- as it is" if combo == right else ""))
    print("   %2d  everything as written" % marks[written])
    short = {}
    for n, axis in enumerate(axes):
        combo = list(right)
        combo[n] = reckon.AS_WRITTEN[axis]
        short[axis] = marks[tuple(combo)]
        print("   %2d  all but %s" % (short[axis], axis))
    for other in reckon.OTHER_CLOCKS:
        combo = tuple(other if a == "clock" else reckon.AS_IT_IS[a]
                      for a in axes)
        short[other] = marks[combo]
        print("   %2d  every controller taken as %s" % (marks[combo], other))
    if marks[right] != total:
        faults.append("the right reading does not get every housing")
    if next_best >= total - MAY_BE_WRONG:
        faults.append("a wrong reading comes within the allowance")

    # ---- guessing ------------------------------------------------------------
    hours = sorted(v["hours"] for v in sealed.values())
    guess = max(sum(1 for v in sealed.values()
                    if v["resin"] == resin and abs(v["hours"] - h) <= 0.1)
                for h in hours for resin in dryrules.RESINS)
    print("guessing\n   %2d  the best single answer" % guess)

    # ---- settled ---------------------------------------------------------------
    shop = reckon.read_shop(YARD, reckon.AS_IT_IS)
    told = json.loads((YARD / "clocks.json").read_text())
    print("settled")
    least_right, most_wrong, behind = None, 0.0, 0
    for machine, entry in sorted(shop.items()):
        truth = told[machine]
        behind += truth == "hour_behind"
        wrong = max(v for k, v in entry["steps"].items() if k != truth)
        least_right = entry["steps"][truth] if least_right is None \
            else min(least_right, entry["steps"][truth])
        most_wrong = max(most_wrong, wrong)
        print("   %s  the waver steps at the refills by %.2f of its usual size "
              "on the true clock (%s), at most %.2f on another"
              % (machine, entry["steps"][truth], truth.replace("_", " "),
                 wrong))
        if entry["clock"] != truth:
            faults.append("the waver misreads %s" % machine)
    if least_right < 0.45 or most_wrong > 0.2:
        faults.append("the waver does not settle a controller's clock")

    # ---- means -----------------------------------------------------------------
    print("means")
    worst_mean, worst_spread = 0.0, 0.0
    for machine, entry in sorted(shop.items()):
        times = sorted(entry["times"].values())
        cycles = [(b, b - a) for a, b in zip(times, times[1:])]
        usual = statistics.median(c for _, c in cycles)
        for lag in (0.0, 3600.0):
            by_resin = {}
            for when, cycle in cycles:
                if cycle < 1.5 * usual:
                    found = entry["dryer"].drying(when + lag)
                    if found:
                        by_resin.setdefault(found[1], []).append(cycle)
            means = [statistics.fmean(v) for v in by_resin.values()]
            spreads = [statistics.pstdev(v) for v in by_resin.values()]
            worst_mean = max(worst_mean, (max(means) - min(means)) / usual)
            worst_spread = max(worst_spread, max(spreads) / min(spreads) - 1)
    print("   mean cycle differs between resins by at most %.2f in a hundred"
          % (100 * worst_mean))
    print("   plain spread of the cycle differs between resins by at most %.0f "
          "in a hundred" % (100 * worst_spread))
    if worst_mean > 0.01:
        faults.append("the mean cycle differs by resin")

    # ---- silent ----------------------------------------------------------------
    natural = reckon.reckon(YARD, dict(reckon.AS_IT_IS, clock="site_time"))
    print("silent\n   %2d  housings get a drying time under the procedure's own "
          "reading, the shortest %.2f h" % (
              len(natural), min(v["hours"] for v in natural.values())))
    if len(natural) != total:
        faults.append("the procedure's own reading drops housings")

    ways = [(entry["way"] is not None, told[m] == "hour_behind")
            for m, entry in shop.items()]
    if len({slow for odd, slow in ways if odd}) < 2:
        faults.append("a slow clock goes with having an odd way with a time")

    print()
    if faults:
        for fault in faults:
            print("FAULT: %s" % fault)
        return 1
    print("bar %d of %d, next best reading %d" % (total - MAY_BE_WRONG, total,
                                                 next_best))
    (YARD / "proof.json").write_text(json.dumps(dict(
        total=total, may_be_wrong=MAY_BE_WRONG, next_best=next_best,
        as_written=marks[written], guess=guess, short=short,
        readings=len(marks), behind=behind, machines=len(shop),
        least_right=round(least_right, 1), most_wrong=round(most_wrong, 1),
        mean_gap="%.2f" % (100 * worst_mean),
        spread_gap=int(100 * worst_spread) + 1,
        shots=sum(len(e["times"]) for e in shop.values()),
        refills=sum(len(e["dryer"].refills) for e in shop.values())),
        indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
