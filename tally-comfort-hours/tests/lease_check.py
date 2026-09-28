"""Weigh every reading of the trends against the sealed hours.

    python lease_check.py
"""

import itertools
import json
import statistics

import rebate

MONTH = rebate.base()
LINES_THAT_MAY_BE_OUT = 4
WITHIN_H = 0.25


def good(said, want):
    return said is not None and abs(said - want) <= WITHIN_H + 1e-9


def main():
    sealed = json.loads((MONTH / "sealed.json").read_text())
    wiring = json.loads((MONTH / "wiring.json").read_text())
    total, trouble = len(sealed), []
    names = list(rebate.THE_TRENDS)
    scores = {}
    for combo in itertools.product(*[[rebate.THE_TRENDS[n],
                                      rebate.THE_PAPERS[n]] for n in names]):
        got, _ = rebate.hours_out(MONTH, dict(zip(names, combo)))
        scores[combo] = sum(good(got.get(k), sealed[k]) for k in sealed)
    trends = tuple(rebate.THE_TRENDS[n] for n in names)
    papers = tuple(rebate.THE_PAPERS[n] for n in names)
    second = max(v for k, v in scores.items() if k != trends)
    print("readings: %d" % len(scores))
    print("  %2d  the trends' word" % scores[trends])
    print("  %2d  the papers' word" % scores[papers])
    without = {}
    for i, n in enumerate(names):
        c = list(trends)
        c[i] = rebate.THE_PAPERS[n]
        without[n] = scores[tuple(c)]
        print("  %2d  the trends' word except %s" % (without[n], n))
    print("  %2d  the best reading that is not the trends'" % second)
    print("  %2d  lines whose sealed hours are nought" % sum(
        1 for v in sealed.values() if v == 0))

    got, seen = rebate.hours_out(MONTH, rebate.THE_TRENDS)
    crossed, least, most_other, margin = 0, 9.9, 0.0, 9.9
    for trend, s in sorted(seen.items()):
        true = wiring["zone_of"][trend]
        crossed += true != s["listed"]
        least, most_other = min(least, s["fit"]), max(most_other, s["next_best"])
        margin = min(margin, s["fit"] - s["next_best"])
        print("  %s  listed %s, really %s (found %s)  restlessness inside the "
              "lease hours %.2f there, at most %.2f under any other zone's   "
              "[%s]" % (trend, s["listed"], true, s["zone"], s["fit"],
                        s["next_best"],
                        ", ".join(s["habits"]) or "trended as the note says"))
        if s["zone"] != true:
            trouble.append("the restlessness misplaces %s" % trend)
    if margin < 0.1:
        trouble.append("the restlessness does not settle a zone")

    # what a table would show: mean and plain spread, lease hours against not
    kept = rebate.lease_hours(MONTH)
    mean_gap, spread_gap = 0.0, 0.0
    every, _ = rebate.read_trends(MONTH, rebate.THE_TRENDS)
    for trend in seen:
        series = every[trend]
        hours = kept[wiring["zone_of"][trend]]
        inside = [v for when, v in series if rebate.is_kept(hours, when)]
        outside = [v for when, v in series if not rebate.is_kept(hours, when)]
        mean_gap = max(mean_gap, abs(statistics.fmean(inside)
                                     - statistics.fmean(outside)))
        spread_gap = max(spread_gap, abs(statistics.pstdev(inside)
                                         / statistics.pstdev(outside) - 1))
    print("  a zone's mean differs by at most %.2f degC between its lease "
          "hours and the rest, its plain spread by at most %.0f in a hundred"
          % (mean_gap, 100 * spread_gap))

    if scores[trends] != total:
        trouble.append("the trends' word does not get every line")
    if second > total - LINES_THAT_MAY_BE_OUT - 1:
        trouble.append("a wrong reading is within the allowance")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (MONTH / "check.json").write_bytes(json.dumps(dict(
            total=total, may_be_out=LINES_THAT_MAY_BE_OUT, second=second,
            papers=scores[papers], without=without, readings=len(scores),
            zones=len(seen), crossed=crossed, least="%.2f" % least,
            most_other="%.2f" % most_other, margin="%.2f" % margin, mean_gap="%.2f" % mean_gap,
            spread_gap="%.0f" % (100 * spread_gap)), indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
