"""Austenitise two furnace loads, then write the logger's records of them.

    python fire_loads.py [outdir]

The furnace comes first: each of sixteen test pieces follows the load's heat-up,
soak and cool-down in its own place in the furnace, its own probe reads that
temperature with its own small error, and the piece's soak is reckoned from the
probe's reading put right by its calibration figures. Then the logger's records
are written, channel by channel. The channel schedule says which piece is on
which channel; in each load one pair of probe leads was landed on the other's
terminals, a thermocouple's on a resistance probe's channel and the other way
about.

A channel's level says nothing, because no two places in a furnace are at the
same temperature anyway. What differs is the kind of probe. A type K
thermocouple's reading jitters by a few tenths from one reading to the next; a
platinum resistance probe's is steady to a few hundredths. The piece list says
which kind each piece carries, because the two kinds are corrected differently.
"""

import csv
import json
import math
import pathlib
import random
import sys
from datetime import datetime, timedelta

SEED = 5385164
SOAK_AT_C = 840.0
EVERY_S = 10
JITTER_C = {"type K": 0.32, "Pt100": 0.025}
HABITS = {"C3": "fahrenheit", "C6": "kelvin", "C8": "tenths"}
# load -> {piece number: channel its lead is really on}; the rest are as scheduled
LANDED = {"A": {2: "C5", 5: "C2"}, "B": {3: "C7", 7: "C3"}}
KINDS = {"A": ("type K", "type K", "Pt100", "type K", "Pt100", "Pt100",
               "type K", "Pt100"),
         "B": ("Pt100", "type K", "type K", "Pt100", "type K", "Pt100",
               "Pt100", "type K")}


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "furnace"
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    sealed, pieces, schedule, wired = {}, [], [], {}

    for load, began in (("A", datetime(2027, 3, 9, 8, 12)),
                        ("B", datetime(2027, 3, 11, 13, 40))):
        steps = rng.randrange(1150, 1300)
        ramp = rng.uniform(52, 60) * 60 / EVERY_S           # steps to setpoint
        hold = rng.uniform(62, 75) * 60 / EVERY_S
        setpoint = rng.uniform(852, 858)
        # the furnace's own slow cycling and the odd disturbance, felt by all
        cycle, fuss, shared = 0.0, 0, []
        for i in range(steps):
            cycle = 0.995 * cycle + rng.gauss(0, 0.04)
            if fuss:
                fuss -= 1
            elif rng.random() < 1 / 400.0:
                fuss = rng.randrange(4, 12)
            shared.append(cycle + (rng.gauss(0, 0.6) if fuss else 0.0))
        rows = {}
        first_line = int(0.22 * ramp)
        for n, kind in enumerate(KINDS[load], 1):
            piece = "%s%d" % (load, n)
            place = rng.uniform(-7.0, 5.0)                  # this spot in the furnace
            lag = rng.uniform(8, 40)
            if kind == "type K":
                offset, scale = round(rng.uniform(1.8, 4.6), 1), ""
            else:
                offset, scale = "", round(rng.uniform(0.9958, 0.9982), 4)
            channel = LANDED[load].get(n, "C%d" % n)
            logged, soak, total = [], 0, 0.0
            for i in range(steps):
                j = max(i - lag, 0.0)
                if j < ramp:
                    body = 20 + (setpoint - 20) * (1 - math.exp(-3.2 * j / ramp)) \
                        / (1 - math.exp(-3.2))
                elif j < ramp + hold:
                    body = setpoint
                else:
                    body = 20 + (setpoint - 20) * math.exp(-(j - ramp - hold)
                                                           / 260.0)
                true_c = body + place * min(1.0, body / setpoint) + shared[i]
                # what the probe reads before its calibration is applied
                raw = true_c - offset if kind == "type K" else true_c / scale
                raw = round(raw + rng.gauss(0, JITTER_C[kind]), 2)
                corrected = raw + offset if kind == "type K" else raw * scale
                if corrected >= SOAK_AT_C:
                    soak += 1
                    total += corrected
                logged.append(raw)
            rows[channel] = logged
            sealed[piece] = [round(soak * EVERY_S / 60.0, 1),
                             round(total / soak, 1)]
            pieces.append([piece, load, kind, "TP-%d" % rng.randrange(1100, 9900),
                           offset, scale])
            schedule.append([load, "C%d" % n, piece])
            wired[piece] = dict(kind=kind, channel=channel)

        with open(outdir / ("load_%s.csv" % load), "w", newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            out.writerow(["time", "channel", "reading"])
            # the logger is started once the load is well on its way up, so
            # no two probes are ever seen at one common temperature
            for i in range(first_line, steps):
                when = (began + timedelta(seconds=EVERY_S * i)).strftime(
                    "%Y-%m-%d %H:%M:%S")
                for n in range(1, 9):
                    ch = "C%d" % n
                    v = rows[ch][i]
                    habit = HABITS.get(ch)
                    if habit == "fahrenheit":
                        shown = "%.2f" % (v * 9 / 5 + 32)
                    elif habit == "kelvin":
                        shown = "%.2f" % (v + 273.15)
                    elif habit == "tenths":
                        shown = "%d" % round(v * 100)
                    else:
                        shown = "%.2f" % v
                    out.writerow([when, ch, shown])

    with open(outdir / "pieces.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["piece", "load", "probe", "probe_serial",
                      "offset_c", "scale"])
        out.writerows(pieces)
    with open(outdir / "channel_schedule.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["load", "channel", "piece"])
        out.writerows(schedule)
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "terminals.json").write_bytes(json.dumps(wired, indent=1).encode())
    print("pieces %d" % len(sealed))
    for k in ("A2", "A5", "B3", "B7"):
        print("  ", k, sealed[k])


if __name__ == "__main__":
    main()
