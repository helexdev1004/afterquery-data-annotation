"""Every reading of the collector's records, against the sealed figures.

    python review_check.py
"""

import itertools
import json
import statistics

import budgets

FORTNIGHT = budgets.base()
LINES_THAT_MAY_BE_WRONG = 1


def right(said, want):
    return said is not None and abs(said[0] - want[0]) <= 0.002 + 1e-9 \
        and abs(said[1] - want[1]) <= 0.5 + 1e-9


def main():
    sealed = json.loads((FORTNIGHT / "sealed.json").read_text())
    truth = json.loads((FORTNIGHT / "relabel_truth.json").read_text())
    total, trouble = len(sealed), []
    names = list(budgets.THE_RECORDS)
    scores = {}
    for combo in itertools.product(*[[budgets.THE_RECORDS[n],
                                      budgets.THE_NOTE[n]] for n in names]):
        got, _ = budgets.budgets(FORTNIGHT, dict(zip(names, combo)))
        scores[combo] = sum(right(got.get(k), sealed[k]) for k in sealed)
    records = tuple(budgets.THE_RECORDS[n] for n in names)
    note = tuple(budgets.THE_NOTE[n] for n in names)
    second = max(v for k, v in scores.items() if k != records)
    print("readings: %d" % len(scores))
    print("  %2d  by the records" % scores[records])
    print("  %2d  by the note" % scores[note])
    without = {}
    for i, n in enumerate(names):
        c = list(records)
        c[i] = budgets.THE_NOTE[n]
        without[n] = scores[tuple(c)]
        print("  %2d  by the records except %s" % (without[n], n))
    print("  %2d  the best reading that is not the records'" % second)

    _, seen = budgets.budgets(FORTNIGHT, budgets.THE_RECORDS)
    on = {t["stream"]: s for s, t in truth.items()}
    crossed, collected, native = 0, [], []
    streams, _ = budgets.read_streams(FORTNIGHT, budgets.THE_RECORDS)
    for stream, s in sorted(seen.items()):
        truly = on[stream]
        crossed += truly != s["ruled"]
        (collected if truth[truly]["runtime"] == "jvm" else native).append(
            s["memory"])
        lat = [l for _, _, l in streams[stream]]
        print("  %s  ruled %-13s really %-13s (found %-13s)  memory %.3f  "
              "middle latency %5.1f  requests %d  [%s]%s"
              % (stream, s["ruled"], truly, s["carries"], s["memory"],
                 statistics.median(lat), len(lat),
                 ", ".join(s["habits"]) or "plain",
                 "  CROSSED" if truly != s["ruled"] else ""))
        if s["carries"] != truly:
            trouble.append("the runtime misplaces %s" % stream)
    print("  latency memory: collected runtimes at least %.3f, native at most "
          "%.3f" % (min(collected), max(native)))
    if min(collected) < 0.12 or max(native) > 0.03:
        trouble.append("the latency memory does not settle a stream")

    if scores[records] != total:
        trouble.append("the records' reading does not get every line")
    if second > total - LINES_THAT_MAY_BE_WRONG - 1:
        trouble.append("a wrong reading is within the allowance")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (FORTNIGHT / "check.json").write_bytes(json.dumps(dict(
            total=total, may_be_wrong=LINES_THAT_MAY_BE_WRONG, second=second,
            by_note=scores[note], without=without, readings=len(scores),
            crossed=crossed, least_collected="%.2f" % min(collected),
            most_native="%.2f" % max(native),
            requests=sum(len(v) for v in streams.values())), indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
