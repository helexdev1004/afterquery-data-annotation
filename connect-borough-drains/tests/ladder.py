"""Score every reading of the survey and derive the bar.

    python ladder.py

The three things the survey does not spell out are taken every way a competent
surveyor might take them, and each account is scored against the sealed
connections. The bar is read off this rather than chosen: it goes in the bottom
third of the band between the best wrong account and the whole one, so a solver
who has the estate right and slips on a chamber or two still carries it.
"""

from __future__ import annotations

import itertools
import json
import pathlib

import solver

YARD, SEALED = solver.places()

WAYS = {
    "gauge": ("own_channel", "as_read", "clamp"),
    "datum": ("correct_book", "as_booked"),
    "storm": ("by_sighting", "by_dosing", "drop_wet_sightings", "ignore"),
}

PLAIN = {
    "gauge": "as_read",
    "datum": "as_booked",
    "storm": "ignore",
}


def score(truth, reading):
    got = solver.run(YARD, reading)
    return sum(1 for d in truth if got.get(d) == truth[d])


def main() -> int:
    truth = json.loads((SEALED / "truth.json").read_text())
    full = len(truth)

    marks = {}
    for combo in itertools.product(*(WAYS[k] for k in WAYS)):
        reading = dict(zip(WAYS, combo))
        marks[tuple(combo)] = score(truth, reading)

    right = tuple(solver.TRUE_READING[k] for k in WAYS)
    best = max(v for k, v in marks.items() if k != right)
    print("readings scored: %d" % len(marks))
    print()
    print("  %-22s %-12s %-11s  score" % tuple(WAYS) + "")
    for combo, mark in sorted(marks.items(), key=lambda kv: -kv[1]):
        flag = "   <- the whole account" if combo == right else ""
        print("  %-22s %-12s %-11s  %2d of %d%s"
              % (combo[0], combo[1], combo[2], mark, full, flag))

    plain = score(truth, PLAIN)
    print()
    print("taking the records at face value settles %d of %d" % (plain, full))
    print("the whole account settles                %d of %d"
          % (marks[right], full))
    print("the best account that is not it settles  %d of %d" % (best, full))

    if marks[right] != full:
        print("FAILED: the whole account does not settle every connection")
        return 1
    if best >= full:
        print("FAILED: a wrong account settles them all")
        return 1

    # The reward here is bimodal by construction: the estate is settled by a
    # single constrained search, so an account that is right settles every
    # drain and one that is wrong anywhere settles very few. There is nothing
    # in between to put a bar in the middle of, and moving the bar down would
    # only let a crude account through. So the bar sits near the top, allowing
    # three slips - the shape collapse-policy used to clear both probes.
    band = full - best
    bar = full - 3
    print()
    print("the band between them is %d wide and empty, so the bar sits near the"
          % band)
    print("top: %d of %d - %d clear of the best wrong account, three slips of"
          % (bar, full, bar - best))
    print("room, and no crude account within %d of it." % (bar - best))

    summary = {
        "full": full, "plain": plain, "best_wrong": best, "bar": bar,
        "marks": {" ".join(k): v for k, v in sorted(marks.items())},
    }
    try:
        (SEALED / "ladder.json").write_text(json.dumps(summary, indent=1),
                                            newline="\n")
    except OSError:
        pass          # read-only when run from /tests; the printout is the point
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
