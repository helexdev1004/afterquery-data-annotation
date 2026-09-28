"""Net tracer counts and mean residence time for every column.

    python breakthrough.py [folder]        writes folder/breakthrough.csv

`work_up(folder, reading)` does the job; `reading` says, for each way the
scaler's dump can differ from the lab's note, which of the two to believe.
"""

import csv
import pathlib
import sys

INJECT_S = 120
WRAP = 65536
BUSY_CPS = 500            # the scatter is measured where the pulse is well up

AS_DUMPED = {"running_total": "difference", "per_minute": "divide",
             "late_start": "shift", "cables": "ask_the_scatter"}
AS_NOTED = {"running_total": "as_counts", "per_minute": "as_counts",
            "late_start": "from_zero", "cables": "as_listed"}


def folder_given():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "labrun"


def sheet(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def dump_blocks(path):
    """{channel: (start second, [values])} from the scaler's dump."""
    blocks, channel = {}, None
    for line in pathlib.Path(path).read_text().splitlines():
        if line.startswith("[CH"):
            head = line.split()
            channel = int(head[0][3:-1])
            start = int(head[1].split("=")[1])
            blocks[channel] = (start, [])
        elif channel is not None and line.strip():
            blocks[channel][1].extend(int(v) for v in line.split())
    return blocks


def counts_per_second(start, values, reading):
    """(first bin, counts in each second) once the block's habits are undone."""
    found = []
    rising = sum(1 for a, b in zip(values, values[1:]) if b >= a)
    if rising > 0.95 * (len(values) - 1):
        found.append("running_total")
        if reading["running_total"] == "difference":
            values = [values[0]] + [(b - a) % WRAP
                                    for a, b in zip(values, values[1:])]
    if all(v % 60 == 0 for v in values) and max(values) > 6000:
        found.append("per_minute")
        if reading["per_minute"] == "divide":
            values = [v // 60 for v in values]
    first = 0
    if start:
        found.append("late_start")
        if reading["late_start"] == "shift":
            first = start
    return first, values, found


def scatter(counts):
    """Spread of a second's count about its neighbours' mean, over Poisson's."""
    squares, level = 0.0, 0.0
    for i in range(1, len(counts) - 1):
        if counts[i] >= BUSY_CPS:
            squares += (counts[i] - (counts[i - 1] + counts[i + 1]) / 2.0) ** 2
            level += 1.5 * counts[i]
    return squares / level if level else 1.0


def reckon(first, counts, dead_s):
    def true_rate(c):
        return c / (1.0 - c * dead_s) if c * dead_s < 1 else float("inf")
    before = [true_rate(c) for i, c in enumerate(counts, first) if i < INJECT_S]
    background = sum(before) / len(before)
    total = moment = 0.0
    for i, c in enumerate(counts, first):
        if i >= INJECT_S:
            net = true_rate(c) - background
            total += net
            moment += (i + 0.5 - INJECT_S) * net
    return total, moment / total if total else 0.0


def work_up(folder, reading):
    """({column: (net counts, mean residence s)}, what each channel showed)."""
    folder = pathlib.Path(folder)
    columns = {r["detector"]: r for r in sheet(folder / "columns.csv")}
    detectors = sheet(folder / "detectors.csv")
    listed = {int(d["scaler_channel"]): d for d in detectors}
    blocks = dump_blocks(folder / "scaler.dmp")
    seen = {}
    for channel, (start, values) in blocks.items():
        first, counts, found = counts_per_second(start, values, reading)
        seen[channel] = dict(first=first, counts=counts, habits=found,
                             listed=listed[channel]["detector"],
                             scatter=scatter(counts))
    feeds = {channel: listed[channel] for channel in blocks}
    if reading["cables"] == "ask_the_scatter":
        tubes = sum(1 for d in detectors if d["type"] == "GM")
        order = sorted(seen, key=lambda ch: seen[ch]["scatter"])
        for k, channel in enumerate(order):
            seen[channel]["looks"] = "GM" if k < tubes else "NaI"
        odd = [ch for ch in seen if seen[ch]["looks"] != listed[ch]["type"]]
        for ch in odd:            # its cable belongs to the odd channel of the same soil
            soil = columns[listed[ch]["detector"]]["soil"]
            for other in odd:
                if other != ch and \
                        columns[listed[other]["detector"]]["soil"] == soil:
                    feeds[ch] = listed[other]
    out = {}
    for channel, detector in feeds.items():
        seen[channel]["detector"] = detector["detector"]
        column = columns[detector["detector"]]["column"]
        dead_s = float(detector["dead_time_us"]) / 1e6
        out[column] = reckon(seen[channel]["first"], seen[channel]["counts"], dead_s)
    return out, seen


if __name__ == "__main__":
    where = folder_given()
    answer, _ = work_up(where, AS_DUMPED)
    with open(where / "breakthrough.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["column", "net_counts", "mean_residence_s"])
        for column in sorted(answer):
            net, mean_s = answer[column]
            out.writerow([column, "%.1f" % net, "%.2f" % mean_s])
    print("%d columns written" % len(answer))
