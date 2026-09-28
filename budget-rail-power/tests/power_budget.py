"""Mean bus power drawn by every rail in every phase.

    python power_budget.py [folder]        writes folder/rail_power.csv

`budget(folder, reading)` is the job; `reading` says, for each way the bench
logger's recordings can differ from the team's note, which to believe.
"""

import csv
import pathlib
import statistics
import sys

BUS_V = 5.00
PHASES = ("sleep", "idle", "active")

THE_RECORDINGS = {"millivolts": "to_volts", "microvolts": "to_millivolts",
                  "reversed": "take_the_size", "probes": "ask_the_ripple"}
THE_NOTE = {"millivolts": "as_volts", "microvolts": "as_millivolts",
            "reversed": "as_logged", "probes": "as_mapped"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "bench"


def table(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def habits_of(rows, probe, largest_mv):
    """What one probe pair's logger channel plainly does, seen under full load."""
    volts = [float(r[probe + "_v"]) for r in rows]
    sense = [float(r[probe + "_sense_mv"]) for r in rows]
    found = []
    if statistics.median(volts) > 50:
        found.append("millivolts")
    if statistics.fmean(sense) < 0:
        found.append("reversed")
    if max(abs(s) for s in sense) > 20 * largest_mv:
        found.append("microvolts")
    return found


def probe_columns(rows, probe, habits, reading):
    """(volts, sense millivolts) for one probe pair in one phase."""
    volts = [float(r[probe + "_v"]) for r in rows]
    sense = [float(r[probe + "_sense_mv"]) for r in rows]
    if "millivolts" in habits and reading["millivolts"] == "to_volts":
        volts = [v / 1000.0 for v in volts]
    if "reversed" in habits and reading["reversed"] == "take_the_size":
        sense = [abs(s) for s in sense]
    if "microvolts" in habits and reading["microvolts"] == "to_millivolts":
        sense = [s / 1000.0 for s in sense]
    return volts, sense, habits


def ripple(volts):
    return statistics.median(abs(volts[i] - (volts[i - 1] + volts[i + 1]) / 2.0)
                             for i in range(1, len(volts) - 1))


def budget(folder, reading):
    """{'RAIL/phase': milliwatts} and what each probe showed."""
    folder = pathlib.Path(folder)
    rails = {r["rail"]: r for r in table(folder / "rails.csv")}
    mapped = {r["probe"]: r["rail"] for r in table(folder / "probe_map.csv")}
    largest_mv = 60.0            # no sense resistor here drops more than this
    data, seen = {}, {}
    sheets = {phase: table(folder / ("phase_%s.csv" % phase))
              for phase in PHASES}
    habits = {probe: habits_of(sheets["active"], probe, largest_mv)
              for probe in mapped}
    for phase in PHASES:
        for probe in mapped:
            data[(probe, phase)] = probe_columns(sheets[phase], probe,
                                                 habits[probe], reading)
    for probe, rail in mapped.items():
        volts = data[(probe, "active")][0]
        seen[probe] = dict(mapped=rail, habits=data[(probe, "active")][2],
                           ripple=ripple(volts))
    clipped = dict(mapped)
    if reading["probes"] == "ask_the_ripple":
        order = sorted(seen, key=lambda p: seen[p]["ripple"])
        ldos = sum(1 for r in rails.values() if r["regulator"] == "LDO")
        for k, probe in enumerate(order):
            seen[probe]["looks"] = "LDO" if k < ldos else "buck"
        odd = [p for p in seen
               if seen[p]["looks"] != rails[mapped[p]]["regulator"]]
        for p in odd:             # its partner: the odd probe at the same voltage
            mine = rails[mapped[p]]["nominal_v"]
            for other in odd:
                if other != p and rails[mapped[other]]["nominal_v"] == mine:
                    clipped[p] = mapped[other]
    out = {}
    for probe, rail in clipped.items():
        seen[probe]["rail"] = rail
        r = rails[rail]
        mohm = float(r["sense_mohm"])
        for phase in PHASES:
            volts, sense, _ = data[(probe, phase)]
            total = 0.0
            for v, s in zip(volts, sense):
                amps = s / mohm
                if r["regulator"] == "LDO":
                    total += amps * BUS_V * 1000.0
                else:
                    total += v * amps * 1000.0 / (float(r["efficiency_pct"])
                                                  / 100.0)
            out["%s/%s" % (rail, phase)] = round(total / len(volts), 2)
    return out, seen


if __name__ == "__main__":
    where = base()
    answer, _ = budget(where, THE_RECORDINGS)
    with open(where / "rail_power.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["rail", "phase", "mean_mw"])
        for key in sorted(answer):
            rail, phase = key.split("/")
            sheet.writerow([rail, phase, "%.2f" % answer[key]])
    print("%d lines written" % len(answer))
