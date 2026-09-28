"""The office's earthworks note, as geometry.

A cross-section is the ground as a line of (offset, level) points, offsets in
metres from the centreline and positive to the right looking up chainage. The
template is a level formation from `left` metres left of the centreline to
`right` metres right of it, and from each edge a side slope running outward
until it meets the ground: rising at 1 in `cut_slope` where the ground at the
edge stands above formation, falling at 1 in `fill_slope` where it stands
below. Cut is the area of ground above the template, fill the area of template
above ground, both between the two points where the side slopes meet the
ground. Topsoil strip is the width of that same footprint under each kind of
land, times the depth stripped from that kind.
"""

TOPSOIL_M = {"pasture": 0.15, "woodland": 0.25, "arable": 0.30}
ROUGHEST_LAST = ("pasture", "woodland", "arable")
FOOT_M = 0.3048
AREA_WITHIN = 0.2


def ground_at(points, x):
    """Level of the ground at offset x, on the straight line between the two
    booked points either side of it."""
    for (x0, z0), (x1, z1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    raise ValueError("offset %.2f is off the section" % x)


def _meets(points, edge_x, formation, outward, run_per_rise):
    """Where the side slope from one edge of the formation meets the ground.
    `outward` is -1 for the left edge and +1 for the right. Returns (offset,
    rising) - rising is True for a cut slope."""
    rising = ground_at(points, edge_x) > formation
    grade = (1.0 / run_per_rise[rising]) * (1 if rising else -1)

    def gap(x):                 # ground above the slope line is positive
        return ground_at(points, x) - (formation + grade * abs(x - edge_x))

    inner = edge_x
    knots = [x for x, _ in points if (x - edge_x) * outward > 0]
    for outer in sorted(knots, key=lambda x: abs(x - edge_x)):
        a, b = gap(inner), gap(outer)
        if a == 0 and inner != edge_x:
            return inner, rising
        if a * b < 0 or b == 0:
            return inner + (outer - inner) * a / (a - b), rising
        inner = outer
    raise ValueError("a side slope runs off the section")


def take_off(points, formation, left, right, cut_slope, fill_slope, land):
    """(cut m2, fill m2, topsoil strip m2) at one cross-section. `land` is a
    list of (from offset, to offset, kind) across the section."""
    points = sorted(points)
    slopes = {True: cut_slope, False: fill_slope}
    toe_l, rising_l = _meets(points, -left, formation, -1, slopes)
    toe_r, rising_r = _meets(points, right, formation, +1, slopes)

    def design(x):
        if x < -left:
            return formation + (-left - x) / slopes[rising_l] \
                * (1 if rising_l else -1)
        if x > right:
            return formation + (x - right) / slopes[rising_r] \
                * (1 if rising_r else -1)
        return formation

    knots = sorted({toe_l, toe_r, -left, right}
                   | {x for x, _ in points if toe_l < x < toe_r})
    cut = fill = 0.0
    for a, b in zip(knots, knots[1:]):
        da = ground_at(points, a) - design(a)
        db = ground_at(points, b) - design(b)
        if da * db < 0:                     # ground crosses the template
            m = a + (b - a) * da / (da - db)
            parts = ((a, m, da, 0.0), (m, b, 0.0, db))
        else:
            parts = ((a, b, da, db),)
        for x0, x1, d0, d1 in parts:
            area = (d0 + d1) / 2.0 * (x1 - x0)
            if area > 0:
                cut += area
            else:
                fill -= area
    strip = 0.0
    for lo, hi, kind in land:
        width = min(hi, toe_r) - max(lo, toe_l)
        if width > 0:
            strip += width * TOPSOIL_M[kind]
    return cut, fill, strip


def agree(said, want, slack=AREA_WITHIN):
    try:
        return all(abs(float(s) - float(w)) <= slack + 1e-9
                   for s, w in zip(said, want)) and len(said) == len(want) == 3
    except (TypeError, ValueError):
        return False
