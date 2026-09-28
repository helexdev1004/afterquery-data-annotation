"""Peak vertical ground velocity and its time for every station.

    python blast_pgv.py [folder]        writes folder/blast_pgv.csv

`report(folder, reading)` does the work; `reading` names, for each way a
logger's file can depart from the group's note, which of the two to go by.
"""

import csv
import math
import pathlib
import sys

LSB_V = 40.0 / 2 ** 24
SPS = 100
FILE_STARTS = "08:29:00"
SHOT_AFTER_START_S = 60

BY_THE_FILES = {"local_time": "put_back", "unsigned": "fold", "volts": "to_counts",
                "stamps": "ask_the_quiet"}
BY_THE_NOTE = {"local_time": "as_stamped", "unsigned": "as_written",
               "volts": "as_counts", "stamps": "as_stamped"}


def where():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else here.parent / "shot"


def read_file(path, reading):
    """(stamped station, samples in counts, seconds the clock is off, habits seen)."""
    lines = path.read_text().splitlines()
    head = [part.strip() for part in lines[0].split(",")]
    station = head[0].split()[1].split("_")[1]
    values = [float(v) for line in lines[1:] for v in line.split()]
    seen, clock_off = [], 0.0
    clock = head[3].split("T")[1][:8]
    if clock != FILE_STARTS:
        seen.append("local_time")
        if reading["local_time"] == "as_stamped":
            h, m, s = (int(x) for x in clock.split(":"))
            h0, m0, s0 = (int(x) for x in FILE_STARTS.split(":"))
            clock_off = (h - h0) * 3600.0 + (m - m0) * 60.0 + (s - s0)
    if head[-1].upper() == "VOLTS" or max(abs(v) for v in values) < 50:
        seen.append("volts")
        if reading["volts"] == "to_counts":
            values = [v / LSB_V for v in values]
    if max(values) > 2 ** 23:
        seen.append("unsigned")
        if reading["unsigned"] == "fold":
            values = [v - 2 ** 24 if v >= 2 ** 23 else v for v in values]
    return station, values, clock_off, seen


def jumpiness(samples):
    """Spread of sample-to-sample steps over the spread of the samples, before the shot."""
    calm = samples[:SHOT_AFTER_START_S * SPS]
    mean = sum(calm) / len(calm)
    spread = math.sqrt(sum((v - mean) ** 2 for v in calm) / len(calm))
    steps = [b - a for a, b in zip(calm, calm[1:])]
    step_spread = math.sqrt(sum(s * s for s in steps) / len(steps))
    return step_spread / spread if spread else 0.0


def peak(samples, clock_off, volts_per_m_s):
    shot = SHOT_AFTER_START_S * SPS
    calm = samples[:shot]
    rest = sum(calm) / len(calm)
    best, at = -1.0, shot
    for i in range(shot, len(samples)):
        size = abs(samples[i] - rest)
        if size > best:
            best, at = size, i
    return best * LSB_V / volts_per_m_s * 1e6, (at - shot) / SPS + clock_off


def report(folder, reading):
    """({station: (pgv um/s, peak time s)}, what each file showed)."""
    folder = pathlib.Path(folder)
    with open(folder / "stations.csv", newline="") as handle:
        stations = {r["station"]: r for r in csv.DictReader(handle)}
    files = {}
    for path in sorted((folder / "waveforms").glob("*.slist")):
        station, samples, clock_off, seen = read_file(path, reading)
        files[path.name] = dict(stamped=station, samples=samples, off=clock_off,
                                habits=seen, jumpiness=jumpiness(samples))
    stood_at = {name: f["stamped"] for name, f in files.items()}
    if reading["stamps"] == "ask_the_quiet":
        smooth = sum(1 for s in stations.values() if s["kind"] == "broadband")
        order = sorted(files, key=lambda n: files[n]["jumpiness"])
        for k, name in enumerate(order):
            files[name]["looks"] = "broadband" if k < smooth else "geophone"
        odd = [n for n in files
               if files[n]["looks"] != stations[files[n]["stamped"]]["kind"]]
        if len(odd) == 2:         # the two loggers stood at each other's stations
            one, other = odd
            stood_at[one], stood_at[other] = files[other]["stamped"], files[one]["stamped"]
    out = {}
    for name, station in stood_at.items():
        files[name]["station"] = station
        s = stations[station]
        gain = float(s["sensitivity_v_s_per_m"]) * float(s["preamp_gain"])
        out[station] = peak(files[name]["samples"], files[name]["off"], gain)
    return out, files


if __name__ == "__main__":
    folder = where()
    answer, _ = report(folder, BY_THE_FILES)
    with open(folder / "blast_pgv.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["station", "pgv_um_s", "peak_time_s"])
        for station in sorted(answer):
            pgv, at = answer[station]
            out.writerow([station, "%.2f" % pgv, "%.2f" % at])
    print("%d stations written" % len(answer))
