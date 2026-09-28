"""Steps, tokens and GPU-hours to the target loss, for every run of the sweep.

    python sweep_cost.py [folder]        writes folder/cost_to_target.csv

`cost(folder, reading)` is the job; `reading` says, for each way a log can
differ from the group's note, which of the two to believe.
"""

import csv
import math
import pathlib
import statistics
import sys

SEQ_LEN = 2048
TARGET = 3.200
WINDOW = 20

THE_LOGS = {"perplexity": "take_the_log", "kilosteps": "times_a_thousand",
            "millinats": "to_nats", "files": "ask_the_jitter"}
THE_NOTE = {"perplexity": "as_loss", "kilosteps": "as_steps",
            "millinats": "as_nats", "files": "as_the_sheet_says"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "cluster"


def table(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def read_log(path, reading):
    """[(step, loss in nats)] and the habits the launcher left in the file."""
    rows = table(path)
    habits = []
    value = [c for c in rows[0] if c != "step"][0]
    losses = [float(r[value]) for r in rows]
    steps = [float(r["step"]) for r in rows]
    if value == "train_ppl":
        habits.append("perplexity")
        if reading["perplexity"] == "take_the_log":
            losses = [math.log(v) for v in losses]
    elif statistics.median(losses) > 100:
        habits.append("millinats")
        if reading["millinats"] == "to_nats":
            losses = [v / 1000.0 for v in losses]
    if steps[1] - steps[0] < 1:
        habits.append("kilosteps")
        if reading["kilosteps"] == "times_a_thousand":
            steps = [round(s * 1000) for s in steps]
    return [(int(round(s)), l) for s, l in zip(steps, losses)], habits


def reached(series):
    window = []
    for step, loss in series:
        window = (window + [loss])[-WINDOW:]
        if len(window) == WINDOW and sum(window) / WINDOW <= TARGET:
            return step
    return None


def jitter(series):
    """The middle distance of a logged loss from the mean of its neighbours,
    over the second half of the log where the curve is nearly flat."""
    losses = [l for _, l in series][len(series) // 2:]
    return statistics.median(abs(losses[i] - (losses[i - 1] + losses[i + 1]) / 2)
                             for i in range(1, len(losses) - 1))


def cost(folder, reading):
    """{run: (steps, tokens, gpu_hours)} and what each log showed."""
    folder = pathlib.Path(folder)
    sheet = table(folder / "run_sheet.csv")
    times = {(r["global_batch"], r["gpus"]): float(r["seconds_per_step"])
             for r in table(folder / "step_times.csv")}
    logs, seen = {}, {}
    for r in sheet:
        logs[r["log_file"]], habits = read_log(folder / "logs" / r["log_file"],
                                               reading)
        seen[r["log_file"]] = dict(habits=habits, sheet=r["run"],
                                   jitter=jitter(logs[r["log_file"]]))
    belongs = {r["log_file"]: r["run"] for r in sheet}
    if reading["files"] == "ask_the_jitter":
        # within a global batch, the jumpiest log is the run with the fewest
        # sequences on a device: match the two orderings
        for batch in sorted({r["global_batch"] for r in sheet}):
            runs = sorted((r for r in sheet if r["global_batch"] == batch),
                          key=lambda r: -int(r["gpus"]))
            files = sorted((r["log_file"] for r in runs),
                           key=lambda f: -seen[f]["jitter"])
            for r, f in zip(runs, files):
                belongs[f] = r["run"]
    by_run = {r["run"]: r for r in sheet}
    out = {}
    for log_file, run in belongs.items():
        seen[log_file]["run"] = run
        r = by_run[run]
        steps = reached(logs[log_file])
        if steps is None:
            continue
        batch, gpus = int(r["global_batch"]), int(r["gpus"])
        hours = steps * times[(r["global_batch"], r["gpus"])] * gpus / 3600.0
        out[run] = (steps, steps * batch * SEQ_LEN, round(hours, 1))
    return out, seen


if __name__ == "__main__":
    where = base()
    answer, _ = cost(where, THE_LOGS)
    with open(where / "cost_to_target.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["run", "steps_to_target", "tokens_to_target",
                        "gpu_hours"])
        for run in sorted(answer):
            sheet.writerow([run, answer[run][0], answer[run][1],
                            "%.1f" % answer[run][2]])
    print("%d runs costed" % len(answer))
