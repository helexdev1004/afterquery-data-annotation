"""Generate an observatory's chronometer trial, forward from chosen truth.

    python gen.py <outdir>

Forward from the truth, as the passing tasks do it: the instrument's real
behaviour is chosen first - its rate on each day, how it answers temperature,
how steady it is - and only then is the comparison book written the way that
observer wrote it. So every trial number is exact by construction rather than a
judgement made afterwards.

Everything is in hundredths of a second. No floating point anywhere.
"""

from __future__ import annotations

import csv
import datetime
import json
import os
import pathlib
import shutil
import sys

import numpy as np

SEED = int(os.environ.get("TRIAL_SEED", "20260924"))

INSTRUMENTS = 40
DAYS = 56
FIRST_DAY = datetime.date(2026, 1, 12)

# The trial runs at the ordinary temperature of the room, then a week held cold
# and a week held warm, then back. Degrees are whole numbers.
COLD_WEEK = (21, 28)        # days [21, 28)
WARM_WEEK = (35, 42)
ROOM_TEMP, COLD_TEMP, WARM_TEMP = 18, 5, 31

# Three chambers, each with a thermometer standing off the chamber by a fixed
# amount. This appears in no sheet: it is read off the certificated
# instruments. Degrees.
CHAMBERS = {"A": 0, "B": 0, "C": 0}

# Four positions a chronometer is trialled in. The sheet gives a code and the
# method never says what it is.
POSITIONS = (1, 2, 3, 4)

MAKERS = ("Arnold & Dent", "Barraud", "Dobbie McInnes", "Frodsham",
          "Kullberg", "Mercer", "Nicole Nielsen", "Poole", "Usher & Cole",
          "Victor Kullberg")

OBSERVERS = ("Aldis", "Bewley", "Crowther", "Dunthorne")
ORDINARY_HOUR = 9

# An instrument put into a held week does not answer the new temperature at
# once: it settles over the first two days. The method says to take the
# coefficient from the held weeks and does not say to leave the settling days
# out - and a natural engine takes the whole week.
SETTLING_DAYS = 2

CERTIFICATED = 8            # instruments whose trial number is already published


