"""Which batch filled each tanker load, and its litres at 15 degC.

    python answer_customer.py [folder]     writes folder/load_batches.csv

`answer(folder, reading)` is the work. `reading` says, for each way the
terminal automation system's log can differ from the terminal's note, whether
to go by the log or by the note.
"""

import bisect
import csv
import pathlib
import re
import statistics
import sys

GALLON_L = 3.785411784
EXPANSION = 0.00084

GO_BY_THE_LOG = {"cubic_metres": "to_litres", "gallons": "to_litres",
                 "fahrenheit": "to_celsius", "meters": "ask_the_meter"}
GO_BY_THE_NOTE = {"cubic_metres": "as_litres", "gallons": "as_litres",
                  "fahrenheit": "as_celsius", "meters": "as_on_file"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "terminal"


def table(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def tickets(folder):
    """{header: ([first litre], [batch])} from the pipeline's batch tickets."""
    out, header = {}, None
    for line in (folder / "batch_tickets.txt").read_text().splitlines():
        if line.startswith("HEADER"):
            header = line.split()[1]
            out[header] = ([], [])
        elif line.strip():
            name, litres = re.match(r"\s+(\S+) from (\d+) L", line).groups()
            out[header][0].append(int(litres))
            out[header][1].append(name)
    return out


class ArmLog:
    """One arm's totaliser in litres and temperature in degC, line by line."""

    def __init__(self, rows, arm, reading):
        total = [float(r[arm + "_total"]) for r in rows]
        temp = [float(r[arm + "_temp"]) for r in rows]
        moving = [b - a for a, b in zip(total, total[1:]) if b > a]
        usual = statistics.median(moving)
        self.habits, self.unit = [], 1.0
        if usual < 5:
            self.habits.append("cubic_metres")
            if reading["cubic_metres"] == "to_litres":
                self.unit = 1000.0
        elif usual < 200:
            self.habits.append("gallons")
            if reading["gallons"] == "to_litres":
                self.unit = GALLON_L
        if statistics.median(temp) > 40:
            self.habits.append("fahrenheit")
            if reading["fahrenheit"] == "to_celsius":
                temp = [(t - 32) * 5 / 9 for t in temp]
        self.total = [v * self.unit for v in total]
        self.temp = temp

    def unsteadiness(self):
        """[(line, distance of that ten seconds' litres from its neighbours')]
        for lines in the steady middle of a load."""
        d = [b - a for a, b in zip(self.total, self.total[1:])]
        full = 0.8 * statistics.median(v for v in d if v > 0)
        return [(i + 1, abs(d[i] - (d[i - 1] + d[i + 1]) / 2.0))
                for i in range(1, len(d) - 1)
                if min(d[i - 1], d[i], d[i + 1]) > full]


def fitted_k(log, k_on_file, candidates, edges, reading):
    """The K of the meter really on the arm: the one under which the batch
    tickets best sort the meter's unsteadiness."""
    if reading["meters"] != "ask_the_meter":
        return k_on_file, {}
    marks = log.unsteadiness()
    whole = statistics.fmean(min(u, 25.0) for _, u in marks)
    scores = {}
    for k in candidates:
        sums, sizes = {}, {}
        for i, u in marks:
            through = (log.total[i] - log.total[0]) * k_on_file / k
            b = bisect.bisect_right(edges, through) - 1
            sums[b] = sums.get(b, 0.0) + min(u, 25.0)
            sizes[b] = sizes.get(b, 0) + 1
        scores[k] = sum(n * (sums[b] / n - whole) ** 2
                        for b, n in sizes.items())
    return max(scores, key=scores.get), scores


def answer(folder, reading):
    """{load: (batch, litres at 15 degC)} and what each arm's log showed."""
    folder = pathlib.Path(folder)
    rows = table(folder / "tas_log.csv")
    arms = {r["arm"]: r for r in table(folder / "arms.csv")}
    every_k = sorted({float(r["k_factor_pulses_per_l"]) for r in arms.values()})
    slips = tickets(folder)
    logs, seen = {}, {}
    for arm, facts in arms.items():
        log = ArmLog(rows, arm, reading)
        on_file = float(facts["k_factor_pulses_per_l"])
        edges, names = slips[facts["header"]]
        k, scores = fitted_k(log, on_file, every_k, edges, reading)
        logs[arm] = (log, on_file / k, edges, names)
        seen[arm] = dict(habits=log.habits, k=k, scores=scores)
    out = {}
    for load in table(folder / "loads.csv"):
        log, true_per_shown, edges, names = logs[load["arm"]]
        a, b = (float(load[c]) * log.unit for c in ("totaliser_start",
                                                    "totaliser_end"))
        lo = bisect.bisect_right(log.total, a + 0.06)
        hi = bisect.bisect_left(log.total, b - 0.06) + 1   # flowing lines only
        degc = statistics.fmean(log.temp[lo:hi] or log.temp[lo:lo + 1])
        through = (a - log.total[0]) * true_per_shown
        batch = names[bisect.bisect_right(edges, through) - 1]
        litres = (b - a) * true_per_shown * (1 - EXPANSION * (degc - 15))
        out[load["load"]] = (batch, round(litres))
    return out, seen


if __name__ == "__main__":
    where = base()
    result, _ = answer(where, GO_BY_THE_LOG)
    with open(where / "load_batches.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["load", "batch", "litres_15"])
        for load in sorted(result):
            sheet.writerow([load, result[load][0], result[load][1]])
    print("%d loads answered" % len(result))
