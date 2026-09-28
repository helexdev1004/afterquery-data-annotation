"""Saw the mill's stock, forward from the truth.

    python gen.py [outdir]

The boards are sawn and the defects laid on them first; the grades are then
worked out from those boards by mill.py. So every grade is exact by
construction rather than a judgement made afterwards.

The stock book is then written the way several men over forty years would have
written it, which is where the four departures come from. Nothing is corrupted
at random: each one is a thing a mill record actually does.
"""

from __future__ import annotations

import csv
import json
import pathlib
import random
import sys

import mill

SEED = 20260918
PARCELS = 40
TO_GRADE = 40

BENCHES = ("A", "B", "C", "D")
# What each bench's logs are like. The benches are not interchangeable, so the
# yields they produce are not expected to agree and no comparison between them
# tells a solver whether a correction was right.
BENCH_TIMBER = {"A": -1, "B": 1, "C": 2, "D": 0}
CUT_FOR = ("furniture", "flooring", "joinery", "pattern stock", "cooperage")

# The bench that books a knot the wrong way about: its sawyer measures across
# the grain, everyone else takes the greatest dimension. A knot grows longer
# ALONG the grain, so his figures come out the wrong way round and say so.
SWAPPED_BENCH = "C"
# The bench that books the wane as the width LEFT rather than the width lost.
# His figures sit close to the board's own width instead of being small, which
# is what gives it away.
REMAINING_BENCH = "D"
NOMINALS = (25, 32, 38, 50, 63)
# The bench whose book runs in centimetres along the board, not millimetres.
# Every defect on it then falls inside the first tenth of the board, which no
# run of timber does.
CENTIMETRE_BENCH = "A"


