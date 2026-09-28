"""What the study's fieldwork protocol fixes, and nothing else."""

from __future__ import annotations

from fractions import Fraction

FOOT_MM = Fraction(3048, 10)
MILE_MM = 1609344
TICK_S = 10                     # the wheel logs every ten seconds
HALF_METRE = 0.5

# How raggedly a measuring wheel runs on each surface, smoothest first: the
# share by which the ground covered in ten seconds strays from the walker's
# pace. Its running total is right on all of them.
CHATTER = {"tarmac": 0.012, "stone dust": 0.028, "ballast": 0.05}
ROUGHNESS = {kind: rank for rank, kind in enumerate(CHATTER)}


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


def agrees(said, want, slack=HALF_METRE, surface=True):
    """Is '412.3 ballast' the answer wanted? The altitude within `slack`
    metres and, unless `surface` is off, the surface the same."""
    try:
        high, kind = str(said).split(None, 1)
        true_high, true_kind = str(want).split(None, 1)
        near = abs(float(high) - float(true_high)) <= slack + 1e-9
    except ValueError:
        return False
    return near and (kind == true_kind or not surface)
