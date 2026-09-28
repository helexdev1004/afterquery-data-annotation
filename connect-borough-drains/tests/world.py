"""The estate's drainage, and the search that recovers it.

Everything is a whole number. Levels are millimetres above Ordnance datum,
distances are metres, flows are litres an hour. Nothing anywhere is a float, so
the answer is exact by construction and there is no tolerance to argue about.

The one model in this file is used three times over: gen.py builds the estate
with it, decidable.py proves the evidence admits exactly one answer, and the
shipped reference solves with it. They cannot drift apart.
"""

from __future__ import annotations

import math

# --------------------------------------------------------------- published ---
# All of this is stated in DRAINAGE.md and none of it is in doubt.

FALL_SLACKEST = 100         # a drain is laid between 1 in 100 ...
FALL_STEEPEST = 30          # ... and 1 in 30
OLD_DATUM_MM = 2740         # the old borough datum stands this far below OD


def distance(a, b) -> int:
    """Whole metres between two points, as the borough books them."""
    return int(round(math.hypot(a[0] - b[0], a[1] - b[1])))


def fall_band(length_m: int) -> tuple[int, int]:
    """The drop in millimetres a drain of this length must have."""
    return (length_m * 1000 + FALL_SLACKEST - 1) // FALL_SLACKEST, \
           (length_m * 1000) // FALL_STEEPEST


class Estate:
    """Manholes in a tree falling to one outfall, with drains hung off them."""

    def __init__(self):
        self.parent = {}                 # manhole -> the manhole it falls to
        self.invert = {}                 # manhole -> invert level, mm AOD
        self.cover = {}                  # manhole -> cover level, mm AOD
        self.at = {}                     # manhole -> (east, north)
        self.drains = {}                 # drain -> dict of its particulars

    # ---------------------------------------------------------- the tree ---
    def children(self, manhole):
        return [m for m, p in self.parent.items() if p == manhole]

    def path_down(self, manhole):
        """The manholes a flow passes through, from here to the outfall."""
        out, seen = [], set()
        while manhole is not None and manhole not in seen:
            out.append(manhole)
            seen.add(manhole)
            manhole = self.parent.get(manhole)
        return out

    def above(self, manhole):
        """Every manhole at or above this one."""
        out = [manhole]
        for child in self.children(manhole):
            out.extend(self.above(child))
        return out

    # ------------------------------------------------------- the evidence ---
    def candidates(self, drain, inverts):
        """Every manhole this drain could be laid to, on the levels alone.

        A drain falls to its manhole at between 1 in 100 and 1 in 30, as
        DRAINAGE.md states. That bounds the candidates and never, on its own,
        settles one.
        """
        out = []
        particulars = self.drains[drain]
        for manhole in self.parent:
            length = distance(particulars["at"], self.at[manhole])
            if length == 0:
                continue
            least, most = fall_band(length)
            drop = particulars["invert"] - inverts[manhole]
            if least <= drop <= most:
                out.append(manhole)
        return sorted(out)

    def gauge(self, manhole, attached):
        """What a gauge at this manhole reads: everything standing above it."""
        total = 0
        for above in self.above(manhole):
            total += sum(self.drains[d]["flow"] for d in attached.get(above, ()))
        return total


def residuals(estate, gauges, own_only=()):
    """What each manhole's own drains must come to.

    A manhole reads everything above it, so what is hung on the manhole itself
    is its own reading less the readings of the manholes that fall into it.
    This is what couples the drains: choosing a manhole for one changes what is
    left for its neighbours, and no drain can be settled on its own.

    `own_only` names the chambers whose gauge was set in the incoming channel
    rather than the outgoing one, so that it reads that chamber's own drains
    and not the whole of what stands above it. Such a gauge reads the same on
    every round - there is no spoiled round to drop and no average to take - so
    the only way past it is to notice that it reads less than the chambers
    falling into it, which nothing standing above them ever can.
    """
    own_only = set(own_only)

    def whole(manhole):
        total = gauges[manhole]
        if manhole in own_only:
            total += sum(whole(child) for child in estate.children(manhole))
        return total

    out = {}
    for manhole in estate.parent:
        if manhole in own_only:
            out[manhole] = gauges[manhole]
        else:
            out[manhole] = gauges[manhole] - sum(
                whole(child) for child in estate.children(manhole))
    return out


def solve(estate, want, cands, fixed, cap=2):
    """Every assignment of drains to manholes the evidence allows.

    Stops once `cap` answers are found - two is enough to know the evidence
    does not settle the estate, which is the thing that must never be true.
    """
    manholes = sorted(want, key=lambda m: len(
        [d for d in cands if m in cands[d] and d not in fixed]))

    by_manhole = {m: [d for d in sorted(cands)
                      if m in cands[d] and d not in fixed] for m in manholes}
    need = dict(want)
    for drain, manhole in fixed.items():
        need[manhole] -= estate.drains[drain]["flow"]

    answers = []
    taken = set()

    def place(index, chosen):
        if len(answers) >= cap:
            return
        if index == len(manholes):
            if len(taken) == len(cands) - len(fixed):
                answers.append(dict(chosen))
            return

        manhole = manholes[index]
        free = [d for d in by_manhole[manhole] if d not in taken]
        target = need[manhole]

        def pick(at, running, picked):
            if len(answers) >= cap:
                return
            if running == target:
                for drain in picked:
                    chosen[drain] = manhole
                    taken.add(drain)
                place(index + 1, chosen)
                for drain in picked:
                    del chosen[drain]
                    taken.discard(drain)
                if running == target and at >= len(free):
                    return
            if at >= len(free) or running > target:
                return
            for next_at in range(at, len(free)):
                drain = free[next_at]
                pick(next_at + 1, running + estate.drains[drain]["flow"],
                     picked + [drain])

        pick(0, 0, [])

    place(0, {})
    return answers
