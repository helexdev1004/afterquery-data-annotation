"""Every reading of the logger's records, against the sealed certificates.

    python furnace_check.py
"""

import itertools
import json

import certify

FURNACE = certify.base()
LINES_THAT_MAY_BE_WRONG = 1


def right(said, want):
    return said is not None and abs(said[0] - want[0]) <= 0.5 + 1e-9 \
        and abs(said[1] - want[1]) <= 0.3 + 1e-9


def main():
    sealed = json.loads((FURNACE / "sealed.json").read_text())
    wired = json.loads((FURNACE / "terminals.json").read_text())
    total, trouble = len(sealed), []
    names = list(certify.THE_RECORDS)
    scores = {}
    for combo in itertools.product(*[[certify.THE_RECORDS[n],
                                      certify.THE_NOTE[n]] for n in names]):
        got, _ = certify.soaks(FURNACE, dict(zip(names, combo)))
        scores[combo] = sum(right(got.get(k), sealed[k]) for k in sealed)
    records = tuple(certify.THE_RECORDS[n] for n in names)
    note = tuple(certify.THE_NOTE[n] for n in names)
    second = max(v for k, v in scores.items() if k != records)
    print("readings: %d" % len(scores))
    print("  %2d  by the records" % scores[records])
    print("  %2d  by the note" % scores[note])
    without = {}
    for i, n in enumerate(names):
        c = list(records)
        c[i] = certify.THE_NOTE[n]
        without[n] = scores[tuple(c)]
        print("  %2d  by the records except %s" % (without[n], n))
    print("  %2d  the best reading that is not the records'" % second)

    _, seen = certify.soaks(FURNACE, certify.THE_RECORDS)
    on = {(p[0], w["channel"]): p for p, w in wired.items()}
    crossed, couples, platinum = 0, [], []
    for key, s in sorted(seen.items()):
        load, ch = key.split("/")
        truly = on[(load, ch)]
        crossed += truly != s["scheduled"]
        (couples if wired[truly]["kind"] == "type K" else platinum).append(
            s["jitter"])
        print("  %s  scheduled %s, really %s (found %s)  jitter %.3f degC  [%s]%s"
              % (key, s["scheduled"], truly, s["carries"], s["jitter"],
                 ", ".join(s["habits"]) or "plain",
                 "  CROSSED" if truly != s["scheduled"] else ""))
        if s["carries"] != truly:
            trouble.append("the jitter misplaces %s" % key)
    gap = min(couples) / max(platinum)
    print("  the steadiest thermocouple jitters %.1f times as much as the "
          "least steady resistance probe" % gap)
    if gap < 3:
        trouble.append("jitter does not settle a channel")

    if scores[records] != total:
        trouble.append("the records' reading does not get every line")
    if second > total - LINES_THAT_MAY_BE_WRONG - 1:
        trouble.append("a wrong reading is within the allowance")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (FURNACE / "check.json").write_bytes(json.dumps(dict(
            total=total, may_be_wrong=LINES_THAT_MAY_BE_WRONG, second=second,
            by_note=scores[note], without=without, readings=len(scores),
            crossed=crossed, gap="%.1f" % gap,
            lines=sum(len(certify.table(FURNACE / ("load_%s.csv" % l)))
                      for l in "AB")), indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
