"""Six weeks of an irrigation trial, and what the plot loggers stored.

    python run_trial.py [outdir]

The soil comes first. Each of ten plots has its own water content, hour by
hour: irrigation and rain wet it, it drains for a day and then dries steadily
as the crop above draws on it. A probe turns water content into apparent
permittivity. A TDR probe reads the permittivity the
Topp equation expects, less a small cable offset of its own. A capacitance
probe, working at a far lower frequency in this clay loam, reads higher, which
is why the trial calibrated each one in the laboratory - and its electronics
follow the soil's temperature a little, so its reading swells by a fraction of
a per cent for every degree the soil warms in the afternoon and shrinks again
overnight. A TDR probe does not do that.

Then the files. A logger file is named by its plot, the installation sheet says
which probe went into which plot, and the probe list gives each probe's kind
and constants. In one pair of plots under the same treatment - one TDR, one
capacitance - the sheet has the two probes the wrong way round.

Nothing in a file's level gives that away: the two plots hold much the same
water, and between plots the permittivity ranges overlap freely. The daily
swell is a few parts in a thousand of the reading, inside the hour-to-hour
scatter; it shows only when the hours of many days are laid over each other,
which no mean of water content ever does.
"""

import csv
import datetime
import json
import math
import pathlib
import random
import sys

SEED = 9051742
DAYS = 42
FIRST = datetime.datetime(2026, 5, 4, 0, 0)
SWELL_PER_DEGREE = 0.0042          # a capacitance probe's reading, per degree of soil warming

PLOTS = (
    # plot, treatment, probe truly in it, habit of its logger
    ("P01", "full", "SN-4105", None),
    ("P02", "full", "SN-4262", "index"),
    ("P03", "deficit", "SN-4118", None),
    ("P04", "deficit", "SN-4277", None),
    ("P05", "rainfed", "SN-4123", None),
    ("P06", "rainfed", "SN-4290", "preamble"),
    ("P07", "deficit", "SN-4131", "hundredths"),
    ("P08", "full", "SN-4304", None),
    ("P09", "rainfed", "SN-4146", None),
    ("P10", "deficit", "SN-4315", None),
)
PROBES = {
    # serial: kind, cable offset (TDR) or laboratory slope and intercept (capacitance)
    "SN-4105": ("TDR", 0.31, None, None), "SN-4118": ("TDR", 0.18, None, None),
    "SN-4123": ("TDR", 0.42, None, None), "SN-4131": ("TDR", 0.26, None, None),
    "SN-4146": ("TDR", 0.37, None, None),
    "SN-4262": ("capacitance", None, 0.1046, -0.1630), "SN-4277": ("capacitance", None, 0.1061, -0.1702),
    "SN-4290": ("capacitance", None, 0.1038, -0.1594), "SN-4304": ("capacitance", None, 0.1055, -0.1668),
    "SN-4315": ("capacitance", None, 0.1049, -0.1641),
}
SHEET = {"P04": "SN-4131", "P07": "SN-4277"}     # what the installation sheet says, where it is wrong
WETTINGS = {"full": (3, 8, 13, 18, 23, 28, 33, 38), "deficit": (3, 13, 23, 33), "rainfed": ()}
RAIN = ((10, 0.035), (26, 0.060), (27, 0.020))


def topp(e):
    return -0.053 + 0.0292 * e - 0.00055 * e * e + 0.0000043 * e ** 3


def permittivity_for(theta):
    low, high = 1.0, 60.0
    for _ in range(60):
        mid = (low + high) / 2.0
        low, high = (mid, high) if topp(mid) < theta else (low, mid)
    return (low + high) / 2.0


def water(rng, treatment):
    theta = rng.uniform(0.22, 0.29)
    ceiling = rng.uniform(0.330, 0.355)
    thirst = {"full": 0.0165, "deficit": 0.0088, "rainfed": 0.0046}[treatment] * rng.uniform(0.9, 1.1)
    when = {day: rng.randrange(5, 21) for day in WETTINGS[treatment]}
    out = []
    for hour in range(DAYS * 24):
        day, h = divmod(hour, 24)
        if when.get(day) == h:
            theta += rng.uniform(0.07, 0.10)
        for rain_day, depth in RAIN:
            if day == rain_day and 14 <= h < 18:
                theta += depth / 4.0 * rng.uniform(0.8, 1.2)
        if theta > ceiling:
            theta -= (theta - ceiling) * 0.12                     # drainage
        # the probes sit below the main root zone: the soil there gives up its
        # water steadily, by night as by day
        theta -= thirst / 24.0 * min(1.0, max(0.0, (theta - 0.08) / 0.12))
        out.append(theta)
    return out


