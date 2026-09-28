"""Every way of tracing the faults without doing the work, scored.

    python gates.py

Two earlier tasks of mine reached review only after every one of these had been
measured first. So this scores, in one place:

  * every reading of the records, so no inspector's habit is decoration and no
    partial account comes near the bar;
  * guessing - the commonest panel, and the panel nearest the middle of a roll;
  * whether the mill seams really do SETTLE which way every roll was laid up,
    because if they do not that reading is a guess and the task is a hidden
    contract;
  * that nothing announces the mistake to a solver who takes every roll to have
    been laid up the way it was inspected: every fault to be traced lands in a
    panel either way, and as many of the mill's faults fall in the waste one
    way as the other;
  * that being laid up tail first is nobody's habit, so that no inspector's
    rolls can be checked against another's;
  * and that no fault to be traced stands near enough a cut line for the rule
    about cut lines, or a yard's or an inch's rounding, to decide its panel.

Nothing ships until every one of them holds.
"""

from __future__ import annotations

import collections
import itertools
import json

import cutroom
import ref

YARD, SEALED = ref.places()

WAYS = {axis: (ref.TRUE_READING[axis], other) + ref.EXTRAS.get(axis, ())
        for axis, other in ref.OTHERS.items()}


def main() -> int:
    truth = json.loads((SEALED / "truth.json").read_text())
    full = len(truth)
    faults_found = []

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
            print("  %-8s %-18s -> %2d of %d" % (axis, other, marks[combo],
                                                 full))

    # ---- guessing -----------------------------------------------------------
    commonest = collections.Counter(truth.values()).most_common(1)[0][1]
    print()
    print("one panel named for every fault gets %d of %d" % (commonest, full))

    # ---- do the seams settle which way every roll was laid up? --------------
    book, rolls, panels, faults, tail_first = ref.build(YARD, ref.TRUE_READING)
    parted = cut = 0
    unsettled = []
    for roll, r in sorted(rolls.items()):
        seams = [f for f in faults if f["roll"] == roll and f["kind"] == "seam"]

        def cut_into(way):
            return sum(1 for s in seams if cutroom.panel_at(
                panels[roll], *cutroom.to_lay(s["along"], r["width"] // 2,
                                              r["length"], r["width"], way)))

        good, bad = cut_into(tail_first[roll]), cut_into(not tail_first[roll])
        parted += len(seams) - good
        cut += bad
        if good or bad < len(seams) or len(seams) < 2:
            unsettled.append(roll)
    seams_all = sum(1 for f in faults if f["kind"] == "seam")
    print()
    print("of %d mill seams, %d stand in a parting of the lay with their roll "
          "taken the right way about, and %d stand inside a panel with it taken "
          "the wrong way" % (seams_all, parted, cut))
    if unsettled:
        faults_found.append("the seams do not settle how %s was laid up, so "
                            "that reading is a guess" % " ".join(unsettled))

    tails = sum(1 for way in tail_first.values() if way)
    print("rolls laid up tail first: %d of %d" % (tails, len(rolls)))
    by_inspector = collections.defaultdict(list)
    for roll, r in rolls.items():
        by_inspector[r["inspector"]].append(tail_first[roll])
    print("  by inspector: %s" % ", ".join(
        "%s %d of %d" % (who, sum(ways), len(ways))
        for who, ways in sorted(by_inspector.items())))
    if any(sum(ways) in (0, len(ways)) for ways in by_inspector.values()):
        faults_found.append("how a roll was laid up goes with who inspected "
                            "it, and his rolls can be checked against others'")

    laid = YARD / "laid.json"
    if laid.is_file():
        told = json.loads(laid.read_text())
        misread = [roll for roll, way in told.items()
                   if (way == "tail") != tail_first[roll]]
        print("rolls the seams misread: %d" % len(misread))
        if misread:
            faults_found.append("the seams misread %s" % " ".join(misread))

    # ---- the natural reading must show no symptom ---------------------------
    natural = ref.run(YARD, dict(ref.TRUE_READING, lay="as_inspected"))
    lost = sum(1 for k in truth if natural.get(k) == "WASTE")
    print("of the forty, faults left in the waste under the natural reading: "
          "%d" % lost)
    if lost:
        faults_found.append("the natural reading leaves faults in the waste, "
                            "which a solver would chase")

    def wasted(way_of):
        count = 0
        for f in faults:
            if f["kind"] == "seam":
                continue
            r = rolls[f["roll"]]
            spot = cutroom.to_lay(f["along"], f["across"], r["length"],
                                  r["width"], way_of(f["roll"]))
            if not cutroom.panel_at(panels[f["roll"]], *spot):
                count += 1
        return count

    right_waste = wasted(lambda roll: tail_first[roll])
    natural_waste = wasted(lambda roll: False)
    print("of the mill's faults, %d fall in the waste with every roll taken "
          "the right way about and %d with every roll taken as inspected"
          % (right_waste, natural_waste))
    if not 0.75 <= right_waste / max(1, natural_waste) <= 1.33:
        faults_found.append("the share of faults in the waste shows which way "
                            "the rolls were laid up")

    # ---- nothing may stand on a cut line -------------------------------------
    tight = 0
    for f in faults:
        if f["fault"] not in truth:
            continue
        r = rolls[f["roll"]]
        x, y = cutroom.to_lay(f["along"], f["across"], r["length"], r["width"],
                              tail_first[f["roll"]])
        _, a0, a1, c0, c1 = next(p for p in panels[f["roll"]]
                                 if p[0] == truth[f["fault"]])
        if min(x - a0, a1 - x, y - c0, c1 - y) < 2:
            tight += 1
    print("of the forty, faults within 2 cm of a cut line: %d" % tight)
    if tight:
        faults_found.append("a fault to be traced stands on a cut line")

    print()
    print("the whole account traces          %d of %d" % (marks[right], full))
    print("the best account that is not it   %d of %d" % (best_wrong, full))

    bar = full - 4
    if marks[right] != full:
        faults_found.append("the whole account does not trace every fault")
    if best_wrong >= bar:
        faults_found.append("an account that gets something wrong clears the "
                            "bar")
    if commonest >= bar:
        faults_found.append("guessing clears the bar")
    if full - single["lay"] <= full - bar:
        faults_found.append("the lay costs no more than the allowance")

    print()
    print("bar %d of %d - %d clear of the best wrong account"
          % (bar, full, bar - best_wrong))
    if faults_found:
        print()
        for fault in faults_found:
            print("FAILED: %s" % fault)
        return 1
    print("no account that skips the work comes near it")

    try:
        (SEALED / "gates.json").write_text(json.dumps({
            "full": full, "bar": bar, "best_wrong": best_wrong,
            "as_stands": marks[plain], "commonest": commonest,
            "single": single, "seams": seams_all, "parted": parted,
            "cut": cut, "tails": tails, "rolls": len(rolls),
            "right_waste": right_waste, "natural_waste": natural_waste,
            "readings": len(marks),
        }, indent=1), newline="\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
