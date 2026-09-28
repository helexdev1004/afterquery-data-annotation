"""Run a tracer pulse through eight soil columns and write the scaler's dump.

    python pulse_columns.py [outdir]

The columns come first. Each of four soils is packed twice, and each replicate
pair is counted with one Geiger-Mueller tube and one sodium-iodide
scintillator. The tracer leaves a column as an inverse-Gaussian pulse on a flat
background; every true event either fires the detector or falls in the dead
time after an event that did, and the scaler counts what fired, second by
second. A Geiger tube is dead for 150 microseconds after each count, a
scintillator for 5.

Then the lab's files are written. detectors.csv says which scaler channel each
detector's cable went to; on two of the four pairs the two cables went to each
other's channels. Within a pair the two pulses arrive together and the doses
were chosen so the two recorded peaks stand equally high, so a channel's curve
says nothing about which detector fed it. What differs is second order: a
detector that is dead after every count spaces its counts out, and its counts
in a second scatter less than a Poisson count of the same size.
"""

import csv
import json
import math
import pathlib
import random
import sys

SEED = 8840217
BINS, INJECT_S = 1500, 120
DEAD_US = {"GM": 150, "NaI": 5}

COLUMNS = (
    # column, soil, length cm, flow mL/min, detector, type, residence s, peclet, recorded peak cps
    ("C1", "coarse sand", 30, 12.0, "GM-2207", "GM", 236, 38, 2350),
    ("C2", "coarse sand", 30, 12.0, "SC-0413", "NaI", 243, 35, 2350),
    ("C3", "fine sand", 30, 8.0, "SC-0398", "NaI", 402, 30, 2500),
    ("C4", "fine sand", 30, 8.0, "GM-2214", "GM", 391, 33, 2500),
    ("C5", "silt loam", 30, 5.0, "GM-2188", "GM", 618, 24, 2200),
    ("C6", "silt loam", 30, 5.0, "SC-0420", "NaI", 634, 22, 2200),
    ("C7", "sandy loam", 30, 3.5, "SC-0377", "NaI", 842, 20, 2400),
    ("C8", "sandy loam", 30, 3.5, "GM-2231", "GM", 861, 19, 2400),
)
CABLED = {"C1": 1, "C2": 2, "C3": 4, "C4": 3, "C5": 5, "C6": 6, "C7": 8, "C8": 7}
LISTED = {"C%d" % n: n for n in range(1, 9)}
HABITS = {3: "running total", 6: "per minute", 1: "late start"}
LATE_S, WRAP = 60, 65536


def pulse(t, residence, peclet):
    """Inverse-Gaussian residence-time density at t seconds after injection."""
    if t <= 0:
        return 0.0
    shape = residence * peclet / 2.0
    return math.sqrt(shape / (2 * math.pi * t ** 3)) * math.exp(
        -shape * (t - residence) ** 2 / (2 * residence ** 2 * t))


def count(rng, rates, dead_s):
    """Counts per one-second bin for true event rates `rates`, with dead time."""
    counts = [0] * len(rates)
    t, end = 0.0, float(len(rates))
    while t < end:
        here = int(t)
        gap = rng.expovariate(rates[here])
        if t + gap >= here + 1:
            t = here + 1.0                      # memoryless: start again in the next bin
            continue
        t += gap
        counts[int(t)] += 1
        t += dead_s
    return counts


def reckon(counts, dead_s, first_bin=0):
    """The note's arithmetic on one channel: (net counts, mean residence s)."""
    before = [c for i, c in enumerate(counts, first_bin) if i < INJECT_S]
    after = [(i, c) for i, c in enumerate(counts, first_bin) if i >= INJECT_S]
    true_rate = lambda c: c / (1.0 - c * dead_s)
    background = sum(true_rate(c) for c in before) / len(before)
    net = [(i + 0.5 - INJECT_S, true_rate(c) - background) for i, c in after]
    total = sum(n for _, n in net)
    return total, sum(t * n for t, n in net) / total


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "labrun"
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    sealed, cabling, blocks = {}, {}, {}

    for column, soil, length, flow, detector, kind, residence, peclet, peak in COLUMNS:
        dead_s = DEAD_US[kind] / 1e6
        residence *= rng.uniform(0.985, 1.015)
        background = rng.uniform(2.0, 6.0)
        shape = [pulse(i + 0.5 - INJECT_S, residence, peclet) for i in range(BINS)]
        true_peak = peak / (1.0 - peak * dead_s)        # what the recorded peak stands for
        dose = true_peak / max(shape)
        rates = [background + dose * s for s in shape]
        counts = count(rng, rates, dead_s)
        channel = CABLED[column]
        first = LATE_S if HABITS.get(channel) == "late start" else 0
        net, mean_s = reckon(counts[first:], dead_s, first)
        sealed[column] = [round(net, 1), round(mean_s, 2)]
        cabling[column] = dict(detector=detector, type=kind, channel=channel,
                               listed=LISTED[column], habit=HABITS.get(channel))
        blocks[channel] = counts

    lines = ["SCALER DUMP  channels=8  dwell_s=1  bins=%d" % BINS]
    for channel in range(1, 9):
        counts, habit, start = blocks[channel], HABITS.get(channel), 0
        if habit == "running total":
            total, shown = 0, []
            for c in counts:
                total = (total + c) % WRAP
                shown.append(total)
        elif habit == "per minute":
            shown = [c * 60 for c in counts]
        elif habit == "late start":
            shown, start = counts[LATE_S:], LATE_S
        else:
            shown = counts
        lines.append("[CH%d] start_s=%d values=%d" % (channel, start, len(shown)))
        for i in range(0, len(shown), 10):
            lines.append("".join("%8d" % v for v in shown[i:i + 10]))
    (outdir / "scaler.dmp").write_bytes(("\n".join(lines) + "\n").encode())

    with open(outdir / "columns.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["column", "soil", "length_cm", "flow_ml_min", "detector"])
        for c in COLUMNS:
            out.writerow([c[0], c[1], c[2], "%.1f" % c[3], c[4]])
    with open(outdir / "detectors.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["detector", "type", "dead_time_us", "scaler_channel"])
        for c in sorted(COLUMNS, key=lambda c: LISTED[c[0]]):
            out.writerow([c[4], c[5], DEAD_US[c[5]], LISTED[c[0]]])
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "cabling.json").write_bytes(json.dumps(cabling, indent=1).encode())
    print("columns %d  bins %d" % (len(COLUMNS), BINS))


if __name__ == "__main__":
    main()
