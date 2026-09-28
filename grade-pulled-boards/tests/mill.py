"""The mill's grading, as the works standard sets it out.

Everything is a whole number of millimetres. The yield is carried as an exact
pair of whole numbers and rounded once, so two correct implementations must
agree exactly and there is no tolerance to argue about.

This one model is used three times over: gen.py saws the boards with it,
decidable.py proves each departure can be found, and the shipped reference
grades with it. They cannot drift apart.
"""

from __future__ import annotations

# --------------------------------------------------------------- published ---
# All of this is stated in GRADING.md and none of it is in doubt.

STRIP_MM = 75               # a cutting is one strip wide
LEAST_CUTTING_MM = 600      # and at least this long to count
SHRINK_NUM, SHRINK_DEN = 96, 100    # oak loses 4 parts in 100 across the grain

# yield per cent needed on the poorer face, best grade first
GRADES = (
    ("Firsts", 83),
    ("Seconds", 75),
    ("Selects", 67),
    ("No.1 Common", 60),
    ("No.2 Common", 50),
    ("Sound Wormy", 0),
)

# A parcel is sold on its poorest board: the buyer opens the pack and grades
# what he finds. An allowance here would be a robust statistic, and a robust
# statistic swallows exactly the mistakes the task is meant to catch.
OFF_GRADE_PER_CENT = 0


def half_up(num: int, den: int) -> int:
    if num >= 0:
        return (2 * num + den) // (2 * den)
    return -((-2 * num + den) // (2 * den))


def dry(value: int) -> int:
    """A green measurement across the grain, brought to the standard's 15%."""
    return half_up(value * SHRINK_NUM, SHRINK_DEN)


def usable_face(board, wanes):
    """Where the sound face starts, and how wide it is.

    Wane is the bark edge left along one side of a board. What is sound is the
    width less the wane at its worst point - but WHICH side the wane is on
    matters as much as how much it takes, because the cuttings are laid out
    from the sound edge. Wane on the near edge moves the whole lay-out across
    the board; wane on the far edge does not move it at all.
    """
    near = far = 0
    for wane in wanes:
        if wane["edge"] == "near":
            near = max(near, wane["lost_mm"])
        else:
            far = max(far, wane["lost_mm"])
    return near, max(0, board["width_mm"] - near - far)


def blocked(defect):
    """The run along the board a defect spoils, and the span across it.

    Every defect is booked by where its CENTRE lies, knot and shake alike, as
    the standard says. Sizes are even, so half of one is a whole number of
    millimetres and there is nothing here for two correct implementations to
    round differently.
    """
    half_along = defect["along_mm"] // 2
    half_across = defect["across_mm"] // 2
    return ((defect["at_along_mm"] - half_along,
             defect["at_along_mm"] + half_along),
            (defect["at_across_mm"] - half_across,
             defect["at_across_mm"] + half_across))


def face_yield(board, defects, wanes, sold_mm, from_edge=True):
    """The cuttings a face yields, as an exact (area, face area) pair.

    The face is laid out in strips a cutting wide, starting at the sound edge.
    In each strip the clear runs between the defects are found, and a run
    counts only if it is at least the least cutting long.

    `from_edge` false lays the strips from the board's own edge instead of the
    sound one, which is what a grader does who takes the wane off the width and
    thinks no more about it.
    """
    offset, width = usable_face(board, wanes)
    if not from_edge:
        offset = 0
    strips = width // STRIP_MM
    if strips == 0 or sold_mm <= 0:
        return 0, max(1, sold_mm * width)

    area = 0
    for strip in range(strips):
        low = offset + strip * STRIP_MM
        high = low + STRIP_MM
        spoiled = []
        for defect in defects:
            (a0, a1), (c0, c1) = blocked(defect)
            if c1 <= low or c0 >= high:
                continue
            spoiled.append((max(0, a0), min(sold_mm, a1)))
        spoiled.sort()

        at = 0
        for start, end in spoiled:
            if start > at:
                run = start - at
                if run >= LEAST_CUTTING_MM:
                    area += run * STRIP_MM
            at = max(at, end)
        if sold_mm > at and sold_mm - at >= LEAST_CUTTING_MM:
            area += (sold_mm - at) * STRIP_MM

    return area, sold_mm * width


def grade_of(per_cent: int) -> str:
    for name, needed in GRADES:
        if per_cent >= needed:
            return name
    return GRADES[-1][0]


def rank(name: str) -> int:
    for index, (grade, _) in enumerate(GRADES):
        if grade == name:
            return index
    return len(GRADES) - 1


def grade_parcel(board_grades) -> str:
    """The parcel's grade: what all but the off-grade allowance come up to.

    The boards are set out worst first and the allowance counted off, and the
    parcel takes the grade of the first board left standing.
    """
    if not board_grades:
        return GRADES[-1][0]
    worst_first = sorted(board_grades, key=rank, reverse=True)
    allowed = (len(worst_first) * OFF_GRADE_PER_CENT) // 100
    return worst_first[allowed]
