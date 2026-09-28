"""Every reading of the terminal's log, against the sealed answers.

    python terminal_check.py
"""

import itertools
import json
import statistics

import answer_customer as ac

TERMINAL = ac.base()
LINES_THAT_MAY_BE_WRONG = 4
WITHIN_L = 25


def right(said, want):
    return said is not None and said[0] == want[0] \
        and abs(said[1] - want[1]) <= WITHIN_L


def main():
    sealed = json.loads((TERMINAL / "sealed.json").read_text())
    fitted = json.loads((TERMINAL / "fitted.json").read_text())
    total, trouble = len(sealed), []
    names = list(ac.GO_BY_THE_LOG)
    scores = {}
    for combo in itertools.product(*[[ac.GO_BY_THE_LOG[n],
                                      ac.GO_BY_THE_NOTE[n]] for n in names]):
        got, _ = ac.answer(TERMINAL, dict(zip(names, combo)))
        scores[combo] = sum(right(got.get(k), sealed[k]) for k in sealed)
    by_log = tuple(ac.GO_BY_THE_LOG[n] for n in names)
    by_note = tuple(ac.GO_BY_THE_NOTE[n] for n in names)
    second = max(v for k, v in scores.items() if k != by_log)
    print("readings: %d" % len(scores))
    print("  %2d  going by the log" % scores[by_log])
    print("  %2d  going by the note" % scores[by_note])
    without = {}
    for i, n in enumerate(names):
        c = list(by_log)
        c[i] = ac.GO_BY_THE_NOTE[n]
        without[n] = scores[tuple(c)]
        print("  %2d  going by the log except %s" % (without[n], n))
    print("  %2d  the best reading that is not the log's" % second)

    got, seen = ac.answer(TERMINAL, ac.GO_BY_THE_LOG)
    changed, least = 0, 9.9
    rows = ac.table(TERMINAL / "tas_log.csv")
    rate_by_batch = 0.0
    for arm, s in sorted(seen.items()):
        truly = fitted[arm]["k_fitted"]
        changed += truly != fitted[arm]["k_on_file"]
        ranked = sorted(s["scores"].values(), reverse=True)
        least = min(least, ranked[0] / ranked[1])
        print("  %s  K on file %.2f, fitted %.2f (found %.2f)  tickets sort "
              "the meter's unsteadiness %.1f times better there than under "
              "the next K   [%s]"
              % (arm, fitted[arm]["k_on_file"], truly, s["k"],
                 ranked[0] / ranked[1], ", ".join(s["habits"]) or "as the note says"))
        if abs(s["k"] - truly) > 1e-9:
            trouble.append("the meter misreads %s" % arm)
    if least < 1.3:
        trouble.append("the unsteadiness does not settle a meter")

    # the loading rate must not change with the batch
    slips = ac.tickets(TERMINAL)
    arms = {r["arm"]: r for r in ac.table(TERMINAL / "arms.csv")}
    for arm, s in seen.items():
        log = ac.ArmLog(rows, arm, ac.GO_BY_THE_LOG)
        edges, _ = slips[arms[arm]["header"]]
        ratio = fitted[arm]["k_on_file"] / fitted[arm]["k_fitted"]
        d = [b - a for a, b in zip(log.total, log.total[1:])]
        full = 0.8 * statistics.median(v for v in d if v > 0)
        by = {}
        for i, v in enumerate(d):
            if v > full:
                through = (log.total[i] - log.total[0]) * ratio
                by.setdefault(sum(e <= through for e in edges), []).append(v)
        means = [statistics.fmean(v) for v in by.values() if len(v) > 300]
        rate_by_batch = max(rate_by_batch, (max(means) - min(means))
                            / statistics.fmean(means))
    print("  an arm's loading rate differs between batches by at most %.2f in "
          "a hundred" % (100 * rate_by_batch))
    if rate_by_batch > 0.01:
        trouble.append("the loading rate shows the batch")

    if scores[by_log] != total:
        trouble.append("going by the log does not answer every load")
    if second > total - LINES_THAT_MAY_BE_WRONG - 1:
        trouble.append("a wrong reading is within the allowance")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (TERMINAL / "check.json").write_bytes(json.dumps(dict(
            total=total, may_be_wrong=LINES_THAT_MAY_BE_WRONG, second=second,
            by_note=scores[by_note], without=without, readings=len(scores),
            arms=len(seen), changed=changed, least="%.1f" % least,
            rate_gap="%.2f" % (100 * rate_by_batch), lines=len(rows)),
            indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
