"""Every way of locating the peaks without doing the work, scored.

    python gates.py

Built from what earlier tasks taught, at some cost. This scores, in one place:

  * every reading of the records, so no surveyor's habit is decoration and no
    partial account comes near the bar;
  * guessing - the middle of each window;
  * whether the instrument's heading error really does SETTLE which end each
    grid was begun from, because if it does not that reading is a guess and
    the task is a hidden contract;
  * that nothing else shows it: nothing on the site runs from one grid into
    the next, so laying a grid out the other way about makes it fit its
    neighbours no better and no worse, and every window keeps a perfectly
    plausible peak. An earlier build crossed the site with ditches, and cold
    solvers tried every grid every way about against its neighbours without
    being asked to;
  * and that the grids begun from the north are spread evenly over the four
    surveyors who strayed, while the one who kept to the specification began
    every grid where it says - which is what shows, in the readings, how a
    grid begun from the south looks.

Nothing ships until every one of them holds.
"""

from __future__ import annotations

import collections
import itertools
import json

import ref
import survey

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
    for combo, mark in sorted(marks.items(), key=lambda kv: -kv[1])[:10]:
        flag = "   <- the whole account" if combo == right else ""
        print("  " + "".join("%-13s" % part[:12] for part in combo)
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
        print("  %-10s %-14s -> %2d of %d" % (axis, ref.OTHERS[axis],
                                              marks[combo], full))

    # ---- guessing -----------------------------------------------------------
    grids, dumps, anomalies = ref.load(YARD)
    middle = 0
    for row in anomalies:
        east = (ref.dm(row["east_from_m"]) + ref.dm(row["east_to_m"])) // 2
        north = (ref.dm(row["north_from_m"]) + ref.dm(row["north_to_m"])) // 2
        east -= east % survey.CELL_DM
        north -= north % survey.CELL_DM
        if survey.cell_ref(east, north) == truth[row["anomaly"]]:
            middle += 1
    print()
    print("naming the middle of each window gets %d of %d" % (middle, full))

    # ---- does the heading error settle which end each grid was begun from? --
    steps = {}
    for g in grids:
        readings = dumps[g["grid"]]
        per_cell = 2 if len(readings) == 2 * survey.CELLS ** 2 else 1
        step = float(ref.heading_step(readings, per_cell))
        if abs(step) > 10:                  # the instrument on the wrong range
            step /= 10
        steps[g["grid"]] = step
    faintest = min(abs(s) for s in steps.values())
    north = sum(1 for s in steps.values() if s < 0)
    print("every grid's northward traverses stand at least %.2f nT above its "
          "southward ones (the instrument's heading error is %d nT from one "
          "way to the other); %d of %d grids were begun from the north"
          % (faintest, 2 * survey.HEADING, north, len(grids)))
    # six standard errors, with eight hundred readings a side and ground
    # that is noisy by eight nanotesla either way
    if faintest < 1.2:
        faults.append("the heading error does not settle which end a grid was "
                      "begun from, so that reading is a guess")
    if not len(grids) // 4 <= north <= 3 * len(grids) // 4:
        faults.append("too few grids were begun from one end for it to matter")

    begun_file = YARD / "begun.json"
    if begun_file.is_file():
        begun = json.loads(begun_file.read_text())
        misread = [g for g, end in begun.items()
                   if (steps[g] < 0) != (end == "N")]
        print("grids whose heading error points the wrong way: %d"
              % len(misread))
        if misread:
            faults.append("the heading error misreads %s" % " ".join(misread))
        by_surveyor = collections.defaultdict(collections.Counter)
        for g in grids:
            by_surveyor[g["surveyor"]][begun[g["grid"]]] += 1
        print("begun from the north, by surveyor: %s"
              % ", ".join("%s %d of %d" % (who, c["N"], sum(c.values()))
                          for who, c in sorted(by_surveyor.items())))
        clean = [who for who, c in by_surveyor.items() if c["N"] == 0]
        if len(clean) != 1 or any(c["N"] * 2 != sum(c.values())
                                  for who, c in by_surveyor.items()
                                  if who not in clean):
            faults.append("the grids begun from the north are not spread "
                          "evenly over the surveyors who strayed")

    # ---- nothing else may show it --------------------------------------------
    # Lay every grid out as begun from the south and as begun from the north,
    # and see how well its north and south edges meet its neighbours' each way.
    corners, _ = ref.tile(grids, ref.TRUE_READING)
    laid = {}
    for g in grids:
        readings = dumps[g["grid"]]
        per_cell = 2 if len(readings) == 2 * survey.CELLS ** 2 else 1
        if abs(ref.heading_step(readings, per_cell)) > 10:
            readings = [v // 10 for v in readings]
        right_end = "N" if steps[g["grid"]] < 0 else "S"
        wrong_end = "S" if right_end == "N" else "N"
        laid[corners[g["grid"]]] = (
            survey.assemble(readings, per_cell, True, right_end),
            survey.assemble(readings, per_cell, True, wrong_end))

    def seam(flipped):
        total = count = 0
        for (east, north_), pair in laid.items():
            above = laid.get((east, north_ + survey.GRID_DM))
            if above is None:
                continue
            mine = pair[1 if flipped else 0]
            for t in range(survey.CELLS):
                total += abs(mine[t][-1] - above[0][t][0])
                count += 1
        return float(total) / max(1, count)

    fits, misfits = seam(False), seam(True)
    print("mean step across a grid's north edge into its neighbour: %.2f nT "
          "laid out the right way about, %.2f the wrong way" % (fits, misfits))
    if not 0.85 <= fits / misfits <= 1.18:
        faults.append("a grid laid out the wrong way about visibly fails to "
                      "meet its neighbours, which a solver can test")

    # ---- taking the heading error out must change no answer -----------------
    # The specification defines a peak on the readings as logged. A solver who
    # works out which way each traverse was walked may well take the heading
    # error back out before looking for peaks; that is a defensible thing to
    # do, so it must not cost him an answer.
    mosaic = {}
    for corner, (raster, _) in laid.items():
        grid = next(g["grid"] for g in grids if corners[g["grid"]] == corner)
        begun_end = "N" if steps[grid] < 0 else "S"
        for t_, line in enumerate(raster):
            northwards = (begun_end == "S") == (t_ % 2 == 0)
            for c_, value in enumerate(line):
                mosaic[(corner[0] + t_ * survey.CELL_DM,
                        corner[1] + c_ * survey.CELL_DM)] = value - (
                    survey.HEADING if northwards else -survey.HEADING)
    moved_by_heading = 0
    for row in anomalies:
        where = survey.peak(mosaic, ref.dm(row["east_from_m"]),
                            ref.dm(row["east_to_m"]),
                            ref.dm(row["north_from_m"]),
                            ref.dm(row["north_to_m"]))
        if survey.cell_ref(*where) != truth[row["anomaly"]]:
            moved_by_heading += 1
    print("peaks that move if the heading error is taken out first: %d"
          % moved_by_heading)
    if moved_by_heading:
        faults.append("taking the heading error out changes an answer, so "
                      "two defensible readings of a peak disagree")

    natural = ref.run(YARD, dict(ref.TRUE_READING, begun="south_west"))
    missing = sum(1 for k in truth if natural.get(k) == "NONE")
    print("windows left with no peak under the natural reading: %d" % missing)
    if missing:
        faults.append("the natural reading leaves windows empty, which "
                      "announces itself")

    print()
    print("the whole account locates         %d of %d" % (marks[right], full))
    print("the best account that is not it   %d of %d" % (best_wrong, full))

    bar = full - 4
    begun_cost = full - single["begun"]
    if marks[right] != full:
        faults.append("the whole account does not locate every peak")
    if best_wrong >= bar:
        faults.append("an account that gets something wrong clears the bar")
    if middle >= bar:
        faults.append("guessing clears the bar")
    if begun_cost <= full - bar:
        faults.append("which end a grid was begun from costs no more than the "
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
            "as_stands": marks[plain], "middle": middle, "single": single,
            "faintest": round(faintest, 2), "north": north,
            "fits": round(fits, 2), "misfits": round(misfits, 2),
            "begun_cost": begun_cost, "readings": len(marks),
        }, indent=1), newline="\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
