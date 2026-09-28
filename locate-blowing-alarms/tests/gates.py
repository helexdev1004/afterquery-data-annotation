"""Every way of placing the alarms without doing the work, scored.

    python gates.py

Five earlier tasks of mine reached review only after every one of these had
been measured first. So this scores, in one place:

  * every reading of the logs, so no crew's habit is decoration and no
    partial account comes near the bar;
  * guessing - one place for everything;
  * whether the cable really does SETTLE which end each route was blown from,
    because if it does not that reading is a guess and the task is a hidden
    contract;
  * that nothing announces the mistake to a solver who blows every route from
    its A chamber as the procedure says: the cable runs the length of its
    route either way, so every alarm still falls on the route;
  * and that the end a route was blown from does not go with having a habit.

Nothing ships until every one of them holds.
"""

from __future__ import annotations

import itertools
import json

import ref
import blowing

YARD, SEALED = ref.places()
WITHIN_M = 2.0

WAYS = {axis: (ref.TRUE_READING[axis], other) + ref.EXTRAS.get(axis, ())
        for axis, other in ref.OTHERS.items()}


def main() -> int:
    truth = json.loads((SEALED / "truth.json").read_text())
    full = len(truth)
    faults = []

    def score(got):
        return sum(1 for k in truth if blowing.agrees(got.get(k), truth[k]))

    marks = {}
    for combo in itertools.product(*(WAYS[k] for k in WAYS)):
        marks[combo] = score(ref.run(YARD, dict(zip(WAYS, combo))))

    right = tuple(ref.TRUE_READING[k] for k in WAYS)
    print("  " + "".join("%-14s" % name for name in WAYS) + "score")
    for combo, mark in sorted(marks.items(), key=lambda kv: -kv[1])[:10]:
        flag = "   <- the whole account" if combo == right else ""
        print("  " + "".join("%-14s" % part[:13] for part in combo)
              + "%2d of %d%s" % (mark, full, flag))
    plain = tuple(ref.OTHERS[k] for k in WAYS)
    print("  ...")
    print("  the logs taken exactly as they stand: %d of %d"
          % (marks[plain], full))

    best_wrong = max(v for k, v in marks.items() if k != right)
    single = {}
    print()
    print("everything right but one:")
    for axis in WAYS:
        combo = tuple(ref.OTHERS[a] if a == axis else ref.TRUE_READING[a]
                      for a in WAYS)
        single[axis] = marks[combo]
        print("  %-12s %-14s -> %2d of %d" % (axis, ref.OTHERS[axis],
                                              marks[combo], full))
    top = tuple("from_the_far_end" if a == "blown_from" else ref.TRUE_READING[a]
                for a in WAYS)
    print("  %-12s %-14s -> %2d of %d" % ("blown_from", "from_the_far_end",
                                          marks[top], full))

    # one place for everything: the best any single figure can do
    heights = sorted(float(v.split()[0]) for v in truth.values())
    commonest = max(sum(1 for h in heights if abs(h - c) <= WITHIN_M)
                    for c in heights)
    print()
    print("one place given for every alarm gets at most %d of %d"
          % (commonest, full))

    # ---- does the cable settle which end each route was blown from? ----------
    paths = ref.build(YARD, ref.TRUE_READING)
    weakest, narrowest, turned = None, None, 0
    for name, p in sorted(paths.items()):
        good, bad = sorted(p["fits"].values(), reverse=True)
        weakest = good if weakest is None else min(weakest, good)
        narrowest = good - bad if narrowest is None \
            else min(narrowest, good - bad)
        turned += p["from_far"]
        print("  %s  %-22s raggedness in earthenware over smoothwall: from A "
              "%.2f, from the far end %.2f" % (name, ", ".join(p["habits"]) or
                                     "as the procedure says",
                                     p["fits"]["a"], p["fits"]["far"]))
    print("routes blown from the far end: %d of %d; read from the right end "
          "the cable runs at least %.1f times as raggedly in earthenware as in "
          "smoothwall, and from the wrong end at least %.1f times less than that"
          % (turned, len(paths), weakest, narrowest))
    if weakest < 2.2 or narrowest < 1.0:
        faults.append("the cable's raggedness does not settle which end a route was blown from, so "
                      "that reading is a guess")

    # ---- and the speed must say nothing, from either end ---------------------
    gap = 0.0
    for name, p in sorted(paths.items()):
        for end in ("a", "far"):
            on = {}
            for a, b in zip(p["paid"], p["paid"][1:]):
                if b - a < 300:
                    continue
                at = (a + b) // 2
                chainage = at if end == "a" else p["length"] - at
                for low, high, kind in p["ducts"]:
                    if low <= chainage < high:
                        on.setdefault(kind, []).append(b - a)
            means = [sum(v) / len(v) for v in on.values()]
            gap = max(gap, (max(means) - min(means)) / min(means))
    print("mean speed differs between kinds of duct by at most %.1f in a hundred, "
          "on any route, read from either end" % (100 * gap))
    if gap > 0.05:
        faults.append("the mean speed differs by duct, which a first look "
                      "would take for a sign, rightly or wrongly")

    walked = YARD / "blown.json"
    if walked.is_file():
        told = json.loads(walked.read_text())
        misread = [name for name, end in told.items()
                   if (end == "far") != paths[name]["from_far"]]
        print("routes the raggedness misreads: %d" % len(misread))
        if misread:
            faults.append("the raggedness misreads %s" % " ".join(misread))
    with_habit = [p["from_far"] for p in paths.values() if p["habits"]]
    if sum(with_habit) in (0, len(with_habit)):
        faults.append("the end a route was blown from goes with having a habit")

    # ---- the natural reading must show no symptom ---------------------------
    natural = ref.run(YARD, dict(ref.TRUE_READING,
                                 blown_from="from_a"))
    lost = sum(1 for k in truth if "NONE" in str(natural.get(k)))
    print("of the forty, alarms that fall off the route under the natural "
          "reading: %d" % lost)
    if lost:
        faults.append("the natural reading drops alarms off the route, which "
                      "announces itself")

    print()
    print("the whole account gets           %d of %d" % (marks[right], full))
    print("the best account that is not it  %d of %d" % (best_wrong, full))

    bar = full - 4
    if marks[right] != full:
        faults.append("the whole account does not place every alarm")
    if best_wrong >= bar:
        faults.append("an account that gets something wrong clears the bar")
    if commonest >= bar:
        faults.append("guessing clears the bar")
    if full - single["blown_from"] <= full - bar:
        faults.append("the end a route was blown from costs no more than the "
                      "allowance")

    print()
    print("bar %d of %d - %d clear of the best wrong account"
          % (bar, full, bar - best_wrong))
    if faults:
        print()
        for fault in faults:
            print("FAILED: %s" % fault)
        return 1
    print("no account that skips the work comes near it")

    try:
        (SEALED / "gates.json").write_text(json.dumps({
            "full": full, "bar": bar, "best_wrong": best_wrong,
            "as_stands": marks[plain], "commonest": commonest,
            "single": single, "turned": turned, "routes": len(paths),
            "weakest": round(weakest, 1), "narrowest": round(narrowest, 1),
            "all_top": marks[top], "readings": len(marks),
            "pace_gap": int(100 * gap) + 1,
            "ducts": sum(len(p["ducts"]) for p in paths.values()),
            "rows": sum(len(p["times"]) for p in paths.values()),
        }, indent=1), newline="\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