def soil_temperature(rng):
    bright, slow, out = 1.0, 0.0, []
    for hour in range(DAYS * 24):
        day, h = divmod(hour, 24)
        if h == 0:
            bright = rng.uniform(0.35, 1.0)
            slow = 0.8 * slow + rng.gauss(0, 0.7)
        out.append(16.5 + 0.06 * day + slow + 2.6 * bright * math.sin(2 * math.pi * (h - 11) / 24.0))
    return out


def vwc(kind, offset, slope, intercept, e):
    """The note's calibration for one reading."""
    if kind == "TDR":
        return topp(e - offset)
    return slope * math.sqrt(e) + intercept


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "trial"
    (outdir / "loggers").mkdir(parents=True, exist_ok=True)
    for old in (outdir / "loggers").glob("*"):
        old.unlink()
    rng = random.Random(SEED)
    warmth = soil_temperature(rng)
    sealed, ground = {}, {}

    for plot, treatment, serial, habit in PLOTS:
        kind, offset, slope, intercept = PROBES[serial]
        theta = water(rng, treatment)
        readings = []
        for hour, th in enumerate(theta):
            if kind == "TDR":
                e = permittivity_for(th) + offset + rng.gauss(0, 0.05)
            else:
                e = ((th - intercept) / slope) ** 2 \
                    * (1 + SWELL_PER_DEGREE * (warmth[hour] - 17.0)) + rng.gauss(0, 0.05)
            readings.append(round(e, 2))
        stored = readings
        if habit == "index":
            stored = [round(math.sqrt(e), 4) for e in readings]
            readings = [s * s for s in stored]
        values = [vwc(kind, offset, slope, intercept, e) for e in readings]
        daily = [sum(values[d * 24:(d + 1) * 24]) / 24.0 for d in range(DAYS)]
        sealed[plot] = dict(mean_vwc=round(sum(values) / len(values), 5),
                            driest_daily_vwc=round(min(daily), 5))
        ground[plot] = dict(probe=serial, kind=kind, listed=SHEET.get(plot, serial), habit=habit)

        stamps = [(FIRST + datetime.timedelta(hours=i)).strftime("%Y-%m-%d %H:%M")
                  for i in range(len(stored))]
        with open(outdir / "loggers" / (plot + ".csv"), "w", newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            if habit == "preamble":
                out.writerow(["TOA5", plot, "CR300", "OS 10.03", "trial2026"])
                out.writerow(["TIMESTAMP", "RECORD", "Ka"])
                out.writerow(["TS", "RN", ""])
                out.writerow(["", "", "Smp"])
                for i, (s, e) in enumerate(zip(stamps, stored)):
                    out.writerow([s + ":00", i, "%.2f" % e])
            elif habit == "index":
                out.writerow(["timestamp", "refractive_index"])
                for s, e in zip(stamps, stored):
                    out.writerow([s, "%.4f" % e])
            elif habit == "hundredths":
                out.writerow(["timestamp", "permittivity"])
                for s, e in zip(stamps, stored):
                    out.writerow([s, "%d" % round(e * 100)])
            else:
                out.writerow(["timestamp", "permittivity"])
                for s, e in zip(stamps, stored):
                    out.writerow([s, "%.2f" % e])

    with open(outdir / "plots.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["plot", "treatment", "probe"])
        for plot, treatment, serial, _ in PLOTS:
            out.writerow([plot, treatment, SHEET.get(plot, serial)])
    with open(outdir / "probes.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["probe", "kind", "cable_offset", "lab_slope", "lab_intercept"])
        for serial in sorted(PROBES):
            kind, offset, slope, intercept = PROBES[serial]
            out.writerow([serial, kind, "" if offset is None else "%.2f" % offset,
                          "" if slope is None else "%.4f" % slope,
                          "" if intercept is None else "%.4f" % intercept])
    (outdir / "sealed.json").write_bytes(json.dumps(sealed, indent=1, sort_keys=True).encode())
    (outdir / "ground.json").write_bytes(json.dumps(ground, indent=1).encode())
    print("plots %d  hours %d" % (len(PLOTS), DAYS * 24))


if __name__ == "__main__":
    main()
