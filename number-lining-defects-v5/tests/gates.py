"""Every way of numbering the defects' rings without doing the work, scored.

    python gates.py

Two earlier tasks of mine reached review only after every one of these had been
measured first. So this scores, in one place:

  * every reading of the records, so no inspector's habit is decoration and no
    partial account comes near the bar;
  * guessing - one ring for everything;
  * whether the joint survey really does SETTLE which portal every tape was
    begun from, because if it does not that reading is a guess and the task is
    a hidden contract;
  * that nothing announces the mistake to a solver who takes every tape to run
    from portal A: every defect falls on the tape and in a ring either way, and
    nothing in the inspection can be checked against anything that knows which
    portal is which;
  * that the portal a tape was begun from does not go with who inspected the
    tunnel in any way a solver could use;
  * and that no wanted defect stands near enough a joint for the rule about
    joints, or a foot's rounding, to decide its ring.

Nothing ships until every one of them holds.
"""

from __future__ import annotations

import collections
import itertools
import json

import lining
import ref

YARD, SEALED = ref.places()

WAYS = {axis: (ref.TRUE_READING[axis], other) + ref.EXTRAS.get(axis, ())
        for axis, other in ref.OTHERS.items()}


def main() -> int:
    truth = json.loads((SEALED / "truth.json").read_text())
    full = len(truth)
    faults = []

    def score(got):
        return sum(1 for k in truth if got.get(k) == truth[k])

    marks = {}
    for combo in itertools.product(*(WAYS[k] for k in WAYS)):
        marks[combo] = score(ref.run(YARD, dict(zip(WAYS, combo))))

    right = tuple(ref.TRUE_READING[k] for k in WAYS)
    print("  " + "".join("%-15s" % name for name in WAYS) + "score")
    for combo, mark in sorted(marks.items(), key=lambda kv: -kv[1])[:10]:
        flag = "   <- the whole account" if combo == right else ""
        print("  " + "".join("%-15s" % part[:14] for part in combo)
              + "%2d of %d%s" % (mark, full, flag))
    plain = tuple(ref.OTHERS[k] for k in WAYS)
    print("  ...")
    print("  the records taken exactly as they stand: %d of %d"
          % (marks[plain], full))

    best_wrong = max(v for k, v in marks.items() if k != right)
    single = {}
    print()
    print("everything right but one:")
    for axis in WAYS:
        for other in WAYS[axis][1:]:
            combo = tuple(other if a == axis else ref.TRUE_READING[a]
                          for a in WAYS)
            label = axis if other == ref.OTHERS[axis] else other
            single[label] = marks[combo]
            print("  %-11s %-16s -> %2d of %d" % (axis, other, marks[combo],
                                                  full))

    commonest = collections.Counter(truth.values()).most_common(1)[0][1]
    print()
    print("one ring named for every defect gets %d of %d" % (commonest, full))

    # ---- does the joint survey settle which portal each tape began at? ------
    book, tunnels, joints, from_a, defects = ref.build(YARD, ref.TRUE_READING)
    weakest, furthest, nearest_wrong = None, 0, None
    for name, t in sorted(tunnels.items()):
        sharp, rings_before = ref.change_of_hand(joints[name])
        met = t["rings_a"] if from_a[name] else t["rings_b"]
        other = t["rings_b"] if from_a[name] else t["rings_a"]
        weakest = float(sharp) if weakest is None else min(weakest, float(sharp))
        furthest = max(furthest, abs(rings_before - met))
        gap = abs(rings_before - other)
        nearest_wrong = gap if nearest_wrong is None else min(nearest_wrong, gap)
    print()
    print("in every tunnel the evenness of the joints changes - by at least "
          "%.2f times - within %d rings of the number its first-met drive "
          "built, and no nearer than %d rings to the number the other built"
          % (weakest, furthest, nearest_wrong))
    if weakest < 2.5 or furthest > 6 or nearest_wrong < 30:
        faults.append("the joint survey does not settle which portal a tape "
                      "was begun from, so that reading is a guess")

    begun_a = sum(1 for way in from_a.values() if way)
    print("tapes begun from portal A: %d of %d" % (begun_a, len(from_a)))
    if begun_a in (0, len(from_a)):
        faults.append("every tape was begun from the same portal, so a rule of "
                      "thumb would do")

    taped = YARD / "taped.json"
    if taped.is_file():
        told = json.loads(taped.read_text())
        misread = [name for name, portal in told.items()
                   if (portal == "A") != from_a[name]]
        print("tapes the joint survey misreads: %d" % len(misread))
        if misread:
            faults.append("the joint survey misreads %s" % " ".join(misread))

    # ---- the natural reading must show no symptom ---------------------------
    natural = ref.run(YARD, dict(ref.TRUE_READING, tape="from_portal_a"))
    lost = sum(1 for k in truth if natural.get(k) == "NONE")
    print("of the forty, defects left on no ring under the natural reading: %d"
          % lost)
    if lost:
        faults.append("the natural reading leaves defects on no ring, which "
                      "announces itself")

    # ---- nothing may stand on a joint ---------------------------------------
    tight = 0
    for d in defects:
        if d["defect"] not in truth:
            continue
        along = lining.ring_along(joints[d["tunnel"]], d["chainage"])
        span = joints[d["tunnel"]]
        if min(d["chainage"] - span[along - 1],
               span[along] - d["chainage"]) < 40:
            tight += 1
    print("of the forty, defects within 4 cm of a joint: %d" % tight)
    if tight:
        faults.append("a wanted defect stands on a joint")

    print()
    print("the whole account numbers         %d of %d" % (marks[right], full))
    print("the best account that is not it   %d of %d" % (best_wrong, full))

    bar = full - 4
    if marks[right] != full:
        faults.append("the whole account does not number every defect")
    if best_wrong >= bar:
        faults.append("an account that gets something wrong clears the bar")
    if commonest >= bar:
        faults.append("guessing clears the bar")
    if full - single["tape"] <= full - bar:
        faults.append("the tape's direction costs no more than the allowance")

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
            "single": single, "sharp": round(weakest, 2),
            "furthest": furthest, "nearest_wrong": nearest_wrong,
            "begun_a": begun_a, "tunnels": len(tunnels),
            "readings": len(marks),
        }, indent=1), newline="\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
