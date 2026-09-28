"""Train the eight runs of the sweep, then write their logs and the run sheet.

    python train_sweep.py [outdir]

The runs come first: each follows its own loss curve, reaches the target at its
own step, and its tokens and GPU-hours follow from that. Then the logs are
written, each by its own launcher script, and the run sheet is written as the
group believes it. For two pairs of runs the log files were copied back from
the cluster under each other's names.

Each crossed pair is two runs at the same global batch size, so their curves
fall at the same pace and nothing about a log's level says whose it is. What
differs is how many GPUs the batch was spread over. A log records the loss of
the first device's share of the batch, not the mean over all devices, so the
fewer sequences a device sees per step the more the logged loss jumps about
from one line to the next.
"""

import csv
import json
import math
import pathlib
import random
import sys

SEED = 5744563
SEQ_LEN = 2048
TARGET = 3.200
LOG_EVERY = 10
WINDOW = 20

RUNS = (
    # run, global batch, gpus, log file really its own, launcher habit
    ("R1", 256, 8, "run_d.log", None),
    ("R2", 256, 16, "run_b.log", "perplexity"),
    ("R3", 256, 32, "run_c.log", None),
    ("R4", 256, 64, "run_a.log", None),
    ("R5", 512, 8, "run_h.log", "kilosteps"),
    ("R6", 512, 16, "run_f.log", None),
    ("R7", 512, 32, "run_g.log", "millinats"),
    ("R8", 512, 64, "run_e.log", None),
)
STEP_TIME_S = {(256, 8): 1.92, (256, 16): 1.04, (256, 32): 0.61, (256, 64): 0.41,
               (512, 8): 3.71, (512, 16): 1.95, (512, 32): 1.08, (512, 64): 0.66}


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "cluster"
    (outdir / "logs").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    sealed, truth = {}, {}

    for n, (run, batch, gpus, log_file, habit) in enumerate(RUNS):
        pace = rng.uniform(0.93, 1.08)                     # this seed's luck
        fast, slow = (1500, 9000) if batch == 256 else (900, 5600)
        per_device = batch // gpus
        jitter = 0.5 / math.sqrt(per_device)
        wander, spike, window, reached, lines = 0.0, 0.0, [], None, []
        step = 0
        while reached is None or step < reached + 3000:
            step += LOG_EVERY
            curve = 2.9 + 1.9 * math.exp(-step / (fast * pace)) \
                + 0.9 * math.exp(-step / (slow * pace))
            wander = 0.97 * wander + rng.gauss(0, 0.006)
            if rng.random() < 1 / 260.0:
                spike = rng.uniform(0.15, 0.5)             # a bad shard
            spike *= 0.88
            loss = round(curve + wander + spike + rng.gauss(0, jitter), 4)
            # the target is judged on the loss as the log holds it
            if habit == "perplexity":
                loss = math.log(float("%.3f" % math.exp(loss)))
            elif habit == "millinats":
                loss = round(loss * 1000) / 1000.0
            window = (window + [loss])[-WINDOW:]
            if reached is None and len(window) == WINDOW \
                    and sum(window) / WINDOW <= TARGET:
                reached = step
            lines.append((step, loss))
        sealed[run] = [reached, reached * batch * SEQ_LEN,
                       round(reached * STEP_TIME_S[(batch, gpus)] * gpus
                             / 3600.0, 1)]
        with open(outdir / "logs" / log_file, "w", newline="\n") as handle:
            if habit == "perplexity":
                handle.write("step,train_ppl\n")
            else:
                handle.write("step,train_loss\n")
            for step, loss in lines:
                shown_step = "%.2f" % (step / 1000.0) if habit == "kilosteps" \
                    else str(step)
                if habit == "perplexity":
                    shown = "%.3f" % math.exp(loss)
                elif habit == "millinats":
                    shown = "%d" % round(loss * 1000)
                else:
                    shown = "%.4f" % loss
                handle.write("%s,%s\n" % (shown_step, shown))
        truth[run] = dict(log=log_file, per_device=per_device, habit=habit)

    with open(outdir / "run_sheet.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["run", "global_batch", "gpus", "learning_rate", "log_file"])
        for k, (run, batch, gpus, _, _) in enumerate(RUNS):
            out.writerow([run, batch, gpus, "3e-4" if batch == 256 else "4.2e-4",
                          "run_%s.log" % "abcdefgh"[k]])
    with open(outdir / "step_times.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["global_batch", "gpus", "seconds_per_step"])
        for (batch, gpus), s in sorted(STEP_TIME_S.items()):
            out.writerow([batch, gpus, "%.2f" % s])
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "copied.json").write_bytes(json.dumps(truth, indent=1).encode())
    for run in sorted(sealed):
        print(run, sealed[run], truth[run]["log"])


if __name__ == "__main__":
    main()
