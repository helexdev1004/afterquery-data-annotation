"""The observatory's arithmetic, with the unpublished practices as switches.

One implementation, used by three things that must never disagree: the
generator writes the sealed trial numbers with it, the ladder scores every
partial account with it, and the shipped solution is it with every practice
held. A diagnostic carrying its own copy of a rule has already reported results
a reference was not producing, twice, on an earlier task.
"""

from __future__ import annotations

import collections
import csv
import datetime
import itertools
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402

half_up = gen.half_up

YARD = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "yard"
PRACTICES = ("bias", "settling", "interval", "ordinary")


def load(yard: pathlib.Path):
    with open(yard / "chronometers.csv", newline="", encoding="utf-8") as fh:
        kit = {r["chronometer"]: r for r in csv.DictReader(fh)}
    with open(yard / "standard.csv", newline="", encoding="utf-8") as fh:
        standard = {datetime.date.fromisoformat(r["date"]): int(r["rate"])
                    for r in csv.DictReader(fh)}
    sheets = {}
    for name in kit:
        with open(yard / "sheets" / f"{name}.csv", newline="",
                  encoding="utf-8") as fh:
            sheets[name] = [{
                "date": datetime.date.fromisoformat(r["date"]),
                "against": int(r["against_standard"]),
                "thermometer": int(r["thermometer"]),
                "pos": int(r["pos"]),
            } for r in csv.DictReader(fh)]
    return kit, standard, sheets


def rates(rows, standard, practices):
    """One rate per interval between consecutive comparisons.

    Each carries the interval in days, the position it was kept in and the
    temperature it stood at, because the practices need all three.
    """
    out = []
    for before, after in zip(rows, rows[1:]):
        days = (after["date"] - before["date"]).days
        moved = after["against"] - before["against"]
        # The standard clock's own rate over the interval goes back on.
        put_back = sum(standard.get(before["date"] + datetime.timedelta(days=k), 0)
                       for k in range(days))
        total = moved + put_back
        if "interval" in practices:
            rate = gen.half_up(total, days)
        else:
            rate = total            # a natural engine divides by one day
        out.append({"rate": rate, "days": days, "pos": after["pos"],
                    "thermometer": after["thermometer"],
                    "date": after["date"]})
    return out


def held_runs(rows):
    """For each comparison in a held week, how many comparisons into it it is.

    Counted by COMPARISONS in the run, not by days on the calendar. Where a
    comparison is missing at the start of a held week the two differ, and the
    reference and the sealed truth then disagreed on one instrument by exactly
    one unit of the coefficient.
    """
    ordinary = collections.Counter(row["thermometer"] for row in rows)
    plain = ordinary.most_common(1)[0][0]
    into: dict = {}
    run: list = []
    for row in list(rows) + [None]:
        if row is not None and row["thermometer"] != plain:
            run.append(row)
            continue
        for position, member in enumerate(run):
            into[member["date"]] = (position,
                                    "warm" if member["thermometer"] > plain
                                    else "cold")
        run = []
    return into


def trial_number(name, rows, kit, standard, practices):
    series = rates(rows, standard, practices)
    if not series:
        return None

    # The mean daily rate. With the interval practice a two-day interval
    # stands for two days and is weighted so.
    if "interval" in practices:
        total = sum(step["rate"] * step["days"] for step in series)
        span = sum(step["days"] for step in series)
    else:
        total = sum(step["rate"] for step in series)
        span = len(series)
    mean = gen.half_up(total, span)

    # The variation: the mean step between consecutive rates. Kept within
    # position where that practice is held, because the `pos` column says what
    # the instrument was lying in and a rate depends on it.
    # Where the ordinary practice is held the variation is taken over the
    # ordinary-temperature days only. The method says "the mean step between
    # consecutive rates" and never says whether the held weeks belong in it;
    # nothing in the sheets settles it either, and the only thing that does is
    # the certificated instruments.
    into = held_runs(rows)
    considered = series
    if "ordinary" in practices:
        considered = [s for s in series if s["date"] not in into]
    # The variation is meant to measure how STEADY an instrument is. A rate
    # depends on the position the instrument lay in, so a change of position
    # shows up as unsteadiness that is not the instrument's fault. Where this
    # practice is held, each rate has the mean rate of its own position taken
    # off it before the steps are measured.
    #
    # This is not a switch on the natural arithmetic: it needs a per-position
    # mean rate for the instrument, which nothing in the method asks for and no
    # straightforward engine would ever compute. That is what the approved task
    # in the archive relies on - "no correct engine has to keep either
    # quantity" - and it is why a practice that is merely a direction or an
    # ordering buys nothing: the probe sweeps those.
    if "bias" in practices:
        by_position: dict = {}
        for step in considered:
            by_position.setdefault(step["pos"], []).append(step["rate"])
        centre = {pos: half_up(sum(seen), len(seen))
                  for pos, seen in by_position.items()}
        levelled = [s["rate"] - centre[s["pos"]] for s in considered]
    else:
        levelled = [s["rate"] for s in considered]
    steps = [abs(b - a) for a, b in zip(levelled, levelled[1:])]
    variation = gen.half_up(sum(steps), len(steps)) if steps else 0

    # The temperature coefficient, off the two held weeks. The thermometer
    # stands off the chamber by a fixed amount where that practice is held, and
    # the settling days at the start of a week are left out where that one is.
    offset = 0
    buckets: dict = {}
    for step in series:
        if step["date"] not in into:
            continue
        position, which = into[step["date"]]
        if "settling" in practices and position < gen.SETTLING_DAYS:
            continue
        buckets.setdefault(which, []).append(
            (step["rate"], step["thermometer"] - offset))
    coefficient = 0
    if "cold" in buckets and "warm" in buckets:
        cold_rate = gen.half_up(sum(r for r, _t in buckets["cold"]),
                                len(buckets["cold"]))
        warm_rate = gen.half_up(sum(r for r, _t in buckets["warm"]),
                                len(buckets["warm"]))
        cold_temp = gen.half_up(sum(t for _r, t in buckets["cold"]),
                                len(buckets["cold"]))
        warm_temp = gen.half_up(sum(t for _r, t in buckets["warm"]),
                                len(buckets["warm"]))
        if warm_temp != cold_temp:
            coefficient = gen.half_up(warm_rate - cold_rate,
                                      warm_temp - cold_temp)

    return abs(mean) + 2 * variation + 10 * abs(coefficient)


