"""Every reading of the training logs, against the sealed figures.

    python cluster_check.py
"""

import itertools
import json

import sweep_cost as sc

CLUSTER = sc.base()


def right(said, want):
    return said is not None and said[0] == want[0] and said[1] == want[1] \
        and abs(said[2] - want[2]) <= 0.1 + 1e-9


def main():
    sealed = json.loads((CLUSTER / "sealed.json").read_text())
    copied = json.loads((CLUSTER / "copied.json").read_text())
    total, trouble = len(sealed), []
    names = list(sc.THE_LOGS)
    scores = {}
    for combo in itertools.product(*[[sc.THE_LOGS[n], sc.THE_NOTE[n]]
                                     for n in names]):
        got, _ = sc.cost(CLUSTER, dict(zip(names, combo)))
        scores[combo] = sum(right(got.get(k), sealed[k]) for k in sealed)
    logs = tuple(sc.THE_LOGS[n] for n in names)
    note = tuple(sc.THE_NOTE[n] for n in names)
    second = max(v for k, v in scores.items() if k != logs)
    print("readings: %d" % len(scores))
    print("  %d  by the logs" % scores[logs])
    print("  %d  by the note" % scores[note])
    without = {}
    for i, n in enumerate(names):
        c = list(logs)
        c[i] = sc.THE_NOTE[n]
        without[n] = scores[tuple(c)]
        print("  %d  by the logs except %s" % (without[n], n))
    print("  %d  the best reading that is not the logs'" % second)

    _, seen = sc.cost(CLUSTER, sc.THE_LOGS)
    own = {c["log"]: run for run, c in copied.items()}
    crossed, ratios, lines = 0, [], 0
    for log_file, s in sorted(seen.items()):
        truly = own[log_file]
        crossed += truly != s["sheet"]
        ratios.append(s["jitter"] * copied[truly]["per_device"] ** 0.5)
        lines += len(sc.table(CLUSTER / "logs" / log_file))
        print("  %s  sheet says %s, really %s (found %s)  jitter %.4f with %2d "
              "sequences a device  [%s]%s"
              % (log_file, s["sheet"], truly, s["run"], s["jitter"],
                 copied[truly]["per_device"],
                 ", ".join(s["habits"]) or "plain",
                 "  COPIED UNDER THE WRONG NAME" if truly != s["sheet"] else ""))
        if s["run"] != truly:
            trouble.append("the jitter misplaces %s" % log_file)
    spread = max(ratios) / min(ratios)
    print("  jitter times the root of sequences per device holds within a "
          "factor of %.2f across the logs" % spread)
    if spread > 1.25:
        trouble.append("jitter does not follow sequences per device")

    if scores[logs] != total:
        trouble.append("the logs' reading does not get every line")
    if second >= total:
        trouble.append("a wrong reading gets every line")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (CLUSTER / "check.json").write_bytes(json.dumps(dict(
            total=total, second=second, by_note=scores[note], without=without,
            readings=len(scores), crossed=crossed, spread="%.2f" % spread,
            lines=lines), indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
