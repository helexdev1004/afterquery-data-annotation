"""Three days at the loading gantry, then the terminal's own records of them.

    python load_out.py [outdir]

What was loaded comes first: every ten seconds each arm delivers so many true
litres of whichever pipeline batch has reached it, and a load's batch and its
litres at 15 degC are taken from that. The terminal automation system's log is
written afterwards. It turns each meter's pulses into litres with the K-factor
it has on file for the arm - and for two arms that is the wrong meter's, the
two meters having changed places at the last service.

An arm loads at the rate its flow controller is set to, whatever the batch, so
a batch does not show in how fast an arm runs. What differs between batches is
how steadily the meter turns from one ten seconds to the next, and the batch
tickets say, in true litres, where on each header one batch gave way to the
next.
"""

import csv
import json
import pathlib
import random
import sys
from datetime import datetime, timedelta

SEED = 3316624
BEGINS = datetime(2026, 12, 1)
STEPS = 3 * 8640                       # ten-second lines in three days
GALLON_L = 3.785411784
EXPANSION = 0.00084                    # per degC, the note's figure
STEADINESS_L = (1.4, 3.6, 8.5)         # ten seconds to the next, by batch
LOADS_EACH = 8

ARMS = (
    # arm, K on file (pulses/L), K of the meter really fitted, TAS habit
    ("A1", 53.94, 53.94, "cubic metres"), ("A2", 50.93, 57.10, None),
    ("A3", 47.85, 47.85, "fahrenheit"), ("A4", 57.10, 50.93, "gallons"),
    ("A5", 60.52, 60.52, None),
)


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "terminal"
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    columns, tickets, sealed, loads_out, fitted = {}, [], {}, [], {}
    batch_no = 40

    for arm, k_file, k_true, habit in ARMS:
        over = k_true / k_file               # TAS litres per true litre
        rate = rng.uniform(340, 420)         # true litres in ten seconds
        true_l, showing = 0.0, rng.uniform(2e6, 9e6)
        show0 = showing
        temp = rng.uniform(9, 17)
        # batches down this header, by true litres since the log began
        batches, at, kind = [], 0.0, None
        while at < 3.6e6:
            batch_no += 1
            kind = rng.choice([k for k in range(3) if k != kind])
            batches.append((at, "B%02d" % batch_no, kind))
            at += rng.uniform(260e3, 520e3)
        tickets.append((arm, batches))

        tot, temps, loads = [], [], []
        idle, left, wander, fuss, current = rng.randrange(5, 90), 0, 0.0, 0, None
        for i in range(STEPS):
            temp += rng.gauss(0, 0.004) + 0.0004 * (13 - temp)
            step = 0.0
            if left:
                k = max(j for j, b in enumerate(batches) if b[0] <= true_l)
                wander = 0.97 * wander + rng.gauss(0, 0.5)
                if fuss:
                    fuss -= 1
                elif rng.random() < 1 / 700.0:
                    fuss = rng.randrange(4, 14)
                step = rate + wander \
                    + rng.gauss(0, STEADINESS_L[batches[k][2]]) \
                    + (rng.gauss(0, 12.0) if fuss else 0.0)
                step = max(step, 0.5 * rate)
                current["temps"].append(temp)
                current["batches"].add(batches[k][1])
                left -= 1
                if not left:
                    current["end_true"] = true_l + step
                    current["end_show"] = showing + step * over
                    loads.append(current)
                    idle = rng.randrange(30, 240)
            elif idle:
                idle -= 1
            else:
                left = rng.randrange(70, 100)       # a load of 12 to 16 minutes
                current = dict(start_true=true_l, start_show=showing,
                               temps=[], batches=set())
            true_l += step
            showing += step * over
            tot.append(showing)
            temps.append(temp)
        columns[arm] = (tot, temps, habit)
        fitted[arm] = dict(k_on_file=k_file, k_fitted=k_true, habit=habit)

        edges = [b[0] for b in batches]
        # a load asked about lies well inside one batch, whether the header's
        # litres are reckoned truly or as the TAS shows them
        whole = [l for l in loads if len(l["batches"]) == 1
                 and min(abs(l["start_true"] - e) for e in edges) > 45e3
                 and min(abs(l["start_show"] - show0 - e) for e in edges) > 45e3]
        rng.shuffle(whole)
        for n, l in enumerate(sorted(whole[:LOADS_EACH],
                                     key=lambda l: l["start_true"]), 1):
            name = "L%s%02d" % (arm[1], n)
            mean_t = sum(l["temps"]) / len(l["temps"])
            litres = (l["end_true"] - l["start_true"]) \
                * (1 - EXPANSION * (mean_t - 15))
            sealed[name] = [next(iter(l["batches"])), round(litres)]
            loads_out.append((name, arm, l["start_show"], l["end_show"], habit))

    def shown_total(v, habit):
        if habit == "cubic metres":
            return "%.4f" % (v / 1000.0)
        if habit == "gallons":
            return "%.1f" % (v / GALLON_L)
        return "%.1f" % v

    with open(outdir / "tas_log.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["logged"] + [c for a, *_ in ARMS
                                   for c in (a + "_total", a + "_temp")])
        for i in range(STEPS):
            row = [(BEGINS + timedelta(seconds=10 * i)).strftime(
                "%Y-%m-%d %H:%M:%S")]
            for arm, *_ in ARMS:
                tot, temps, habit = columns[arm]
                t = temps[i] * 9 / 5 + 32 if habit == "fahrenheit" else temps[i]
                row += [shown_total(tot[i], habit), "%.2f" % t]
            out.writerow(row)
    with open(outdir / "arms.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["arm", "header", "meter_serial", "k_factor_pulses_per_l"])
        for n, (arm, k_file, _, _) in enumerate(ARMS, 1):
            out.writerow([arm, "H%d" % n, "TM-%d" % (4410 + 7 * n),
                          "%.2f" % k_file])
    with open(outdir / "batch_tickets.txt", "w", newline="\n") as handle:
        for n, (arm, batches) in enumerate(tickets, 1):
            handle.write("HEADER H%d\n" % n)
            for at, name, _ in batches:
                handle.write("  %s from %d L\n" % (name, round(at)))
            handle.write("\n")
    with open(outdir / "loads.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["load", "arm", "totaliser_start", "totaliser_end"])
        for name, arm, a, b, habit in sorted(loads_out):
            out.writerow([name, arm, shown_total(a, habit),
                          shown_total(b, habit)])
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "fitted.json").write_bytes(json.dumps(fitted, indent=1).encode())
    print("arms %d  log lines %d  loads asked about %d"
          % (len(ARMS), STEPS, len(sealed)))
    return 0 if len(sealed) == LOADS_EACH * len(ARMS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
