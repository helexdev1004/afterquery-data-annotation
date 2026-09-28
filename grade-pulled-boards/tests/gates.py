"""Every way of getting the grades without doing the work, scored.

    python gates.py

Four submissions of an earlier task were lost to accounts nobody had scored:
a heuristic that read the answer off the geometry, a robust statistic that
stepped around a defect, and finally a consistency check that WAS the answer
key. So this scores, in one place:

  * the account a solver gets by applying the standard to the book as written;
  * every combination of the four departures, so no single one is decoration;
  * the crude repairs - a different dedupe tolerance, a different test for the
    swapped bench - that cost no understanding;
  * guessing, both the commonest grade and the commonest grade of a parcel's
    own boards;
  * and whether the records admit any consistency test at all, because if they
    do the task can be searched rather than worked.

Nothing ships until every one of them is well under the bar.
"""

from __future__ import annotations

import collections
import itertools
import json

import grader_ref
import mill

YARD, SEALED = grader_ref.places()

WAYS = {
    "knots": ("unswap", "as_booked"),
    "moisture": ("to_dry", "as_measured"),
    "units": ("to_mm", "as_booked"),
    "wane": ("as_remaining", "as_lost"),
    "edge": ("sound_edge", "board_edge"),
    "faces": ("own_edge", "one_frame"),
}


