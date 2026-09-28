"""Every way of getting the altitudes without doing the work, scored.

    python gates.py

Four earlier tasks of mine reached review only after every one of these had
been measured first. So this scores, in one place:

  * every reading of the logs, so no fieldworker's habit is decoration and no
    partial account comes near the bar;
  * guessing - one altitude for everything;
  * whether the walking really does SETTLE which end each walk began at,
    because if it does not that reading is a guess and the task is a hidden
    contract;
  * that nothing announces the mistake to a solver who starts every walk at
    the foot as the protocol says: the wheel rolls the length of its path
    either way, so every reading still falls on the path;
  * and that the end a walk began at does not go with having a habit.

Nothing ships until every one of them holds.
"""

from __future__ import annotations

import itertools
import json

import ref
import survey

YARD, SEALED = ref.places()
HALF_METRE = 0.5

WAYS = {axis: (ref.TRUE_READING[axis], other) + ref.EXTRAS.get(axis, ())
        for axis, other in ref.OTHERS.items()}


def main() -> int:
    truth = json.loads((SEALED / "truth.json").read_text())
    full = len(truth)
    faults = []

    def score(got):
        return sum(1 for k in truth if survey.agrees(got.get(k), truth[k]))

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
    top = tuple("from_the_top" if a == "walked_from" else ref.TRUE_READING[a]
                for a in WAYS)
    print("  %-12s %-14s -> %2d of %d" % ("walked_from", "from_the_top",
                                          marks[top], full))

    # one altitude for everything: the best any single figure can do
    heights = sorted(float(v.split()[0]) for v in truth.values())
    commonest = max(sum(1 for h in heights if abs(h - c) <= HALF_METRE)
                    for c in heights)
    print()
    print("one altitude given for every reading gets at most %d of %d"
          % (commonest, full))

    # ---- does the walking settle which end each walk began at? --------------
    paths = ref.build(YARD, ref.TRUE_READING)
    weakest, narrowest, turned = None, None, 0
    for name, p in sorted(paths.items()):
        good, bad = sorted(p["fits"].values(), reverse=True)
        weakest = good if weakest is None else min(weakest, good)
        narrowest = good - bad if narrowest is None \
            else min(narrowest, good - bad)
        turned += p["from_top"]
        print("  %s  %-22s chatter on ballast over chatter on tarmac: from the "
              "foot %.2f, from the top %.2f" % (name, ", ".join(p["habits"]) or
                                     "as the protocol says",
                                     p["fits"]["foot"], p["fits"]["top"]))
    print("walks made from the top: %d of %d; read from the right end the "
          "wheel chatters at least %.1f times as much on ballast as on tarmac, "
          "and from the wrong end at least %.1f times less than that"
          % (turned, len(paths), weakest, narrowest))
    if weakest < 2.2 or narrowest < 1.0:
        faults.append("a wheel's chatter does not settle which end it began at, so "
                      "that reading is a guess")

    # ---- and the pace must say nothing, from either end ----------------------
    gap = 0.0
    for name, p in sorted(paths.items()):
        for end in ("foot", "top"):
            on = {}
            for a, b in zip(p["rolled"], p["rolled"][1:]):
                if b - a < 3000:
                    continue
                at = (a + b) // 2
                chainage = at if end == "foot" else p["length"] - at
                for low, high, kind in p["surfaces"]:
                    if low <= chainage < high:
                        on.setdefault(kind, []).append(b - a)
            means = [sum(v) / len(v) for v in on.values()]
            gap = max(gap, (max(means) - min(means)) / min(means))
    print("mean pace differs between surfaces by at most %.1f in a hundred, on "
          "any path, read from either end" % (100 * gap))
    if gap > 0.05:
        faults.append("the mean pace differs by surface, which a first look "
                      "would take for a sign, rightly or wrongly")

    walked = YARD / "walked.json"
    if walked.is_file():
        told = json.loads(walked.read_text())
        misread = [name for name, end in told.items()
                   if (end == "top") != paths[name]["from_top"]]
        print("walks the chatter misreads: %d" % len(misread))
        if misread:
            faults.append("the chatter misreads %s" % " ".join(misread))
    with_habit = [p["from_top"] for p in paths.values() if p["habits"]]
    if sum(with_habit) in (0, len(with_habit)):
        faults.append("the end a walk began at goes with having a habit")

    # ---- the natural reading must show no symptom ---------------------------
    natural = ref.run(YARD, dict(ref.TRUE_READING,
                                 walked_from="from_the_foot"))
    lost = sum(1 for k in truth if natural.get(k) == "NONE")
    print("of the forty, readings that fall off the path under the natural "
          "reading: %d" % lost)
    if lost:
        faults.append("the natural reading drops readings off the path, which "
                      "announces itself")

    print()
    print("the whole account gets           %d of %d" % (marks[right], full))
    print("the best account that is not it  %d of %d" % (best_wrong, full))

    bar = full - 4
    if marks[right] != full:
        faults.append("the whole account does not get every altitude")
    if best_wrong >= bar:
        faults.append("an account that gets something wrong clears the bar")
    if commonest >= bar:
        faults.append("guessing clears the bar")
    if full - single["walked_from"] <= full - bar:
        faults.append("the end a walk began at costs no more than the "
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
            "single": single, "turned": turned, "paths": len(paths),
            "weakest": round(weakest, 1), "narrowest": round(narrowest, 1),
            "all_top": marks[top], "readings": len(marks),
            "pace_gap": int(100 * gap) + 1,
            "stations": sum(len(p["stations"]) for p in paths.values()),
            "rows": sum(len(p["times"]) for p in paths.values()),
        }, indent=1), newline="\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
