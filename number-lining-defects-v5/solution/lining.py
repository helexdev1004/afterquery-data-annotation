"""The tunnels' lining, as the asset team's note sets it out.

Everything is whole millimetres inside, and every comparison against a joint is
made exactly, so two correct implementations must agree to the ring.

This one model is used three times over: gen.py drives the tunnels with it,
gates.py scores every reading of the records with it, and the shipped reference
numbers the defects with it. They cannot drift apart.
"""

from __future__ import annotations

from fractions import Fraction

# --------------------------------------------------------------- published ---
# All of this is stated in LINING.md and none of it is in doubt.

FOOT_MM = Fraction(3048, 10)        # a foot is 0.3048 m
YARD_MM = Fraction(9144, 10)        # a yard is 0.9144 m
SEGMENTS = "ABCDEF"                 # six to a ring, two hours of the clock each


def mm(text):
    """Metres to three places, as whole millimetres, without touching a float."""
    text = text.strip()
    whole, _, part = text.partition(".")
    return int(whole or 0) * 1000 + int((part + "000")[:3])


def nearest_mm(value):
    """A Fraction of millimetres to the nearest whole one, halves up."""
    return (2 * value.numerator + value.denominator) // (2 * value.denominator)


def ring_along(joints, chainage):
    """Which ring of the tape a chainage falls in, counting from the tape's zero.

    `joints` is the tape chainage of every joint, the portal face first. Ring n
    lies between joint n-1 and joint n. A defect exactly on a joint goes to the
    ring beyond it, the one further along the tape.
    """
    for n in range(1, len(joints)):
        if joints[n - 1] <= chainage < joints[n]:
            return n
    return None


def segment(clock, looking_up_chainage):
    """The segment a clock position falls on.

    Segments are lettered clockwise looking up-chainage, A holding twelve and
    one o'clock, B two and three, and so on round. A clock position read
    looking down-chainage is the same face seen from the other side: what
    stands at three o'clock one way stands at nine the other.
    """
    hour = clock % 12
    if not looking_up_chainage:
        hour = (12 - hour) % 12
    return SEGMENTS[hour // 2]


def painted(tunnel, along, rings_a, rings_b, from_a):
    """The number painted on the ring that stands `along`-th on the tape.

    Drive A numbered its rings from portal A and drive B from portal B, each
    from 1, so a tape begun at portal A meets A-0001 first and B-0001 last, and
    a tape begun at portal B meets them the other way about.
    """
    total = rings_a + rings_b
    from_portal_a = along if from_a else total - along + 1
    if from_portal_a <= rings_a:
        return "%s-A-%04d" % (tunnel, from_portal_a)
    return "%s-B-%04d" % (tunnel, total - from_portal_a + 1)
