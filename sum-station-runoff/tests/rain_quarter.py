"""A wet quarter in the catchment, then the stage loggers' files.

    python rain_quarter.py [outdir]

The streams come first: the same storms cross all eight stations, each stream
rises and falls in its own way, and a station's monthly runoff is its true
stage put through its own rating and summed. Then the logger files are written,
each by its own logger. The field sheet says which file came from which
station; for two pairs of stations the loggers went back into each other's
housings after the last download, and the sheet was filled in from the housing
labels.

Each crossed pair shares a gauge zero and much the same range of stage, so a
file's level says nothing. What differs is the control. A logger in the
stilling well behind a weir sees flat water; one in a rated natural section
sees the surge of the riffle, and its stage is restless from one reading to the
next. The station list says which kind of control each station has, because
each kind is rated by its own formula.
"""

import csv
import json
import math
import pathlib
import random
import sys
from datetime import datetime, timedelta

SEED = 5099019
BEGINS = datetime(2027, 1, 1)
STEPS, EVERY_MIN = 90 * 96, 15

STATIONS = (
    # station, control, coefficient, exponent, gauge zero m, file really from it, habit
    ("G1", "weir", 1.38, 2.5, 0.000, "L1", None),
    ("G2", "section", 3.10, 1.9, 0.120, "L5", None),
    ("G3", "weir", 1.38, 2.5, 0.000, "L3", "centimetres"),
    ("G4", "section", 5.60, 1.7, 0.250, "L8", None),
    ("G5", "weir", 1.42, 2.5, 0.120, "L2", "millimetres"),
    ("G6", "section", 4.20, 1.8, 0.080, "L6", "negative"),
    ("G7", "section", 2.70, 2.0, 0.050, "L7", None),
    ("G8", "weir", 1.35, 2.5, 0.250, "L4", None),
)
RESTLESS_M = {"weir": 0.0006, "section": 0.0045}
CONTROL_NAME = {"weir": "v-notch weir", "section": "natural riffle"}


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "catchment"
    (outdir / "stage_logs").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    # the storms every station sees
    storms, t = [], rng.uniform(1, 4) * 96
    while t < STEPS:
        storms.append((t, rng.uniform(0.3, 1.0)))
        t += rng.expovariate(1 / (5.5 * 96))
    sealed, housings = {}, {}
    for name, control, coeff, power, zero, log_file, habit in STATIONS:
        base = rng.uniform(0.16, 0.22)                  # head over the control, m
        gain = rng.uniform(0.35, 0.5)
        rise, fall = rng.uniform(6, 14), rng.uniform(90, 170)   # in steps
        lag = rng.uniform(2, 10)
        wander, fuss = 0.0, 0
        rows, month_sum = [], {}
        for i in range(STEPS):
            head = base
            for at, size in storms:
                dt = i - at - lag
                if dt > 0:
                    head += gain * size * (1 - math.exp(-dt / rise)) \
                        * math.exp(-dt / fall)
            wander = 0.97 * wander + rng.gauss(0, 0.0004)
            if fuss:
                fuss -= 1
            elif rng.random() < 1 / 700.0:
                fuss = rng.randrange(3, 12)             # debris, a gust, a sheep
            noisy = head + wander + rng.gauss(0, RESTLESS_M[control]) \
                + (rng.gauss(0, 0.006) if fuss else 0.0)
            stage = round(zero + max(noisy, 0.02), 3)
            when = BEGINS + timedelta(minutes=EVERY_MIN * i)
            q = coeff * (stage - zero) ** power                  # m3/s
            key = when.strftime("%Y-%m")
            month_sum[key] = month_sum.get(key, 0.0) + q * EVERY_MIN * 60
            rows.append((when, stage))
        for key, volume in month_sum.items():
            sealed["%s/%s" % (name, key)] = round(volume / 1000.0, 1)
        with open(outdir / "stage_logs" / (log_file + ".csv"), "w",
                  newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            out.writerow(["time", "stage"])
            for when, stage in rows:
                if habit == "centimetres":
                    shown = "%.1f" % (stage * 100)
                elif habit == "millimetres":
                    shown = "%d" % round(stage * 1000)
                elif habit == "negative":
                    shown = "%.3f" % -stage
                else:
                    shown = "%.3f" % stage
                out.writerow([when.strftime("%Y-%m-%d %H:%M"), shown])
        housings[name] = dict(control=control, file=log_file, habit=habit)

    with open(outdir / "stations.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["station", "control", "coefficient", "exponent",
                      "gauge_zero_m"])
        for s in STATIONS:
            # a V-notch needs no fitted exponent: the note gives the weir formula
            out.writerow([s[0], CONTROL_NAME[s[1]], "%.2f" % s[2],
                          "" if s[1] == "weir" else "%.1f" % s[3],
                          "%.3f" % s[4]])
    with open(outdir / "field_sheet.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["logger_file", "station", "downloaded"])
        for n, s in enumerate(STATIONS, 1):
            out.writerow(["L%d" % n, s[0], "2027-04-0%d" % (1 + n % 2)])
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "housings.json").write_bytes(json.dumps(housings, indent=1).encode())
    print("stations %d  readings %d  lines %d"
          % (len(STATIONS), STEPS * len(STATIONS), len(sealed)))


if __name__ == "__main__":
    main()
