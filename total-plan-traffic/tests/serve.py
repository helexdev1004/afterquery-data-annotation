"""Vehicles served under each plan run the signals team asked about.

    python serve.py [folder]        writes folder/plan_volumes.csv

`volumes(folder, reading)` is all of it. `reading` names, for each thing a
detector file can have different from the team's note, whose word to take.
"""

import bisect
import csv
import pathlib
import re
import statistics
import sys
from datetime import datetime

EVERY_S = 20
ZERO = datetime(2026, 1, 1)
REACH_MIN = 90

AS_FOUND = {"rate": "back_to_counts", "lanes": "add_them",
            "dayfirst": "day_then_month", "clock": "ask_the_bunching"}
AS_NOTED = {"rate": "as_counts", "lanes": "first_column",
            "dayfirst": "month_then_day", "clock": "as_stamped"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "town"


def seconds(text, pattern="%Y-%m-%d %H:%M:%S"):
    return (datetime.strptime(text, pattern) - ZERO).total_seconds()


def bookings(folder):
    """{junction: [(when, run, plan)]} from the control system's event log."""
    out = {}
    line = re.compile(r"(\S+) \| (\S+) \| run (\S+) \| plan (\S+) selected")
    for text in (folder / "controller.log").read_text().splitlines():
        when, junction, run, plan = line.match(text).groups()
        out.setdefault(junction, []).append(
            (seconds(when, "%Y-%m-%dT%H:%M:%S"), run, plan))
    return out


def streets(folder):
    """{junction: detector file stem}, from the table in the team's note."""
    note = (folder / "COUNTS.md").read_text(encoding="utf-8")
    return dict(re.findall(r"^\| (J\d) \| ([a-z-]+) \|", note, re.M))


class Detector:
    """One count site's twenty-second counts on the counter's own clock."""

    def __init__(self, path, reading):
        self.habits = []
        with open(path, newline="") as handle:
            head = handle.readline()
            handle.seek(0)
            rows = list(csv.reader(handle, delimiter=";" if ";" in head
                                   else ","))[1:]
        if "/" in rows[0][0]:
            self.habits.append("dayfirst")
            day_first = reading["dayfirst"] == "day_then_month"
            pattern = "%d/%m/%Y %H:%M:%S" if day_first else "%m/%d/%Y %H:%M:%S"
            kept = []
            for r in rows:                  # a thirteenth month reads as nothing
                try:
                    kept.append((seconds(r[0], pattern), r))
                except ValueError:
                    pass
            self.times, rows = [k[0] for k in kept], [k[1] for k in kept]
        else:
            self.times = [seconds(r[0]) for r in rows]
        if len(rows[0]) == 3:
            self.habits.append("lanes")
            counts = [int(r[1]) + int(r[2]) if reading["lanes"] == "add_them"
                      else int(r[1]) for r in rows]
        else:
            counts = [int(r[1]) for r in rows]
        per_hour = 3600 // EVERY_S
        if all(c % per_hour == 0 for c in counts) and max(counts) > 500:
            self.habits.append("rate")
            if reading["rate"] == "back_to_counts":
                counts = [c // per_hour for c in counts]
        order = sorted(range(len(rows)), key=lambda i: self.times[i])
        self.times = [self.times[i] for i in order]
        self.counts = [counts[i] for i in order]

    def bunching(self):
        """For every twenty seconds, how far the count stands from the counts
        around it, squared, over what a steady stream of that size would do."""
        c, out = self.counts, []
        for i in range(len(c)):
            near = c[max(0, i - 6):i] + c[i + 1:i + 7]
            level = max(statistics.fmean(near), 0.5)
            out.append((c[i] - level) ** 2 / level)
        return out

    def between(self, a, b, fast_s):
        """Vehicles in the twenty seconds that began in [a, b) once the
        counter's clock is put back by fast_s."""
        lo = bisect.bisect_left(self.times, a + fast_s)
        hi = bisect.bisect_left(self.times, b + fast_s)
        return sum(self.counts[lo:hi])


def clock_fast_by(log, booked, reading):
    """Minutes the counter's clock is fast: the setting-back under which the
    booked plans best sort the twenty seconds by how bunched they are."""
    if reading["clock"] != "ask_the_bunching":
        return 0, {}
    ragged = [min(r, 12.0) for r in log.bunching()]
    whole = statistics.fmean(ragged)
    spread = sum((r - whole) ** 2 for r in ragged)
    times = [when for when, _, _ in booked]
    scores = {}
    for fast in range(-REACH_MIN, REACH_MIN + 1):
        sums, sizes = {}, {}
        for t, r in zip(log.times, ragged):
            k = bisect.bisect_right(times, t - fast * 60) - 1
            if k >= 0:
                plan = booked[k][2]
                sums[plan] = sums.get(plan, 0.0) + r
                sizes[plan] = sizes.get(plan, 0) + 1
        scores[fast] = sum(n * (sums[p] / n - whole) ** 2
                           for p, n in sizes.items()) / spread
    return max(scores, key=scores.get), scores


def volumes(folder, reading):
    """{run: vehicles} for the runs wanted, and what each detector showed."""
    folder = pathlib.Path(folder)
    wanted = set((folder / "runs_wanted.txt").read_text().split())
    out, seen = {}, {}
    for junction, booked in sorted(bookings(folder).items()):
        log = Detector(folder / "detectors" / (streets(folder)[junction]
                                               + ".csv"), reading)
        fast, scores = clock_fast_by(log, booked, reading)
        seen[junction] = dict(habits=log.habits, fast=fast, scores=scores,
                              log=log)
        for (a, run, _), (b, _, _) in zip(booked, booked[1:]):
            if run in wanted:
                out[run] = log.between(a, b, fast * 60)
    return out, seen


if __name__ == "__main__":
    where = base()
    answer, _ = volumes(where, AS_FOUND)
    with open(where / "plan_volumes.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["run", "vehicles"])
        for run in sorted(answer):
            sheet.writerow([run, answer[run]])
    print("%d runs counted" % len(answer))
