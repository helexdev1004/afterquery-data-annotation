"""Out-of-band occupied hours for every zone and week.

    python rebate.py [folder]        writes folder/out_of_band.csv

`hours_out(folder, reading)` is the whole job; `reading` says, for each thing
about the trends that can differ from the agent's note, which to believe.
"""

import csv
import math
import pathlib
import statistics
import sys
from datetime import datetime

BAND = (20.0, 24.0)
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

THE_TRENDS = {"fahrenheit": "to_celsius", "hundredths": "to_degrees",
              "kelvin": "to_celsius", "points": "ask_the_restlessness"}
THE_PAPERS = {"fahrenheit": "as_written", "hundredths": "as_written",
              "kelvin": "as_written", "points": "as_listed"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "month"


def table(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def lease_hours(folder):
    """{zone: {weekday number: (from minute, to minute)}}"""
    kept = {}
    for r in table(folder / "occupancy.csv"):
        a, b = (int(r[k][:2]) * 60 + int(r[k][3:]) for k in ("from", "to"))
        kept.setdefault(r["zone"], {})[DAYS.index(r["day"])] = (a, b)
    return kept


def read_trends(folder, reading):
    """{trend: [(when, celsius)]} and {trend: habits found in its column}."""
    series, habits = {}, {}
    for path in sorted((folder / "outstations").glob("*.csv")):
        rows = table(path)
        whens = [datetime.strptime(r["logged_at"], "%Y-%m-%d %H:%M")
                 for r in rows]
        for trend in [c for c in rows[0] if c != "logged_at"]:
            values, found = [float(r[trend]) for r in rows], []
            middle = statistics.median(values)
            if middle > 1000:
                found.append("hundredths")
                if reading["hundredths"] == "to_degrees":
                    values = [v / 100.0 for v in values]
            elif middle > 200:
                found.append("kelvin")
                if reading["kelvin"] == "to_celsius":
                    values = [v - 273.15 for v in values]
            elif middle > 45:
                found.append("fahrenheit")
                if reading["fahrenheit"] == "to_celsius":
                    values = [(v - 32) * 5 / 9 for v in values]
            series[trend], habits[trend] = list(zip(whens, values)), found
    return series, habits


def is_kept(hours, when):
    span = hours.get(when.weekday())
    return span is not None and span[0] <= when.hour * 60 + when.minute < span[1]


def restlessness(series):
    """How far each reading stands from the mean of its two neighbours."""
    v = [x for _, x in series]
    return [0.0] + [abs(v[i] - (v[i - 1] + v[i + 1]) / 2.0)
                    for i in range(1, len(v) - 1)] + [0.0]


def whose_hours(series, kept):
    """For each zone, how much more restless the trend is inside that zone's
    lease hours than outside them, as a log ratio of middles."""
    restless = restlessness(series)
    out = {}
    for zone, hours in kept.items():
        inside = [r for (when, _), r in zip(series, restless)
                  if is_kept(hours, when)]
        outside = [r for (when, _), r in zip(series, restless)
                   if not is_kept(hours, when)]
        out[zone] = math.log(max(statistics.median(inside), 1e-3)
                             / max(statistics.median(outside), 1e-3))
    return out


def hours_out(folder, reading):
    """{'Z01/1': hours} and what was found about each trend."""
    folder = pathlib.Path(folder)
    kept = lease_hours(folder)
    listed = {r["trend"]: r["zone"] for r in table(folder / "points.csv")}
    trends, habits = read_trends(folder, reading)
    seen = {t: dict(habits=habits[t], listed=listed[t]) for t in listed}
    serves = dict(listed)
    if reading["points"] == "ask_the_restlessness":
        fit = {t: whose_hours(s, kept) for t, s in trends.items() if s}
        pairs = sorted(((fit[t][z], t, z) for t in fit for z in kept),
                       reverse=True)
        serves, taken = {}, set()
        for score, t, z in pairs:                 # best fits first, one each
            if t not in serves and z not in taken:
                serves[t] = z
                taken.add(z)
        for t in listed:                          # a trend nothing was read from
            if t not in serves:
                serves[t] = listed[t] if listed[t] not in taken else                     sorted(set(kept) - taken)[0]
                taken.add(serves[t])
        for t in fit:
            others = [v for z, v in fit[t].items() if z != serves[t]]
            seen[t].update(fit=fit[t][serves[t]], next_best=max(others))
    out = {}
    for trend, zone in serves.items():
        seen[trend]["zone"] = zone
        if not trends[trend]:
            continue
        start = min(when for when, _ in trends[trend])
        start = datetime(start.year, start.month, start.day)
        for when, celsius in trends[trend]:
            week = (when - start).days // 7 + 1
            key = "%s/%d" % (zone, week)
            out.setdefault(key, 0)
            if is_kept(kept[zone], when) and not BAND[0] <= celsius <= BAND[1]:
                out[key] += 1
    step_h = 2 / 60.0
    return {k: round(n * step_h, 2) for k, n in out.items()}, seen


if __name__ == "__main__":
    where = base()
    answer, _ = hours_out(where, THE_TRENDS)
    with open(where / "out_of_band.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["zone", "week", "hours"])
        for key in sorted(answer):
            zone, week = key.split("/")
            sheet.writerow([zone, week, "%.2f" % answer[key]])
    print("%d lines written" % len(answer))
