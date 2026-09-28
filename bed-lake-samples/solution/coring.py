"""The lake cores, as the project's coring note sets them out.

Everything is whole millimetres inside, and every comparison against a bed
boundary is made exactly, so two correct implementations must agree to the bed.

This one model is used three times over: gen.py lays the beds down with it,
gates.py scores every reading of the records with it, and the shipped reference
places the samples with it. They cannot drift apart.
"""

from __future__ import annotations

from fractions import Fraction

# --------------------------------------------------------------- published ---
# All of this is stated in CORING.md and none of it is in doubt.

INCH_MM = Fraction(254, 10)         # an inch is 25.4 mm

# grain sizes as the loggers wrote them, finest first
GRAINS = ("clay", "silt", "very fine sand", "fine sand", "medium sand",
          "coarse sand")


def mm_from_cm(text):
    """Centimetres to one place, as whole millimetres, without a float."""
    text = text.strip()
    whole, _, part = text.partition(".")
    return int(whole or 0) * 10 + int((part + "0")[:1])


def nearest_mm(value):
    """A Fraction of millimetres to the nearest whole one, halves up."""
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def bed_at(beds, offset):
    """Which of a section's logged beds an offset along the section falls in.

    `beds` is a list of (top, base) offsets in the order logged, counting from 1.
    A sample cut exactly on a boundary goes to the bed beyond it, the one
    further along the section.
    """
    for index, (top, base) in enumerate(beds, 1):
        if top <= offset < base:
            return index
    return None


def numbered(site, beds_above, in_section, along, right_way_up):
    """A bed's number down the hole, B001 the first bed under the lake floor.

    `along` is the bed's place among the `in_section` beds logged in its
    section, counted from the section's labelled top. A section that lies the
    right way up has its first-logged bed uppermost; one that was labelled
    upside down has it lowermost.
    """
    down = along if right_way_up else in_section - along + 1
    return "%s-B%03d" % (site, beds_above + down)