def main() -> int:
    truth = json.loads((SEALED / "truth.json").read_text())
    full = len(truth)

    def score(got):
        return sum(1 for p in truth if got.get(p) == truth[p])

    marks = {}
    for combo in itertools.product(*(WAYS[k] for k in WAYS)):
        reading = dict(zip(WAYS, combo))
        marks[combo] = score(grader_ref.run(YARD, reading))

    right = tuple(grader_ref.TRUE_READING[k] for k in WAYS)
    print("  " + "".join("%-13s" % name for name in WAYS) + " score")
    for combo, mark in sorted(marks.items(), key=lambda kv: -kv[1]):
        flag = "   <- the whole account" if combo == right else ""
        print("  " + "".join("%-13s" % part for part in combo)
              + " %2d of %d%s" % (mark, full, flag))

    best_wrong = max(v for k, v in marks.items() if k != right)
    faults = []

    print()
    book = grader_ref.load(YARD)
    spread = collections.Counter(truth.values())
    commonest = spread.most_common(1)[0]
    print("naming %s for every parcel gets %d of %d"
          % (commonest[0], commonest[1], full))

    # Does anything in the records give the grade away without the work? The
    # obvious suspects are the things a board carries for other reasons: how
    # many defects are on it, its size, its bench, what its parcel was cut for.
    parcel_of = {row["board"]: row["parcel"] for row in book["boards"]}
    use_of = {row["parcel"]: row["cut_for"] for row in book["parcels"]}
    count_of = collections.Counter(row["board"] for row in book["defects"])

    def by_key(key):
        groups = collections.defaultdict(collections.Counter)
        for board in truth:
            groups[key(board)][truth[board]] += 1
        return sum(c.most_common(1)[0][1] for c in groups.values())

    leak = max(
        by_key(lambda b: use_of[parcel_of[b]]),
        by_key(lambda b: count_of[b] // 3),
        by_key(lambda b: next(r["bench"] for r in book["boards"]
                              if r["board"] == b)),
    )
    print("the best guess from what a board carries anyway gets %d of %d"
          % (leak, full))

    # Nothing may sit ON a line the grader has to decide. A defect edge exactly
    # at a strip boundary, or a clear run exactly at the least cutting, makes
    # the grade turn on a convention rather than on the records - which is the
    # hidden-contract failure however well the rest is calibrated.
    boards, defects, wanes = grader_ref.build(YARD, grader_ref.TRUE_READING)
    wane_of = {}
    for wane in wanes:
        wane_of.setdefault(wane["board"], []).append(wane)
    on_face = {}
    for defect in defects:
        on_face.setdefault((defect["board"], defect["face"]), []).append(defect)

    tight_edge, tight_run = [], []
    for name in truth:
        board = boards[name]
        its_wane = wane_of.get(name, [])
        width = board["width_mm"]
        mine = on_face
        if board["state"] == "green":
            width = mill.dry(width)
            its_wane = [dict(w, lost_mm=mill.dry(w["lost_mm"]))
                        for w in its_wane]
        dry_board = dict(board, width_mm=width)
        offset, sound = mill.usable_face(dry_board, its_wane)
        lines = [offset + s * mill.STRIP_MM
                 for s in range(sound // mill.STRIP_MM + 1)]
        for face in (1, 2):
            here = mine.get((name, face), [])
            if board["state"] == "green":
                here = [dict(d, at_across_mm=mill.dry(d["at_across_mm"]),
                             across_mm=mill.dry(d["across_mm"]))
                        for d in here]
            for defect in here:
                _, (c0, c1) = mill.blocked(defect)
                for line in lines:
                    if min(abs(c0 - line), abs(c1 - line)) < 2:
                        tight_edge.append(name)

    # The through-knots must SETTLE which way the second face runs, or that
    # boundary is a guess and the task is a hidden contract. A knot goes
    # through the board, so the same knot stands on both faces: the pairs line
    # up under one reading and under no other.
    widths = {row["board"]: int(row["width_mm"]) for row in book["boards"]}
    ones, twos = {}, {}
    for row in book["defects"]:
        if row["kind"] != "knot":
            continue
        key = (row["board"], row["at_along_mm"], row["along_mm"],
               row["across_mm"])
        (ones if row["face"] == "1" else twos).setdefault(key, []).append(
            int(row["at_across_mm"]))

    lined_up, mirrored = 0, 0
    for key, firsts in ones.items():
        for second in twos.get(key, []):
            for first in firsts:
                if abs(first - second) <= 2:
                    lined_up += 1
                if abs((widths[key[0]] - second) - first) <= 2:
                    mirrored += 1

    print()
    print("knots standing on both faces: %d line up read the same way about, "
          "%d read the other way about" % (lined_up, mirrored))
    if mirrored < 20 or lined_up * 3 > mirrored:
        faults.append("the through-knots do not settle which way the second "
                      "face is booked, so that reading is a guess")

    print("defect edges sitting on a strip line: %d" % len(set(tight_edge)))
    if tight_edge:
        faults.append("a defect edge sits on a strip line, so whether it "
                      "blocks that strip is a convention and not a fact")

    print("the whole account grades          %d of %d" % (marks[right], full))
    print("the best account that is not it   %d of %d" % (best_wrong, full))

    bar = full - 4
    if marks[right] != full:
        faults.append("the whole account does not grade every parcel")
    if best_wrong >= bar:
        faults.append("an account that gets a departure wrong clears the bar")
    if commonest[1] >= bar or leak >= bar:
        faults.append("guessing clears the bar")

    print()
    print("bar %d of %d - %d clear of the best wrong account"
          % (bar, full, bar - best_wrong))
    if faults:
        print()
        for fault in faults:
            print("FAILED: %s" % fault)
        return 1
    print("no account that skips the work comes near it")

    (SEALED / "gates.json").write_text(json.dumps({
        "full": full, "bar": bar, "best_wrong": best_wrong,
        "as_booked": marks[tuple(
            "as_booked as_measured as_booked as_lost board_edge "
            "one_frame".split())],
        "commonest": commonest[1], "commonest_grade": commonest[0],
        "by_use": leak,
        "mirrored": mirrored, "lined_up": lined_up,
        "face_cost": full - marks[tuple(
            "unswap to_dry to_mm as_remaining sound_edge one_frame".split())],
        "marks": {" ".join(k): v for k, v in sorted(marks.items())},
    }, indent=1), newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
