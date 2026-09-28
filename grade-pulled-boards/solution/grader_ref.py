"""Grade the stock from the shipped records alone.

This reads only what the agent's container carries and never looks at the
answer. `TRUE_READING` is the account the mill worked to; the ladder scores
every other way of reading the book.
"""

from __future__ import annotations

import csv
import pathlib

import mill

TRUE_READING = {
    # One bench measures a knot across the grain and everyone else takes its
    # greatest dimension. A knot grows longer ALONG the grain, so his entries
    # come out the wrong way about and say so.
    "knots": "unswap",
    # The standard is written for boards at fifteen per cent. A green board is
    # wider than it will be, and so is its wane and the spacing of its defects.
    "moisture": "to_dry",
    # One bench's book runs in centimetres along the board. Every defect on it
    # then falls inside the first tenth of the board, which no run of timber
    # does.
    "units": "to_mm",
    # One bench books the wane as the width LEFT rather than the width lost.
    "wane": "as_remaining",
    # The book takes each face from its own near edge, and the near edge of the
    # second face is the far edge of the first. What proves it is that a knot
    # goes through the board: the same knot stands on both faces, and the pairs
    # only line up when the second face is read the other way about.
    "faces": "own_edge",
    # The cuttings are laid out from the SOUND edge, so wane on the near edge
    # moves the whole lay-out across the board. Taking the wane off the width
    # and thinking no more about it lays them out from the board's own edge.
    "edge": "sound_edge",
}


def places():
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    if (yard / "truth.json").is_file():
        return yard, yard
    return pathlib.Path("/app"), here


def load(app):
    app = pathlib.Path(app)

    def rows(name):
        with open(app / (name + ".csv"), newline="") as fh:
            return list(csv.DictReader(fh))

    return {name: rows(name) for name in
            ("parcels", "boards", "defects", "wane", "to_grade")}


def build(app, reading):
    book = load(app)

    boards = {}
    for row in book["boards"]:
        boards[row["board"]] = {
            "board": row["board"], "parcel": row["parcel"],
            "bench": row["bench"], "state": row["state"],
            "length_mm": int(row["length_mm"]),
            "width_mm": int(row["width_mm"]),
            "thickness_mm": int(row["thickness_mm"]),
        }

    defects = []
    for row in book["defects"]:
        defects.append({
            "board": row["board"], "face": int(row["face"]),
            "kind": row["kind"],
            "at_along_mm": int(row["at_along_mm"]),
            "at_across_mm": int(row["at_across_mm"]),
            "along_mm": int(row["along_mm"]),
            "across_mm": int(row["across_mm"]),
        })

    wanes = []
    for row in book["wane"]:
        wanes.append({"board": row["board"], "edge": row["edge"],
                      "lost_mm": int(row["wane_mm"])})

    # ---- which way the second face runs ------------------------------------
    if reading["faces"] == "own_edge":
        for defect in defects:
            if defect["face"] == 2:
                defect["at_across_mm"] = (boards[defect["board"]]["width_mm"]
                                          - defect["at_across_mm"])

    # ---- the swapped bench -------------------------------------------------
    if reading["knots"] == "unswap":
        # Which bench it is has to be found, not assumed. A knot is longer
        # along the grain than across it, so the bench whose knots come out
        # the other way about is the one measuring across.
        wrong = {}
        for defect in defects:
            if defect["kind"] != "knot":
                continue
            bench = boards[defect["board"]]["bench"]
            tally = wrong.setdefault(bench, [0, 0])
            tally[1] += 1
            if defect["across_mm"] > defect["along_mm"]:
                tally[0] += 1
        swapped = {b for b, (bad, all_of) in wrong.items()
                   if all_of and bad * 2 > all_of}
        for defect in defects:
            if (defect["kind"] == "knot"
                    and boards[defect["board"]]["bench"] in swapped):
                defect["along_mm"], defect["across_mm"] = (
                    defect["across_mm"], defect["along_mm"])

    # ---- the wane booked as what is left -----------------------------------
    if reading["wane"] == "as_remaining":
        by_bench = {}
        for wane in wanes:
            bench = boards[wane["board"]]["bench"]
            width = boards[wane["board"]]["width_mm"]
            by_bench.setdefault(bench, []).append(
                (wane["lost_mm"], width))
        backwards = set()
        for bench, seen in by_bench.items():
            big = sum(1 for lost, width in seen if lost * 2 > width)
            if big * 2 > len(seen):
                backwards.add(bench)
        for wane in wanes:
            if boards[wane["board"]]["bench"] in backwards:
                wane["lost_mm"] = max(
                    0, boards[wane["board"]]["width_mm"] - wane["lost_mm"])

    # ---- the bench whose book runs in centimetres ---------------------------
    if reading["units"] == "to_mm":
        # Found, not assumed: a bench whose every defect falls inside the first
        # tenth of its board is not booking millimetres.
        reach = {}
        for defect in defects:
            board = boards[defect["board"]]
            tally = reach.setdefault(board["bench"], [0, 0])
            tally[1] += 1
            if defect["at_along_mm"] * 8 < board["length_mm"]:
                tally[0] += 1
        short = {b for b, (low, all_of) in reach.items()
                 if all_of and low == all_of}
        for defect in defects:
            if boards[defect["board"]]["bench"] in short:
                defect["at_along_mm"] *= 10

    return boards, defects, wanes


def run(app, reading=None):
    reading = reading or TRUE_READING
    boards, defects, wanes = build(app, reading)

    by_board = {}
    for defect in defects:
        by_board.setdefault(defect["board"], []).append(defect)
    wane_of = {}
    for wane in wanes:
        wane_of.setdefault(wane["board"], []).append(wane)

    wanted = {row["board"] for row in load(app)["to_grade"]}
    grades = {}
    for name, board in boards.items():
        if name not in wanted:
            continue
        mine = by_board.get(name, [])
        its_wane = wane_of.get(name, [])
        width = board["width_mm"]

        if reading["moisture"] == "to_dry" and board["state"] == "green":
            width = mill.dry(width)
            its_wane = [dict(w, lost_mm=mill.dry(w["lost_mm"]))
                        for w in its_wane]
            mine = [dict(d, at_across_mm=mill.dry(d["at_across_mm"]),
                         across_mm=mill.dry(d["across_mm"])) for d in mine]

        dry_board = dict(board, width_mm=width)
        per_face = []
        for face in (1, 2):
            on_face = [d for d in mine if d["face"] == face]
            area, whole = mill.face_yield(
                dry_board, on_face, its_wane, board["length_mm"],
                from_edge=reading["edge"] == "sound_edge")
            per_face.append(mill.half_up(area * 100, whole))
        grades[name] = mill.grade_of(min(per_face))

    return grades