def saw_board(rng, name, parcel, bench, quality):
    length = rng.randrange(1800, 4200, 100)
    width = rng.randrange(150, 401, 25)
    thick = rng.choice(NOMINALS)
    measured = thick + rng.choice((-3, -2, -1, 1, 2, 3))

    board = {
        "board": name, "parcel": parcel, "bench": bench,
        "length_mm": length, "width_mm": width,
        "thickness_mm": measured,
        "nominal_mm": thick,
        "state": "green" if rng.random() < 0.35 else "dry",
    }

    # A parcel is cut from one part of the log run, so its boards are much of a
    # muchness and the forty parcels spread right across the grades. Without
    # that the whole stock lands on one grade and naming that grade for every
    # parcel would carry the task by itself.
    # A knot is a branch. It goes THROUGH the board and shows on both faces at
    # the same place, and that is what proves how face two is booked: the book
    # takes each face from its own near edge, so a face-two figure runs the
    # other way about. The through-knots are the only evidence for it, and they
    # are not a bench's habit, so there is no clean bench to check it against.
    defects, wanes = [], []
    for face in (1, 2):
        for _ in range(max(0, rng.randint(quality - 1, quality + 1))):
            along = rng.randrange(60, length - 60)
            if bench == CENTIMETRE_BENCH:
                # He books to the nearest centimetre, so the record IS the
                # position to that resolution. Rounding here rather than when
                # the book is written means the figure can be put back exactly
                # and a solver who spots it is not punished for the remainder.
                along = (along // 10) * 10
            across = rng.randrange(20, width - 20)
            if rng.random() < 0.72:
                # a knot: markedly longer along the grain than across it, so
                # booking the two the wrong way about is both visible and
                # costly
                # Even, so that half a defect is a whole number of millimetres
                # and there is no rounding for two correct implementations to
                # differ over.
                across_mm = rng.randrange(12, 56, 2)
                along_mm = across_mm * rng.randint(3, 6)
                defects.append({
                    "board": name, "face": face, "kind": "knot",
                    "at_along_mm": along, "at_across_mm": across,
                    "along_mm": along_mm, "across_mm": across_mm,
                })
            else:
                defects.append({
                    "board": name, "face": face, "kind": "shake",
                    "at_along_mm": along, "at_across_mm": across,
                    "along_mm": rng.randrange(120, 700, 2), "across_mm": 2,
                })

    if rng.random() < 0.45:
        wanes.append({
            "board": name, "edge": rng.choice(("near", "far")),
            # Not all even. A column that comes out all-even once a correction
            # is applied is a checksum: it tells a solver the repair was right
            # without their understanding a thing.
            "lost_mm": rng.randrange(10, 60),
        })

    # Some of the knots go right through and show on the other face too.
    through = []
    for defect in list(defects):
        if defect["kind"] == "knot" and defect["face"] == 1 \
                and rng.random() < 0.38:
            through.append(dict(defect, face=2))
    defects.extend(through)

    settle_across(board, defects, wanes)
    return board, defects, wanes


def settle_across(board, defects, wanes):
    """Move any defect whose edge sits on a strip line.

    Whether a defect that just touches the line between two strips spoils the
    further one is a convention, not a fact, and a grade that turns on it would
    be unfair however well the rest is calibrated. So the sawing is arranged so
    that the question never arises.
    """
    green = board["state"] == "green"
    width = mill.dry(board["width_mm"]) if green else board["width_mm"]
    dry_wanes = [dict(w, lost_mm=mill.dry(w["lost_mm"])) for w in wanes] \
        if green else wanes
    offset, sound = mill.usable_face(dict(board, width_mm=width), dry_wanes)
    lines = [offset + step * mill.STRIP_MM
             for step in range(sound // mill.STRIP_MM + 1)]

    for defect in defects:
        for shift in (0, 3, -3, 6, -6, 9, -9, 12, -12, 15, -15):
            at = defect["at_across_mm"] + shift
            if at < 4 or at > board["width_mm"] - 4:
                continue
            centre = mill.dry(at) if green else at
            half = (mill.dry(defect["across_mm"]) if green
                    else defect["across_mm"]) // 2
            edges = (centre - half, centre + half)
            if all(abs(edge - line) >= 2
                   for edge in edges for line in lines):
                defect["at_across_mm"] = at
                break


def truth_grade(board, defects, wanes):
    """The grade the board really is, worked on the boards as sawn."""
    width = board["width_mm"]
    if board["state"] == "green":
        # the standard is written for dry boards, and everything across the
        # grain moves: the width, the wane, and where the defects sit
        width = mill.dry(width)

    dry_board = dict(board, width_mm=width)
    dry_wanes = [dict(w, lost_mm=mill.dry(w["lost_mm"])) for w in wanes] \
        if board["state"] == "green" else list(wanes)

    per_face = []
    for face in (1, 2):
        mine = [d for d in defects if d["face"] == face]
        if board["state"] == "green":
            mine = [dict(d,
                         at_across_mm=mill.dry(d["at_across_mm"]),
                         across_mm=mill.dry(d["across_mm"]))
                    for d in mine]
        area, whole = mill.face_yield(dry_board, mine, dry_wanes,
                                      board["length_mm"])
        per_face.append(mill.half_up(area * 100, whole))
    return mill.grade_of(min(per_face))


def write(outdir, parcels, boards, defects, wanes, truth):
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    with open(out / "parcels.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["parcel", "cut_for", "boards"])
        for parcel, cut_for, count in parcels:
            writer.writerow([parcel, cut_for, count])

    with open(out / "boards.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["board", "parcel", "bench", "state", "length_mm",
                         "width_mm", "thickness_mm"])
        for board in boards:
            writer.writerow([board["board"], board["parcel"], board["bench"],
                             board["state"], board["length_mm"],
                             board["width_mm"], board["thickness_mm"]])

    with open(out / "defects.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["board", "face", "kind", "at_along_mm",
                         "at_across_mm", "along_mm", "across_mm"])
        widths_of = {b["board"]: b["width_mm"] for b in boards}
        for defect in defects:
            # Each face is booked from its own near edge, and the near edge of
            # the second face is the far edge of the first.
            across = defect["at_across_mm"]
            if defect["face"] == 2:
                across = widths_of[defect["board"]] - across
            writer.writerow([defect["board"], defect["face"], defect["kind"],
                             defect["at_along_mm"], across,
                             defect["along_mm"], defect["across_mm"]])

    widths = {b["board"]: b["width_mm"] for b in boards}
    at_bench = {b["board"]: b["bench"] for b in boards}
    with open(out / "wane.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["board", "edge", "wane_mm"])
        for wane in wanes:
            lost = wane["lost_mm"]
            if at_bench[wane["board"]] == REMAINING_BENCH:
                lost = widths[wane["board"]] - lost
            writer.writerow([wane["board"], wane["edge"], lost])

    with open(out / "to_grade.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["board"])
        for board in sorted(truth):
            writer.writerow([board])

    (out / "truth.json").write_text(json.dumps(truth, indent=1), newline="\n")


def main() -> int:
    outdir = sys.argv[1] if len(sys.argv) > 1 else str(
        pathlib.Path(__file__).resolve().parent.parent / "yard")
    rng = random.Random(SEED)

    parcels, boards, defects, wanes = [], [], [], []
    grade_of = {}
    index = 0
    for number in range(1, PARCELS + 1):
        parcel = "P%02d" % number
        count = rng.randint(8, 16)
        # Kept off the floor and the ceiling: a parcel that is Sound Wormy
        # whatever you do, or Firsts whatever you do, cannot tell a solver who
        # has read the book right from one who has not, and a stock full of
        # them flatters every wrong account.
        quality = rng.randint(1, 4)
        grades = []
        for _ in range(count):
            index += 1
            # A parcel is made up over months and every bench in the mill has a
            # hand in it, so each way of booking a board runs through all forty
            # parcels rather than sitting in a corner of the stock.
            # Each bench works its own logs, so the benches do NOT cut timber
            # of the same quality. If they did, a solver could check any
            # correction by seeing whether the corrected bench's yields fell
            # back into line with the others - which is an answer key got for
            # nothing, and it is how the whole book was cracked in testing.
            bench = rng.choice(BENCHES)
            board, mine, its_wane = saw_board(
                rng, "B%04d" % index, parcel, bench,
                max(0, quality + BENCH_TIMBER[bench]))
            grade_of[board["board"]] = truth_grade(board, mine, its_wane)
            boards.append(board)
            defects.extend(mine)
            wanes.extend(its_wane)
        parcels.append((parcel, rng.choice(CUT_FOR), count))

    # The swapped bench is applied to the book, not to the boards: the timber
    # is what it is and only the writing of it is wrong.
    at_bench = {b["board"]: b["bench"] for b in boards}
    for defect in defects:
        if (at_bench[defect["board"]] == SWAPPED_BENCH
                and defect["kind"] == "knot"):
            defect["along_mm"], defect["across_mm"] = (
                defect["across_mm"], defect["along_mm"])

    for defect in defects:
        if at_bench[defect["board"]] == CENTIMETRE_BENCH:
            defect["at_along_mm"] = defect["at_along_mm"] // 10

    # Write the whole book first, with every board down for grading, so the
    # boards that go out can be chosen on what the departures actually do to
    # them rather than on hope.
    write(outdir, parcels, boards, defects, wanes, grade_of)

    import grader_ref
    right = grader_ref.run(outdir)
    if right != grade_of:
        wrong = [b for b in grade_of if right.get(b) != grade_of[b]]
        print("FAILED: the reference and the boards disagree on %d of %d"
              % (len(wrong), len(grade_of)))
        return 1

    # How many of the five departures move this board's grade if missed?
    moved = {board: 0 for board in grade_of}
    for axis, other in (("knots", "as_booked"), ("moisture", "as_measured"),
                        ("units", "as_booked"), ("wane", "as_lost"),
                        ("edge", "board_edge")):
        reading = dict(grader_ref.TRUE_READING)
        reading[axis] = other
        got = grader_ref.run(outdir, reading)
        for board in grade_of:
            if got.get(board) != grade_of[board]:
                moved[board] += 1

    # Take the boards each departure bites on, still spread evenly across the
    # grades so that naming one grade for all forty carries nothing.
    by_grade = {}
    for board, grade in sorted(grade_of.items()):
        by_grade.setdefault(grade, []).append(board)
    for grade in by_grade:
        by_grade[grade].sort(key=lambda b: (-moved[b], b))

    # NOT an even number of each grade. An evenly stratified sample is itself
    # a check: a solver can try a correction, see whether the grades come out
    # balanced, and know it is right without understanding anything. The spread
    # here is irregular, as a buyer's pull off the racks would be, but no grade
    # is allowed to be common enough for naming it everywhere to carry the task.
    names = [name for name, _ in mill.GRADES if by_grade.get(name)]
    share, left = {}, TO_GRADE
    for index, name in enumerate(names):
        room = min(len(by_grade[name]), TO_GRADE // 3)
        take = (left if index == len(names) - 1
                else rng.randint(2, max(2, min(room, left - 2 * (
                    len(names) - index - 1)))))
        share[name] = min(take, room)
        left -= share[name]
    for name in names:                       # hand back any shortfall
        while left > 0 and share[name] < min(len(by_grade[name]),
                                             TO_GRADE // 3):
            share[name] += 1
            left -= 1

    wanted = []
    for name in names:
        wanted.extend(by_grade[name][:share[name]])
    truth = {board: grade_of[board] for board in sorted(wanted)}
    bites = sum(1 for b in truth if moved[b])
    print("of the forty boards going out, %d are moved by at least one "
          "departure" % bites)

    write(outdir, parcels, boards, defects, wanes, truth)

    spread = {}
    for grade in truth.values():
        spread[grade] = spread.get(grade, 0) + 1
    print("parcels %d  boards %d  defects %d  wane %d  graded %d"
          % (len(parcels), len(boards), len(defects), len(wanes), len(truth)))
    for name, _ in mill.GRADES:
        if name in spread:
            print("  %-14s %d" % (name, spread[name]))
    print("wrote %s" % outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
