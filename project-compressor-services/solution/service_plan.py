"""Running hours, starts and next service date for every compressor.

    python service_plan.py [folder]        writes folder/service_due.csv

`due(folder, reading)` is the job; `reading` says, for each thing the power
monitor's log can do differently from the planner's note, which to believe.
"""

import csv
import pathlib
import statistics
import sys
from datetime import date, datetime, timedelta

EVERY_S = 10
RUNNING_AT = 0.20
INTERVAL = {"screw": 4000.0, "piston": 6000.0}

THE_LOG = {"milliamps": "to_amps", "secondary": "through_the_ratio",
           "negative": "take_the_size", "wiring": "ask_the_ripple"}
THE_NOTE = {"milliamps": "as_amps", "secondary": "as_amps",
            "negative": "as_logged", "wiring": "as_scheduled"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "house"


def table(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def channel_amps(rows, channel, ratio, largest_fla, reading):
    """A channel's primary amps, its habits undone, and the habits found."""
    values = [float(r[channel]) for r in rows]
    habits = []
    if statistics.fmean(values) < 0:
        habits.append("negative")
        if reading["negative"] == "take_the_size":
            values = [abs(v) for v in values]
    top = max(abs(v) for v in values)
    if top > 20 * largest_fla:
        habits.append("milliamps")
        if reading["milliamps"] == "to_amps":
            values = [v / 1000.0 for v in values]
    elif top < 12:
        habits.append("secondary")
        if reading["secondary"] == "through_the_ratio":
            primary, secondary = (float(x) for x in ratio.split("/"))
            values = [v * primary / secondary for v in values]
    return values, habits


def ripple(amps):
    """The middle line-to-line unsteadiness of a channel while it runs, as a
    share of its running level."""
    high = 0.5 * max(amps)
    steps = [abs(amps[i] - (amps[i - 1] + amps[i + 1]) / 2.0)
             for i in range(1, len(amps) - 1)
             if min(amps[i - 1], amps[i], amps[i + 1]) > high]
    level = statistics.median(a for a in amps if a > high)
    return statistics.median(steps) / level


def due(folder, reading):
    """{compressor: (run_hours, starts, due date)} and what each channel showed."""
    folder = pathlib.Path(folder)
    rows = table(folder / "current_log.csv")
    assets = {r["compressor"]: r for r in table(folder / "asset_register.csv")}
    wiring = table(folder / "monitor_channels.csv")
    largest = max(float(a["full_load_amps"]) for a in assets.values())
    amps, seen = {}, {}
    for w in wiring:
        values, habits = channel_amps(rows, w["channel"], w["ct_ratio"],
                                      largest, reading)
        amps[w["channel"]] = values
        seen[w["channel"]] = dict(habits=habits, scheduled=w["compressor"],
                                  ripple=ripple([abs(v) for v in values]))
    serves = {w["channel"]: w["compressor"] for w in wiring}
    if reading["wiring"] == "ask_the_ripple":
        cut = statistics.fmean(sorted(s["ripple"] for s in seen.values())[3:5])
        for ch, s in seen.items():
            s["looks"] = "piston" if s["ripple"] > cut else "screw"
        odd = [ch for ch, s in seen.items()
               if s["looks"] != assets[s["scheduled"]]["kind"]]
        for ch in odd:        # its partner: the odd channel of the same rating
            mine = assets[seen[ch]["scheduled"]]["full_load_amps"]
            for other in odd:
                if other != ch and assets[seen[other]["scheduled"]][
                        "full_load_amps"] == mine:
                    serves[ch] = seen[other]["scheduled"]
    ends = (datetime.strptime(rows[-1]["logged"], "%Y-%m-%d %H:%M:%S")
            + timedelta(seconds=EVERY_S)).date()
    days = len(rows) * EVERY_S / 86400.0
    out = {}
    for ch, compressor in serves.items():
        seen[ch]["serves"] = compressor
        asset = assets[compressor]
        bar = RUNNING_AT * float(asset["full_load_amps"])
        on = [a >= bar for a in amps[ch]]
        hours = sum(on) * EVERY_S / 3600.0
        starts = sum(1 for a, b in zip(on, on[1:]) if b and not a)
        used = hours if asset["kind"] == "screw" else starts
        to_go = INTERVAL[asset["kind"]] - float(asset["used_since_service"]) \
            - used
        when = ends + timedelta(days=round(to_go / (used / days))) \
            if used else date.max
        out[compressor] = (round(hours, 1), starts, when.isoformat())
    return out, seen


if __name__ == "__main__":
    where = base()
    answer, _ = due(where, THE_LOG)
    with open(where / "service_due.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["compressor", "run_hours", "starts", "due_date"])
        for k in sorted(answer):
            sheet.writerow([k, "%.1f" % answer[k][0], answer[k][1], answer[k][2]])
    print("%d compressors planned" % len(answer))
