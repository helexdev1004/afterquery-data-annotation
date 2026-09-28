"""Every reading of the logger files, against the sealed volumes.

    python catchment_check.py
"""

import itertools
import json
import statistics

import water_balance as wb

CATCHMENT = wb.base()
LINES_THAT_MAY_BE_WRONG = 2


def right(said, want):
    return said is not None and abs(said - want) <= 0.005 * want + 1e-9


def main():
    sealed = json.loads((CATCHMENT / "sealed.json").read_text())
    housings = json.loads((CATCHMENT / "housings.json").read_text())
    total, trouble = len(sealed), []
    names = list(wb.THE_FILES)
    scores = {}
    for combo in itertools.product(*[[wb.THE_FILES[n], wb.THE_NOTE[n]]
                                     for n in names]):
        got, _ = wb.runoff(CATCHMENT, dict(zip(names, combo)))
        scores[combo] = sum(right(got.get(k), sealed[k]) for k in sealed)
    files = tuple(wb.THE_FILES[n] for n in names)
    note = tuple(wb.THE_NOTE[n] for n in names)
    second = max(v for k, v in scores.items() if k != files)
    print("readings: %d" % len(scores))
    print("  %2d  by the files" % scores[files])
    print("  %2d  by the note" % scores[note])
    without = {}
    for i, n in enumerate(names):
        c = list(files)
        c[i] = wb.THE_NOTE[n]
        without[n] = scores[tuple(c)]
        print("  %2d  by the files except %s" % (without[n], n))
    print("  %2d  the best reading that is not the files'" % second)

    _, seen = wb.runoff(CATCHMENT, wb.THE_FILES)
    came = {h["file"]: s for s, h in housings.items()}
    crossed, still, surging, middles = 0, [], [], {}
    for name, s in sorted(seen.items()):
        truly = came[name]
        crossed += truly != s["sheet"]
        (still if housings[truly]["control"] == "weir" else surging).append(
            s["restless"])
        series, _ = wb.read_log(CATCHMENT / "stage_logs" / (name + ".csv"),
                                wb.THE_FILES)
        middles[name] = statistics.median(abs(v) for _, v in series)
        print("  %s  sheet says %s, really %s (found %s)  restless %.4f m  "
              "middle stage %.3f m  [%s]%s"
              % (name, s["sheet"], truly, s["from"], s["restless"],
                 middles[name], ", ".join(s["habits"]) or "plain",
                 "  CROSSED" if truly != s["sheet"] else ""))
        if s["from"] != truly:
            trouble.append("the water misplaces %s" % name)
    gap = min(surging) / max(still)
    print("  the stillest rated section is %.1f times as restless as the most "
          "restless weir" % gap)
    if gap < 3:
        trouble.append("restlessness does not settle a file")

    if scores[files] != total:
        trouble.append("the files' reading does not get every line")
    if second > total - LINES_THAT_MAY_BE_WRONG - 1:
        trouble.append("a wrong reading is within the allowance")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (CATCHMENT / "check.json").write_bytes(json.dumps(dict(
            total=total, may_be_wrong=LINES_THAT_MAY_BE_WRONG, second=second,
            by_note=scores[note], without=without, readings=len(scores),
            crossed=crossed, gap="%.1f" % gap,
            readings_logged=sum(len(wb.table(CATCHMENT / "stage_logs"
                                             / (n + ".csv"))) for n in seen)),
            indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
