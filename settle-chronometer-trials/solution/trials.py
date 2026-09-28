"""Settle every chronometer's trial number off the comparison book.

The reference. It reads only what ships to the agent - the sheets, the two
tables and the certificates - and writes the answer on standard output.

The observatory's method is published and gives the whole arithmetic. Four
things it worked to are not in it, and each changes the answer:

1. `pos` is the position the instrument lay in, and its rate depends on it.
   The variation is meant to measure steadiness, so the part of each rate that
   belongs to its position is taken off first - each rate less the mean rate of
   its own position - before the steps are measured.
2. A comparison is sometimes missed, so an interval is two days rather than
   one. The rate is a rate a day, so such an interval is divided by two, and it
   stands for two days when the mean is taken.
3. An instrument put into a held week takes two days to come to the new
   temperature. Those days are left out of the coefficient.
4. The variation is taken over the ordinary-temperature days only. Nothing in
   the sheets shows this; it is the certificated instruments that settle it,
   and it is the only reading of the four that reproduces all eight.

Nothing is hardcoded about when the held weeks fall: they are the runs where
the chamber thermometer stands away from the ordinary reading.
"""

from __future__ import annotations

import collections
import csv
import datetime
import pathlib

APP = pathlib.Path("/app")
SETTLING_DAYS = 2


def half_up(numerator: int, denominator: int) -> int:
    """Divide to the nearest whole hundredth, a half away from zero."""
    if denominator < 0:
        numerator, denominator = -numerator, -denominator
    if numerator >= 0:
        return (2 * numerator + denominator) // (2 * denominator)
    return -((-2 * numerator + denominator) // (2 * denominator))


def load():
    with open(APP / "chronometers.csv", newline="") as fh:
        kit = {r["chronometer"]: r for r in csv.DictReader(fh)}
    with open(APP / "standard.csv", newline="") as fh:
        standard = {datetime.date.fromisoformat(r["date"]): int(r["rate"])
                    for r in csv.DictReader(fh)}
    sheets = {}
    for name in kit:
        with open(APP / "sheets" / f"{name}.csv", newline="") as fh:
            sheets[name] = [{
                "date": datetime.date.fromisoformat(r["date"]),
                "against": int(r["against_standard"]),
                "thermometer": int(r["thermometer"]),
                "pos": int(r["pos"]),
            } for r in csv.DictReader(fh)]
    return kit, standard, sheets


def ordinary_temperature(sheets) -> int:
    """The temperature the room ordinarily stood at: the commonest reading."""
    counted = collections.Counter(row["thermometer"]
                                  for rows in sheets.values() for row in rows)
    return counted.most_common(1)[0][0]


def held_runs(rows, ordinary: int) -> dict:
    """For each date in a held week, how many days into that week it is.

    A held week is a run of comparisons whose thermometer stands away from the
    ordinary reading. Nothing is assumed about when they fall.
    """
    into: dict = {}
    run: list = []
    for row in rows + [None]:
        if row is not None and row["thermometer"] != ordinary:
            run.append(row)
            continue
        for position, member in enumerate(run):
            into[member["date"]] = position
        run = []
    return into


def rates(rows, standard):
    out = []
    for before, after in zip(rows, rows[1:]):
        days = (after["date"] - before["date"]).days
        moved = after["against"] - before["against"]
        put_back = sum(
            standard.get(before["date"] + datetime.timedelta(days=k), 0)
            for k in range(days))
        out.append({"rate": half_up(moved + put_back, days), "days": days,
                    "pos": after["pos"], "thermometer": after["thermometer"],
                    "date": after["date"]})
    return out


def trial_number(rows, standard, ordinary: int) -> int:
    series = rates(rows, standard)
    into = held_runs(rows, ordinary)

    total = sum(step["rate"] * step["days"] for step in series)
    span = sum(step["days"] for step in series)
    mean = half_up(total, span)

    # The variation measures how steady the instrument is, so the part of a
    # rate that belongs to the position it lay in is taken off first: each
    # rate has the mean rate of its own position subtracted. Nothing in the
    # method asks for a per-position mean and no straightforward engine would
    # compute one.
    ordinary_days = [s for s in series if s["date"] not in into]
    by_position = {}
    for step in ordinary_days:
        by_position.setdefault(step["pos"], []).append(step["rate"])
    centre = {pos: half_up(sum(seen), len(seen))
              for pos, seen in by_position.items()}
    levelled = [s["rate"] - centre[s["pos"]] for s in ordinary_days]
    steps = [abs(b - a) for a, b in zip(levelled, levelled[1:])]
    variation = half_up(sum(steps), len(steps)) if steps else 0

    buckets: dict = {}
    for step in series:
        if step["date"] not in into or into[step["date"]] < SETTLING_DAYS:
            continue
        which = "warm" if step["thermometer"] > ordinary else "cold"
        buckets.setdefault(which, []).append((step["rate"], step["thermometer"]))

    coefficient = 0
    if "cold" in buckets and "warm" in buckets:
        def mean_of(which, index):
            seen = [pair[index] for pair in buckets[which]]
            return half_up(sum(seen), len(seen))
        gap = mean_of("warm", 1) - mean_of("cold", 1)
        if gap:
            coefficient = half_up(mean_of("warm", 0) - mean_of("cold", 0), gap)

    return abs(mean) + 2 * variation + 10 * abs(coefficient)


def main() -> None:
    kit, standard, sheets = load()
    ordinary = ordinary_temperature(sheets)
    print("chronometer,trial_number")
    for name in sorted(kit):
        print(f"{name},{trial_number(sheets[name], standard, ordinary)}")


if __name__ == "__main__":
    main()
