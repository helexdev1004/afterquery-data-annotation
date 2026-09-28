"""Set every reading of the counters against the sealed counts.

    python town_check.py
"""

import itertools
import json
import statistics

import serve

TOWN = serve.base()
RUNS_THAT_MAY_BE_OUT = 4
WITHIN = 0.02


def right(said, want):
    return said is not None and abs(said - want) <= WITHIN * want + 1e-9


def main():
    sealed = json.loads((TOWN / "sealed.json").read_text())
    clocks = json.loads((TOWN / "clocks.json").read_text())
    total, trouble = len(sealed), []
    names = list(serve.AS_FOUND)
    scores = {}
    for combo in itertools.product(*[[serve.AS_FOUND[n], serve.AS_NOTED[n]]
                                     for n in names]):
        got, _ = serve.volumes(TOWN, dict(zip(names, combo)))
        scores[combo] = sum(right(got.get(r), sealed[r]) for r in sealed)
    found = tuple(serve.AS_FOUND[n] for n in names)
    noted = tuple(serve.AS_NOTED[n] for n in names)
    second = max(v for k, v in scores.items() if k != found)
    print("readings: %d" % len(scores))
    print("  %2d  as found" % scores[found])
    print("  %2d  as noted" % scores[noted])
    without = {}
    for i, n in enumerate(names):
        c = list(found)
        c[i] = serve.AS_NOTED[n]
        without[n] = scores[tuple(c)]
        print("  %2d  as found except %s" % (without[n], n))
    print("  %2d  the best reading that is not as found" % second)

    got, seen = serve.volumes(TOWN, serve.AS_FOUND)
    out_clocks, sharpest, flattest = 0, 9.9, 0.0
    for site, s in sorted(seen.items()):
        true = clocks[site]["fast_min"]
        out_clocks += true != 0
        ranked = sorted(s["scores"].values(), reverse=True)
        far = [v for m, v in s["scores"].items() if abs(m - s["fast"]) >= 30]
        print("  %s  clock fast by %4d min (found %4d)  the plans sort "
              "its bunching by %.3f there, by at most %.3f half an hour or more away   [%s]"
              % (site, true, s["fast"], ranked[0], max(far),
                 ", ".join(s["habits"]) or "logged as the note says"))
        if abs(s["fast"] - true) > 1:
            trouble.append("the bunching misreads %s's clock" % site)
        sharpest = min(sharpest, ranked[0] / max(far))
    if sharpest < 1.4:
        trouble.append("the bunching does not settle a clock")

    # the mean must say nothing: flow just after a change against just before
    booked = serve.bookings(TOWN)
    lift = []
    for site in seen:
        log = seen[site]["log"]
        for when, _, _ in booked[site]:
            when += clocks[site]["fast_min"] * 60
            before = log.between(when - 1500, when, 0)
            after = log.between(when, when + 1500, 0)
            if before > 50 and after > 50:
                lift.append(after / before)
    gap = abs(statistics.median(lift) - 1)
    print("  flow in the 25 min after a change is %.3f of the flow before, in "
          "the middle of %d changes" % (statistics.median(lift), len(lift)))
    if gap > 0.03:
        trouble.append("the flow itself steps at a change")

    # pln1: the day's shape had a seam at true midnight, and it showed in a
    # counter's own day at midnight plus whatever its clock was out by
    seam = 0.0
    for site in seen:
        log = seen[site]["log"]
        bins = [[] for _ in range(144)]
        back = clocks[site]["fast_min"] * 60
        for t, c in zip(log.times, log.counts):
            bins[int((t - back) % 86400 // 600)].append(c)
        shape = [statistics.fmean(b) for b in bins]
        steps = [abs(shape[i] - shape[i - 1]) for i in range(144)]
        seam = max(seam, steps[0] / statistics.median(steps))
    print("  across true midnight a site's day steps by at most %.1f times "
          "its usual ten-minute step" % seam)
    if seam > 3.5:
        trouble.append("a site's day has a seam at midnight")

    if scores[found] != total:
        trouble.append("as found does not count every run")
    if second > total - RUNS_THAT_MAY_BE_OUT - 1:
        trouble.append("a wrong reading is within the allowance")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (TOWN / "check.json").write_bytes(json.dumps(dict(
            total=total, may_be_out=RUNS_THAT_MAY_BE_OUT, second=second,
            as_noted=scores[noted], without=without, readings=len(scores),
            sites=len(seen), out_clocks=out_clocks,
            sharpest="%.1f" % sharpest,
            changes=sum(len(b) for b in booked.values())), indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
