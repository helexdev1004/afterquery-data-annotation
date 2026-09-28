"""What the contractor's blowing procedure fixes, and nothing else."""

from __future__ import annotations

from fractions import Fraction

FOOT_MM = Fraction(3048, 10)
WITHIN_M = 2.0                  # a distance within two metres is right

# How raggedly cable runs into each kind of duct, smoothest first: the share by
# which the length paid out in a second strays from the machine's set speed.
# The running total is right in all of them.
RAGGED = {"smoothwall": 0.012, "ribbed": 0.028, "earthenware": 0.05}
ROUGHNESS = {kind: rank for rank, kind in enumerate(RAGGED)}


def clock(text):
    """'09:41:20' -> seconds after midnight."""
    h, m, s = (int(part) for part in text.split(":"))
    return 3600 * h + 60 * m + s


def as_clock(seconds):
    return "%02d:%02d:%02d" % (seconds // 3600, seconds // 60 % 60,
                               seconds % 60)


def mm(text, unit=1000):
    """A logged figure -> whole millimetres, `unit` being its size in mm."""
    return int(round(Fraction(text) * unit))


def agrees(said, want, slack=WITHIN_M, duct=True):
    """Is '1234.5 ribbed' the answer wanted? The distance within `slack`
    metres and, unless `duct` is off, the kind of duct the same."""
    try:
        far, kind = str(said).split(None, 1)
        true_far, true_kind = str(want).split(None, 1)
        near = abs(float(far) - float(true_far)) <= slack + 1e-9
    except ValueError:
        return False
    return near and (kind == true_kind or not duct)
