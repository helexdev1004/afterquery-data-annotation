"""Every reading of the power monitor's log, against the sealed plan.

    python house_check.py
"""

import itertools
import json
import statistics
from datetime import date

import service_plan as sp

HOUSE = sp.base()


def right(said, want):
    return said is not None and abs(said[0] - want[0]) <= 0.2 + 1e-9 \
        and said[1] == want[1] and abs((date.fromisoformat(said[2])
                                        - date.fromisoformat(want[2])).days) <= 1


def main():
    sealed = json.loads((HOUSE / "sealed.json").read_text())
    terminals = json.loads((HOUSE / "terminals.json").read_text())
    total, trouble = len(sealed), []
    names = list(sp.THE_LOG)
    scores = {}
    for combo in itertools.product(*[[sp.THE_LOG[n], sp.THE_NOTE[n]]
                                     for n in names]):
        got, _ = sp.due(HOUSE, dict(zip(names, combo)))
        scores[combo] = sum(right(got.get(k), sealed[k]) for k in sealed)
    log = tuple(sp.THE_LOG[n] for n in names)
    note = tuple(sp.THE_NOTE[n] for n in names)
    second = max(v for k, v in scores.items() if k != log)
    print("readings: %d" % len(scores))
    print("  %d  by the log" % scores[log])
    print("  %d  by the note" % scores[note])
    without = {}
    for i, n in enumerate(names):
        c = list(log)
        c[i] = sp.THE_NOTE[n]
        without[n] = scores[tuple(c)]
        print("  %d  by the log except %s" % (without[n], n))
    print("  %d  the best reading that is not the log's" % second)

    got, seen = sp.due(HOUSE, sp.THE_LOG)
    on = {t["channel"]: k for k, t in terminals.items()}
    crossed, smooth, pulsing = 0, [], []
    for ch, s in sorted(seen.items()):
        truly = on[ch]
        crossed += truly != s["scheduled"]
        (pulsing if terminals[truly]["kind"] == "piston" else smooth).append(
            s["ripple"])
        print("  %s  scheduled %s, really %s (found %s)  ripple %.4f of its "
              "running level   [%s]%s"
              % (ch, s["scheduled"], truly, s["serves"], s["ripple"],
                 ", ".join(s["habits"]) or "plain",
                 "   CROSSED" if truly != s["scheduled"] else ""))
        if s["serves"] != truly:
            trouble.append("the ripple misplaces %s" % ch)
    gap = min(pulsing) / max(smooth)
    print("  the smoothest piston channel ripples %.1f times the roughest "
          "screw channel" % gap)
    if gap < 3:
        trouble.append("the ripple does not settle a channel")

    # level and pattern of running must not tell a kind: by true machine
    rows = sp.table(HOUSE / "current_log.csv")
    kinds = {"screw": [], "piston": []}
    for k, t in terminals.items():
        kinds[t["kind"]].append(sealed[k][1] / max(sealed[k][0], 1))
    print("  starts per running hour: screws %.2f to %.2f, pistons %.2f to %.2f"
          % (min(kinds["screw"]), max(kinds["screw"]), min(kinds["piston"]),
             max(kinds["piston"])))
    if max(kinds["screw"]) < min(kinds["piston"]) or \
            max(kinds["piston"]) < min(kinds["screw"]):
        trouble.append("the pattern of running tells the kinds apart")

    if scores[log] != total:
        trouble.append("the log's reading does not get every line")
    if second >= total:
        trouble.append("a wrong reading gets every line")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (HOUSE / "check.json").write_bytes(json.dumps(dict(
            total=total, second=second, by_note=scores[note], without=without,
            readings=len(scores), crossed=crossed, gap="%.1f" % gap,
            lines=len(rows)), indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
