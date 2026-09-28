"""Put the board through its three phases, then write the bench logger's files.

    python bench_run.py [outdir]

The board comes first: in each phase every rail carries its own current at its
own voltage, and what it draws from the 5 V bus follows from its regulator - a
linear regulator passes its load current straight through from the bus, a buck
converter draws the rail's power over its efficiency. Then the logger's
recordings are written, probe by probe. The probe map says which rail each
probe pair is clipped to; on two pairs of rails the probes were clipped to each
other's test points.

Each crossed pair is two rails of the same nominal voltage, so a probe's level
says nothing. What differs is the regulator. A buck converter's rail carries
switching ripple, several millivolts from one sample to the next; a linear
regulator's rail is flat to a fraction of a millivolt. Every rail also drifts
slowly with temperature and bus sag, and the drift is sized so that the spread
of a rail's voltage over a phase is the same whatever its regulator: only how
one sample stands to the next tells the two kinds apart.
"""

import csv
import json
import pathlib
import random
import sys

SEED = 5916079
BUS_V = 5.00
PHASES = (("sleep", 0.04), ("idle", 0.35), ("active", 1.0))
SAMPLES, EVERY_MS = 2400, 10
RIPPLE_V = {"buck": 0.0085, "LDO": 0.00035}
DRIFT_V = {"buck": 0.0085, "LDO": 0.0130}   # sized so a phase's spread is alike

RAILS = (
    # rail, nominal V, regulator, sense mOhm, buck efficiency %, full-load mA, probe really on it, habit
    ("V_CORE_1V1", 1.1, "buck", 10, 88, 420, "P1", "millivolts"),
    ("V_IO_1V8", 1.8, "buck", 20, 90, 160, "P6", None),
    ("V_MEM_1V2", 1.2, "buck", 10, 87, 300, "P3", None),
    ("V_MCU_3V3", 3.3, "buck", 20, 92, 210, "P8", "microvolts"),
    ("V_RF_2V8", 2.8, "LDO", 50, "", 95, "P5", None),
    ("V_ANA_1V8", 1.8, "LDO", 100, "", 38, "P2", None),
    ("V_PLL_1V0", 1.0, "LDO", 100, "", 22, "P7", "reversed"),
    ("V_SENS_3V3", 3.3, "LDO", 50, "", 64, "P4", None),
)


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "bench"
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    sealed, clipped = {}, {}
    trim = {r[0]: r[1] * rng.uniform(0.992, 1.008) for r in RAILS}

    for phase, load in PHASES:
        columns = {}
        for rail, nominal, reg, mohm, eff, full_ma, probe, habit in RAILS:
            share = load * rng.uniform(0.7, 1.15)
            wander, burst, volts, senses, drawn = 0.0, 0, [], [], 0.0
            slow_sd = DRIFT_V[reg]
            drift = rng.gauss(0, slow_sd)
            for i in range(SAMPLES):
                drift = 0.997 * drift + rng.gauss(0, slow_sd * (1 - 0.997 ** 2) ** 0.5)
                wander = 0.99 * wander + rng.gauss(0, 0.004)
                if burst:
                    burst -= 1
                elif rng.random() < 1 / 300.0:
                    burst = rng.randrange(5, 30)               # a radio or flash burst
                amps = full_ma / 1000.0 * share * (1 + wander) \
                    * (1.6 if burst else 1.0) * rng.uniform(0.97, 1.03)
                v = trim[rail] - 0.012 * amps / (full_ma / 1000.0) + drift \
                    + rng.gauss(0, RIPPLE_V[reg])
                v = round(v, 4)
                sense_mv = round(amps * mohm, 4)                # mOhm x A = mV
                amps_seen = sense_mv / mohm
                if reg == "LDO":
                    drawn += amps_seen * BUS_V * 1000.0
                else:
                    drawn += v * amps_seen * 1000.0 / (eff / 100.0)
                volts.append(v)
                senses.append(sense_mv)
            columns[probe] = (volts, senses, habit)
            sealed["%s/%s" % (rail, phase)] = round(drawn / SAMPLES, 2)
            clipped[rail] = dict(probe=probe, regulator=reg, habit=habit)
        with open(outdir / ("phase_%s.csv" % phase), "w", newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            probes = ["P%d" % n for n in range(1, 9)]
            out.writerow(["t_ms"] + [c for p in probes
                                     for c in (p + "_v", p + "_sense_mv")])
            for i in range(SAMPLES):
                row = [i * EVERY_MS]
                for p in probes:
                    volts, senses, habit = columns[p]
                    v, s = volts[i], senses[i]
                    if habit == "millivolts":
                        row += ["%.1f" % (v * 1000), "%.4f" % s]
                    elif habit == "microvolts":
                        row += ["%.4f" % v, "%.1f" % (s * 1000)]
                    elif habit == "reversed":
                        row += ["%.4f" % v, "%.4f" % -s]
                    else:
                        row += ["%.4f" % v, "%.4f" % s]
                out.writerow(row)

    with open(outdir / "rails.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["rail", "nominal_v", "regulator", "sense_mohm",
                      "efficiency_pct"])
        for r in RAILS:
            out.writerow([r[0], "%.1f" % r[1], r[2], r[3], r[4]])
    with open(outdir / "probe_map.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["probe", "rail"])
        for n, r in enumerate(RAILS, 1):
            out.writerow(["P%d" % n, r[0]])
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "clips.json").write_bytes(json.dumps(clipped, indent=1).encode())
    print("rails %d  lines %d" % (len(RAILS), len(sealed)))


if __name__ == "__main__":
    main()