def half_up(numerator: int, denominator: int) -> int:
    """Divide and round halves away from zero, in whole hundredths."""
    if denominator < 0:
        numerator, denominator = -numerator, -denominator
    if numerator >= 0:
        return (2 * numerator + denominator) // (2 * denominator)
    return -((-2 * numerator + denominator) // (2 * denominator))


def chamber_temp(day: int) -> int:
    if COLD_WEEK[0] <= day < COLD_WEEK[1]:
        return COLD_TEMP
    if WARM_WEEK[0] <= day < WARM_WEEK[1]:
        return WARM_TEMP
    return ROOM_TEMP


def build(outdir: pathlib.Path) -> None:
    rng = np.random.default_rng(SEED)

    instruments = []
    for index in range(INSTRUMENTS):
        name = f"CH{index + 1:02d}"
        instruments.append({
            "name": name,
            "maker": MAKERS[int(rng.integers(len(MAKERS)))],
            "chamber": sorted(CHAMBERS)[index % len(CHAMBERS)],
            "observer": OBSERVERS[int(rng.integers(len(OBSERVERS)))],
            # The truth of the instrument, in hundredths of a second a day.
            "base_rate": int(rng.integers(-320, 321)),
            # How it answers temperature, per degree.
            "temp_coeff": int(rng.integers(-45, 46)),
            # How unsteady it is, and how much its rate depends on position.
            "wander": int(rng.integers(2, 26)),
            "position_bias": {p: int(rng.integers(-40, 41)) for p in POSITIONS},
        })

    # The standard clock has a rate of its own, published day by day. The
    # comparison book records the chronometer against the standard, so the
    # standard's rate has to be put back to get the chronometer's.
    standard_rate = {day: int(rng.integers(-18, 19)) for day in range(DAYS)}

    rows_by_instrument: dict[str, list[dict]] = {}
    for kit in instruments:
        offset = CHAMBERS[kit["chamber"]]
        hour = ORDINARY_HOUR

        # Which days the instrument was left to run through rather than wound.
        # The winding column is simply blank on those days.
        ran_through = set()
        for _ in range(int(rng.integers(2, 6))):
            day = int(rng.integers(2, DAYS - 2))
            if day - 1 not in ran_through and day + 1 not in ran_through:
                ran_through.add(day)

        position_of = {}
        current = int(rng.integers(len(POSITIONS)))
        for day in range(DAYS):
            if day % 7 == 0:
                current = (current + 1 + int(rng.integers(3))) % len(POSITIONS)
            position_of[day] = POSITIONS[current]

        # The instrument's reading against the standard, accumulated. Its rate
        # on a day depends on the chamber temperature and the position it lay
        # in, plus its own wander.
        rows = []
        accumulated = int(rng.integers(-4000, 4001))
        for day in range(DAYS):
            temp = chamber_temp(day)
            # Settling: for the first days of a held week the instrument has
            # not yet come to the new temperature, so it answers part way.
            settled = temp
            for start, _end in (COLD_WEEK, WARM_WEEK):
                if start <= day < start + SETTLING_DAYS:
                    part = (day - start + 1)
                    settled = ROOM_TEMP + (temp - ROOM_TEMP) * part // (
                        SETTLING_DAYS + 1)
            rate = (kit["base_rate"]
                    + kit["temp_coeff"] * (settled - ROOM_TEMP) // 10
                    + kit["position_bias"][position_of[day]]
                    + int(rng.integers(-kit["wander"], kit["wander"] + 1)))
            accumulated += rate - standard_rate[day]
            if day in ran_through:
                # No comparison taken that morning: the instrument ran on, and
                # the next comparison closes a two-day interval.
                continue
            rows.append({
                "day": day,
                "date": (FIRST_DAY + datetime.timedelta(days=day)).isoformat(),
                "hour": hour,
                "against_standard": accumulated,
                "thermometer": temp + offset,
                "pos": position_of[day],
            })
        rows_by_instrument[kit["name"]] = rows

    outdir.mkdir(parents=True, exist_ok=True)
    if (outdir / "sheets").is_dir():
        shutil.rmtree(outdir / "sheets")
    (outdir / "sheets").mkdir(parents=True, exist_ok=True)
    for name, rows in rows_by_instrument.items():
        with open(outdir / "sheets" / f"{name}.csv", "w", newline="",
                  encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh, lineterminator="\n",
                fieldnames=["date", "hour", "against_standard",
                            "thermometer", "pos"])
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row[k] for k in writer.fieldnames})

    with open(outdir / "chronometers.csv", "w", newline="",
              encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, lineterminator="\n",
            fieldnames=["chronometer", "maker", "chamber", "observer"])
        writer.writeheader()
        for kit in instruments:
            writer.writerow({"chronometer": kit["name"], "maker": kit["maker"],
                             "chamber": kit["chamber"],
                             "observer": kit["observer"]})

    with open(outdir / "standard.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, lineterminator="\n", fieldnames=["date", "rate"])
        writer.writeheader()
        for day in range(DAYS):
            writer.writerow({
                "date": (FIRST_DAY + datetime.timedelta(days=day)).isoformat(),
                "rate": standard_rate[day]})

    # The sealed trial numbers, written with the whole account over the sheets
    # just emitted. The instrument's real behaviour was chosen first - its rate
    # on every day - so these are exact by construction; this step only applies
    # the observatory's own arithmetic to the book as the observer wrote it.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import engine                                             # noqa: PLC0415
    kit, standard, sheets = engine.load(outdir)
    truth = {name: engine.trial_number(name, rows, kit, standard,
                                       set(engine.PRACTICES))
             for name, rows in sheets.items()}
    (outdir / "truth.json").write_text(json.dumps(truth, indent=1, sort_keys=True),
                                       encoding="utf-8", newline="\n")

    # The attested book. The observatory published certificates for some
    # instruments, and those are the only thing that settles the practices the
    # method does not state - in particular whether the held weeks belong in
    # the variation, which nothing in the sheets can show.
    certificated = [kit["name"] for kit in instruments][:CERTIFICATED]
    with open(outdir / "certificates.csv", "w", newline="",
              encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, lineterminator="\n", fieldnames=["chronometer", "trial_number"])
        writer.writeheader()
        for name in certificated:
            writer.writerow({"chronometer": name, "trial_number": truth[name]})

    print(f"certificated: {len(certificated)} instruments")
    print(f"{len(instruments)} instruments, {DAYS} days, "
          f"{sum(len(r) for r in rows_by_instrument.values())} comparisons")
    print(f"chambers {CHAMBERS}, settling days {SETTLING_DAYS}")


def main() -> None:
    build(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "yard"))


if __name__ == "__main__":
    main()
