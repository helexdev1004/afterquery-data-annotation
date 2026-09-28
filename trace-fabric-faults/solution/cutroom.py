"""The cutting room, as its procedure sets it out.

Everything is whole centimetres inside, and every comparison against a cut
line is made exactly, so two correct implementations must agree to the panel.

This one model is used three times over: gen.py lays the rolls up with it,
gates.py scores every reading of the records with it, and the shipped reference
traces the faults with it. They cannot drift apart.
"""

from __future__ import annotations

from fractions import Fraction

# --------------------------------------------------------------- published ---
# All of this is stated in PROCEDURE.md and none of it is in doubt.

YARD_CM = Fraction(9144, 100)   # a yard is 0.9144 m
INCH_CM = Fraction(254, 100)    # an inch is 25.4 mm
SELVEDGE_CM = 2                 # trimmed off each selvedge, never in a panel


def cm(text):
    """Metres to two places, as whole centimetres, without touching a float."""
    text = text.strip()
    whole, _, part = text.partition(".")
    return int(whole or 0) * 100 + int((part + "00")[:2])


def nearest_cm(value):
    """A Fraction of centimetres to the nearest whole one, halves up."""
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def panel_at(panels, along, across):
    """The panel a point of the lay falls in, or None if it falls in waste.

    `panels` is a list of (panel, along_from, along_to, across_from, across_to).
    A point on a cut line goes to the panel beyond it: the one further along
    the lay, or further across it.
    """
    for panel, a0, a1, c0, c1 in panels:
        if a0 <= along < a1 and c0 <= across < c1:
            return panel
    return None


def to_lay(along, across, length, width, tail_first):
    """A position on the roll as inspected, carried onto the lay.

    Both are booked the same way: along from the end that comes first, and
    across from the selvedge on the left looking along from that end, face up.
    A roll laid up head first keeps its figures. One laid up tail first has been
    turned end for end, which turns it side for side as well.
    """
    if tail_first:
        return length - along, width - across
    return along, across
