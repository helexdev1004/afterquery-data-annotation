"""Every way of phasing the finds without doing the work, scored.

    python gates.py

An earlier task of mine was lost four times over to accounts nobody had
scored, and the one that finally went through did so because every one of
these was measured first. So this scores, in one place:

  * every reading of the archive, so no habit is decoration and no partial
    account comes near the bar;
  * guessing - one context for everything, and the commonest context of each
    find's own trench and section;
  * whether each drawing's change of hands really does SETTLE which way that
    drawing runs, because if it does not that reading is a guess and the
    task is a hidden contract;
  * that nothing shows the mistake to a solver who takes every drawing to run
    from the zero peg - no find left outside the deposits, no context number
    that the drawings do not explain, no pit drawn at two offsets;
  * and that no find to be phased stands near enough a boundary, or near
    enough the meeting point, for anybody's rounding to decide its context.

Nothing ships until every one of them holds.
"""

from __future__ import annotations

import collections
import itertools
import json
from fractions import Fraction

import ref
import site_model as site

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
    print("  " + "".join("%-13s" % name for name in WAYS) + "score")
    for combo, mark in sorted(marks.items(), key=lambda kv: -kv[1])[:12]:
        flag = "   <- the whole account" if combo == right else ""
        print("  " + "".join("%-13s" % part[:12] for part in combo)
              + "%2d of %d%s" % (mark, full, flag))
    print("  ...")
    plain = tuple(ref.OTHERS[k] for k in WAYS)
    print("  the archive taken exactly as it stands: %d of %d"
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
            print("  %-10s %-20s -> %2d of %d" % (axis, other, marks[combo],
                                                  full))

    # ---- guessing -----------------------------------------------------------
    book = ref.load(YARD)
    where = {row["find"]: (row["trench"], row["section"])
             for row in book["finds"]}
    spread = collections.Counter(truth.values())
    commonest = spread.most_common(1)[0][1]
    groups = collections.defaultdict(collections.Counter)
    for k, context in truth.items():
        groups[where[k]][context] += 1
    by_place = sum(c.most_common(1)[0][1] for c in groups.values())
    print()
    print("one context named for every find gets %d of %d" % (commonest, full))
    print("the commonest context of each find's own trench and section gets "
          "%d of %d (and needs the answers to know it)" % (by_place, full))

    # ---- no pit may stand in both of a trench's drawings ---------------------
    _, trenches, built, from_peg, fixed = ref.build(YARD, ref.TRUE_READING)

    def paired(name, turned):
        length = trenches[name]["length"]
        count = 0
        for _, n_top, n_bottom in built[(name, "N")]["features"]:
            for _, s_top, s_bottom in built[(name, "S")]["features"]:
                n_a, n_b = n_top[0][0], n_top[-1][0]
                s_a, s_b = s_top[0][0], s_top[-1][0]
                if turned:
                    s_a, s_b = length - s_b, length - s_a
                n_deep = max(z for _, z in n_bottom) - min(z for _, z in n_top)
                s_deep = max(z for _, z in s_bottom) - min(z for _, z in s_top)
                if abs((n_b - n_a) - (s_b - s_a)) <= 8 \
                        and abs(n_deep - s_deep) <= 30 \
                        and abs(n_a - s_a) <= 60 and abs(n_b - s_b) <= 60:
                    count += 1
        return count

    pits = sum(len(built[(name, "N")]["features"]) for name in trenches)
    lined_up = sum(paired(name, False) for name in trenches)
    turned_round = sum(paired(name, True) for name in trenches)
    print()
    print("pits of one drawing that match a pit of the trench's other drawing "
          "in size and place: %d with both drawings read one way, %d with one "
          "turned round" % (lined_up, turned_round))
    # Three builds let the pits run right across the trench, and each time
    # cold solvers matched them up between the two drawings - by number, then
    # by size - and had the drawings' directions in two minutes. No pit may
    # stand in both drawings.
    if lined_up or turned_round:
        faults.append("a pit stands in both of a trench's drawings, where a "
                      "solver can lay one drawing against the other")
    if any(from_peg[(name, "S")] == from_peg[(name, "N")]
           for name in trenches):
        faults.append("the reference takes both drawings of a trench to run "
                      "the same way")

    # ---- and does each drawing's hand settle WHICH one runs from the peg? ---
    weakest, widest, nearest_wrong = None, 0, None
    for (name, side), way in sorted(from_peg.items()):
        t = trenches[name]
        here = t["meet"] if way else t["length"] - t["meet"]
        there = t["length"] - here
        edges = {x for _, top, _ in built[(name, side)]["features"]
                 for x in (top[0][0], top[-1][0])}
        sharp, where = ref.change_of_hand(built[(name, side)]["surface"],
                                          edges)
        weakest = float(sharp) if weakest is None else min(weakest,
                                                           float(sharp))
        widest = max(widest, abs(where - here))
        nearest_wrong = abs(where - there) if nearest_wrong is None else min(
            nearest_wrong, abs(where - there))
    print("every drawing changes hands - its points at least %.1f times closer "
          "on one side than the other - within %d cm of the meeting point read "
          "the right way about, and no nearer than %d cm to it read the wrong "
          "way" % (weakest, widest, nearest_wrong))
    if weakest < 1.8 or widest > 200 or nearest_wrong < 2 * widest:
        faults.append("the drawings' hands do not settle which drawing runs "
                      "from the zero peg, so that reading is a guess")
    north_from = sum(1 for (name, side), way in from_peg.items()
                     if side == "N" and way)
    print("trenches whose north drawing is the one that runs from the zero "
          "peg: %d of %d" % (north_from, len(trenches)))
    if north_from in (0, len(trenches)):
        faults.append("the same drawing runs from the peg in every trench, so "
                      "a rule of thumb would do")

    # ---- and nothing LABELLED may show it -----------------------------------
    # A pit under one number in both drawings stands at two offsets in any
    # listing of the contexts. Layers of one thickness in both drawings agree
    # only with one drawing turned, which a solver who lays one over the other
    # sees at once. A drawing jointed at the meeting point shows which end it
    # runs from to anyone who looks there. Each of those let cold solvers phase
    # all forty inside two minutes, so none of them may be in the data.
    same_way = turned = Fraction(0)
    samples = shared = jointed = 0
    for name, t in trenches.items():
        north = {c: (top, bottom)
                 for c, top, bottom in built[(name, "N")]["layers"]}
        south = {c: (top, bottom)
                 for c, top, bottom in built[(name, "S")]["layers"]}
        shared += len({c for c, _, _ in built[(name, "N")]["features"]}
                      & {c for c, _, _ in built[(name, "S")]["features"]})
        for side in ("N", "S"):
            for _, top, bottom in built[(name, side)]["layers"]:
                for poly in (top, bottom):
                    if {t["meet"], t["length"] - t["meet"]} & {x for x, _ in poly}:
                        jointed += 1

        def thick(pair, at):
            return ref.value_at(pair[1], at) - ref.value_at(pair[0], at)

        for context in north:
            for x in range(50, t["length"] - 49, 50):
                here = thick(north[context], x)
                same_way += abs(here - thick(south[context], x))
                turned += abs(here - thick(south[context], t["length"] - x))
                samples += 1
    same_way, turned = float(same_way / samples), float(turned / samples)
    print("a layer's thickness in one drawing against the other's at the same "
          "offset: %.1f cm apart read the same way about, %.1f cm with one "
          "turned round" % (same_way, turned))
    if not 0.8 <= same_way / turned <= 1.25:
        faults.append("the layers' thickness shows which way the drawings run "
                      "to anyone who lays one drawing over the other")
    print("pits under one number in both of a trench's drawings: %d" % shared)
    if shared:
        faults.append("a pit stands in both drawings under one number, and a "
                      "listing of the contexts shows it at two offsets")
    print("boundaries with a digitised point at the meeting point, either way "
          "about: %d" % jointed)
    if jointed:
        faults.append("a drawing carries a point at the meeting point, which "
                      "shows which end it runs from")

    # ---- the natural reading must show no symptom ---------------------------
    # Eight builds of this task were phased by cold solvers inside two minutes,
    # every time off something that went visibly wrong under the wrong reading:
    # finds above the turf, a pit at two offsets, finds missing the pits. Here
    # a find is located on its own drawing in that drawing's own frame, so
    # every find lands in the deposits and in the pits whatever the solver
    # thinks of the meeting point.
    stray = 0
    for f in fixed:
        key = (f["trench"], f["section"])
        ground = ref.value_at(built[key]["surface"], f["x"])
        base = ref.value_at(built[key]["floor"], f["x"])
        if ground is None or f["z"] < ground or f["z"] >= base:
            stray += 1
    print("finds outside the deposits: %d of %d" % (stray, len(fixed)))
    if stray:
        faults.append("finds lie outside the deposits, which a solver would "
                      "chase")

    natural = ref.run(YARD, dict(ref.TRUE_READING,
                                 meeting="along_the_drawing"))
    hanging = sum(1 for k in truth if natural.get(k) == "NONE")
    print("of the forty, finds left in no context under the natural reading: "
          "%d" % hanging)
    if hanging:
        faults.append("the natural reading leaves finds nowhere, which "
                      "announces itself")

    # ---- the generator must leave no margin for a solver to test against ----
    near = 0
    for f in fixed:
        key = (f["trench"], f["section"])
        gap = site.nearest_boundary(built[key], f["x"], f["z"])
        if gap is not None and gap < 4:
            near += 1
    print("finds within 4 cm of a boundary: %d of %d" % (near, len(fixed)))
    if near < 25:
        faults.append("finds keep clear of the boundaries, which a solver can "
                      "test a reading against")

    close = 0
    for f in fixed:
        if f["find"] not in truth:
            continue
        t = trenches[f["trench"]]
        if min(abs(f["x"] - t["meet"]),
               abs(t["length"] - f["x"] - t["meet"])) < 5:
            close += 1
    print("of the forty, finds within 5 cm of the meeting point either way "
          "about: %d" % close)
    if close:
        faults.append("a find to be phased stands at the meeting point")

    print()
    print("the whole account phases          %d of %d" % (marks[right], full))
    print("the best account that is not it   %d of %d" % (best_wrong, full))

    bar = full - 4
    if marks[right] != full:
        faults.append("the whole account does not phase every find")
    if best_wrong >= bar:
        faults.append("an account that gets something wrong clears the bar")
    if max(commonest, by_place) >= bar:
        faults.append("guessing clears the bar")
    if full - single["meeting"] <= full - bar:
        faults.append("the meeting point costs no more than the allowance")

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
            "by_place": by_place, "single": single,
            "pits": pits, "lined_up": lined_up, "turned_round": turned_round,
            "hand": round(weakest, 1), "north_from": north_from,
            "hand_near": widest, "hand_far": nearest_wrong,
            "half_way": single["north_from_the_peg"],
            "readings": len(marks),
        }, indent=1), newline="\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
