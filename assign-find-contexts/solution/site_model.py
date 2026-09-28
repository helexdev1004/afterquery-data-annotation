"""The excavation's section geometry, as the recording manual sets it out.

Everything is a whole number of centimetres inside this module - offsets along
a section, depths below site datum (positive downwards). A boundary between two
digitised points runs straight, and every comparison against it is made on
whole numbers, so two correct implementations must agree exactly and there is
no tolerance to argue about.

This one model is used three times over: gen.py lays the deposits down with
it, gates.py scores every reading of the archive with it, and the shipped
reference phases the finds with it. They cannot drift apart.
"""

from __future__ import annotations

DATUM_LEVEL_CM = 10000      # site datum stands at 100.00 m above Ordnance datum


def side_of(poly, x, z):
    """Sign of z minus the boundary's depth at x, without leaving whole numbers.

    `poly` is a run of (offset, depth) points in increasing offset. Returns a
    (numerator, denominator) pair whose ratio is z - boundary(x); denominator is
    positive. None if x is outside the run.
    """
    if x < poly[0][0] or x > poly[-1][0]:
        return None
    for (x1, z1), (x2, z2) in zip(poly, poly[1:]):
        if x1 <= x <= x2:
            if x2 == x1:
                return (z - z1, 1)
            return ((z - z1) * (x2 - x1) - (z2 - z1) * (x - x1), x2 - x1)
    return None


def below_or_on(poly, x, z):
    side = side_of(poly, x, z)
    return side is not None and side[0] >= 0


def above(poly, x, z):
    side = side_of(poly, x, z)
    return side is not None and side[0] < 0


def clearance(poly, x, z):
    """How far, in whole centimetres rounded down, z stands from the boundary."""
    side = side_of(poly, x, z)
    if side is None:
        return None
    return abs(side[0]) // side[1]


def locate(section, x, z, use_features=True):
    """The context holding the point (x, z) on one section drawing.

    `section` is {"layers": [(context, top_poly, bottom_poly), ...],
                  "features": [(context, top_poly, bottom_poly), ...]}.

    A cut feature removed whatever stood where it was dug, so a find inside a
    feature's outline belongs to the feature's fill and not to the layer the
    outline was cut through. A find lying exactly on a boundary is taken with
    the context below it: top boundaries are inclusive, bottom ones are not.
    """
    if use_features:
        for context, top, bottom in section["features"]:
            if below_or_on(top, x, z) and above(bottom, x, z):
                return context
    for context, top, bottom in section["layers"]:
        if below_or_on(top, x, z) and above(bottom, x, z):
            return context
    return None


def nearest_boundary(section, x, z):
    """The least clearance, in cm, from (x, z) to any boundary it could touch."""
    least = None
    for group in ("layers", "features"):
        for _, top, bottom in section[group]:
            for poly in (top, bottom):
                gap = clearance(poly, x, z)
                if gap is not None and (least is None or gap < least):
                    least = gap
    return least
