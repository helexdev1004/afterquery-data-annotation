"""Every way of placing the samples without doing the work, scored.

    python gates.py

Four earlier tasks of mine reached review only after every one of these had
been measured first. So this scores, in one place:

  * every reading of the records, so no curator's habit is decoration and no
    partial account comes near the bar;
  * guessing - one bed for everything;
  * whether the beds' grading really does SETTLE which sections were labelled
    upside down, because if it does not that reading is a guess and the task
    is a hidden contract;
  * that nothing announces the mistake to a solver who takes every section to
    lie as it is labelled: a sample is found among the beds of its own section
    as that section was logged, so every sample falls in a bed either way;
  * that being labelled upside down is nobody's habit, so that no curator's
    sections can be checked against another's;
  * and that no wanted sample stands near enough a bed boundary for the rule
    about boundaries, or an inch's rounding, to decide its bed.

Nothing ships until every one of them holds.
"""

from __future__ import annotations

import collections
import itertools
import json

import coring
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
    print("  " + "".join("%-16s" % name for name in WAYS) + "score")
    for combo, mark in sorted(marks.items(), key=lambda kv: -kv[1])[:10]:
        flag = "   <- the whole account" if combo == right else ""
        print("  " + "".join("%-16s" % part[:15] for part in combo)
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
        combo = tuple(ref.OTHERS[a] if a == axis else ref.TRUE_READING[a]
                      for a in WAYS)
        single[axis] = marks[combo]
        print("  %-12s %-14s -> %2d of %d" % (axis, ref.OTHERS[axis],
                                              marks[combo], full))

    commonest = collections.Counter(truth.values()).most_common(1)[0][1]
    print()
    print("one bed named for every sample gets %d of %d" % (commonest, full))

    # ---- does the grading settle which sections were labelled upside down? --
    book, sections, samples = ref.build(YARD, ref.TRUE_READING)
    closest, turned = None, 0
    for name, s in sorted(sections.items()):
        margin = int(abs(s["lean"]) / max(1, len(s["beds"])))
        closest = margin if closest is None else min(closest, margin)
        turned += not s["right_way_up"]
    print()
    print("sections labelled upside down: %d of %d; in every section the beds "
          "read coarser in their lower third than their upper, or the other "
          "way about, by at least %d points of the scanner's index a bed"
          % (turned, len(sections), closest))
    if closest < 6:
        faults.append("a section's grading does not settle which way up it "
                      "lies, so that reading is a guess")

    labelled = YARD / "labelled.json"
    if labelled.is_file():
        told = json.loads(labelled.read_text())
        misread = [name for name, way in told.items()
                   if (way == "up") != sections[name]["right_way_up"]]
        print("sections the grading misreads: %d" % len(misread))
        if misread:
            faults.append("the grading misreads %s" % " ".join(misread))
    by_curator = collections.defaultdict(list)
    for s in sections.values():
        by_curator[s["curator"]].append(not s["right_way_up"])
    print("  by curator: %s" % ", ".join(
        "%s %d of %d" % (who, sum(v), len(v))
        for who, v in sorted(by_curator.items())))
    if any(sum(v) in (0, len(v)) for v in by_curator.values()):
        faults.append("being labelled upside down goes with who curated the "
                      "hole, and his sections can be checked against others'")

    # ---- the natural reading must show no symptom ---------------------------
    natural = ref.run(YARD, dict(ref.TRUE_READING, way_up="as_labelled"))
    lost = sum(1 for k in truth if natural.get(k) == "NONE")
    print("of the forty, samples left in no bed under the natural reading: %d"
          % lost)
    if lost:
        faults.append("the natural reading leaves samples in no bed, which "
                      "announces itself")

    # ---- nothing may stand on a boundary ------------------------------------
    tight = 0
    for sample in samples:
        if sample["sample"] not in truth:
            continue
        s = sections[sample["section"]]
        along = coring.bed_at(s["beds"], sample["offset"])
        top, base = s["beds"][along - 1]
        if min(sample["offset"] - top, base - sample["offset"]) < 12:
            tight += 1
    print("of the forty, samples within 1.2 cm of a bed boundary: %d" % tight)
    if tight:
        faults.append("a wanted sample stands on a bed boundary")

    print()
    print("the whole account places          %d of %d" % (marks[right], full))
    print("the best account that is not it   %d of %d" % (best_wrong, full))

    bar = full - 4
    if marks[right] != full:
        faults.append("the whole account does not place every sample")
    if best_wrong >= bar:
        faults.append("an account that gets something wrong clears the bar")
    if commonest >= bar:
        faults.append("guessing clears the bar")
    if full - single["way_up"] <= full - bar:
        faults.append("the labelling costs no more than the allowance")

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
            "single": single, "turned": turned, "sections": len(sections),
            "closest": closest, "holes": len(by_curator),
            "readings": len(marks),
        }, indent=1), newline="\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
