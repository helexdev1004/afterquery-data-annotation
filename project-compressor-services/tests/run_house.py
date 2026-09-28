"""A fortnight in the compressor house, then the power monitor's log of it.

    python run_house.py [outdir]

The machines come first: each of eight compressors starts, runs and stops as
the factory's demand has it, and its running hours, its starts and the date its
next service falls due are taken from what it really did. Then the power
monitor's log is written, channel by channel. The wiring schedule says channel
n is compressor n; for two pairs of machines the current transformers were
landed on each other's terminals when the monitor was fitted.

Each crossed pair is two machines of one rating, so a channel's level says
nothing, and every machine is started and stopped by the same sequencer, so its
pattern of running says nothing either. What differs is the kind of machine: a
piston compressor's current pulses with every stroke and a screw's is smooth,
and the asset register says which kind each machine is.
"""

import csv
import json
import pathlib
import random
import sys
from datetime import date, datetime, timedelta

SEED = 4358898
BEGINS = datetime(2027, 1, 4)
DAYS, EVERY_S = 14, 10
RUNNING_AT = 0.20                    # of full-load amps, the note's figure

MACHINES = (
    # compressor, kind, kW, full-load amps, channel really wired, channel habit
    ("K1", "screw", 75, 134.0, "CH1", "negative"),
    ("K2", "piston", 55, 99.0, "CH7", None),
    ("K3", "screw", 90, 160.0, "CH6", "milliamps"),
    ("K4", "piston", 37, 68.0, "CH4", "secondary"),
    ("K5", "screw", 110, 195.0, "CH5", None),
    ("K6", "piston", 90, 160.0, "CH3", None),
    ("K7", "screw", 55, 99.0, "CH2", None),
    ("K8", "piston", 75, 134.0, "CH8", None),
)
RIPPLE = {"screw": 0.006, "piston": 0.045}       # of full-load amps, line to line
INTERVAL = {"screw": 4000, "piston": 6000}       # running hours / starts
CT_RATIO = {"CH4": (100, 5)}


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "house"
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    steps = DAYS * 86400 // EVERY_S
    columns, sealed, register = {}, {}, []

    for name, kind, kw, fla, channel, habit in MACHINES:
        level, wander, fuss = rng.uniform(0.62, 0.92), 0.0, 0
        running, left = False, rng.randrange(20, 400)
        amps, hours, starts = [], 0.0, 0
        for i in range(steps):
            left -= 1
            if left <= 0:                          # the sequencer's call
                running = not running
                left = int(rng.expovariate(1 / 420.0) + 30) if running \
                    else int(rng.expovariate(1 / 300.0) + 20)
                if running:
                    starts += 1
            if running:
                wander = 0.99 * wander + rng.gauss(0, 0.004)
                if fuss:
                    fuss -= 1
                elif rng.random() < 1 / 900.0:
                    fuss = rng.randrange(5, 25)
                a = fla * (level + wander + rng.gauss(0, RIPPLE[kind])
                           + (rng.gauss(0, 0.05) if fuss else 0.0))
                a = max(a, 0.35 * fla)
                hours += EVERY_S / 3600.0
            else:
                a = abs(rng.gauss(0, 0.004)) * fla
            amps.append(a)
        columns[channel] = (amps, habit)

        used = rng.uniform(0.35, 0.8) * INTERVAL[kind]
        last = date(2026, rng.randrange(3, 11), rng.randrange(1, 28))
        per_day = (hours if kind == "screw" else starts) / DAYS
        # the last service lies as far back as that use takes at this rate
        last = BEGINS.date() - timedelta(days=round(used / per_day))
        done = (hours if kind == "screw" else starts)
        to_go = INTERVAL[kind] - used - done
        due = (BEGINS + timedelta(days=DAYS)).date() \
            + timedelta(days=round(to_go / per_day))
        sealed[name] = [round(hours, 1), starts, due.isoformat()]
        register.append([name, kind, kw, "%.1f" % fla, last.isoformat(),
                         "%.0f" % used])

    with open(outdir / "current_log.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        channels = ["CH%d" % n for n in range(1, 9)]
        out.writerow(["logged"] + channels)
        for i in range(steps):
            row = [(BEGINS + timedelta(seconds=EVERY_S * i)).strftime(
                "%Y-%m-%d %H:%M:%S")]
            for ch in channels:
                amps, habit = columns[ch]
                a = amps[i]
                if habit == "milliamps":
                    row.append("%.0f" % (a * 1000))
                elif habit == "secondary":
                    primary, secondary = CT_RATIO[ch]
                    row.append("%.3f" % (a * secondary / primary))
                elif habit == "negative":
                    row.append("%.2f" % -a)
                else:
                    row.append("%.2f" % a)
            out.writerow(row)
    with open(outdir / "asset_register.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["compressor", "kind", "rated_kw", "full_load_amps",
                      "last_service", "used_since_service"])
        out.writerows(register)
    with open(outdir / "monitor_channels.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["channel", "compressor", "ct_ratio"])
        for n in range(1, 9):
            ch = "CH%d" % n
            ratio = CT_RATIO.get(ch, (250, 5))
            out.writerow([ch, "K%d" % n, "%d/%d" % ratio])
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "terminals.json").write_bytes(json.dumps(
        {m[0]: dict(kind=m[1], channel=m[4], habit=m[5]) for m in MACHINES},
        indent=1).encode())
    print("machines %d  log lines %d" % (len(MACHINES), steps))
    for k, v in sorted(sealed.items()):
        print("  ", k, v)


if __name__ == "__main__":
    main()
