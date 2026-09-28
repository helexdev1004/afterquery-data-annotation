"""Monthly runoff at every gauging station.

    python water_balance.py [folder]        writes folder/monthly_runoff.csv

`runoff(folder, reading)` is the job; `reading` says, for each way a logger
file can differ from the hydrologist's note, which of the two to believe.
"""

import csv
import pathlib
import statistics
import sys

EVERY_S = 15 * 60

THE_FILES = {"centimetres": "to_metres", "millimetres": "to_metres",
             "negative": "take_the_size", "housings": "ask_the_water"}
THE_NOTE = {"centimetres": "as_metres", "millimetres": "as_metres",
            "negative": "as_logged", "housings": "as_the_sheet_says"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "catchment"


def table(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def read_log(path, reading):
    """[(month, stage in metres)] and the habits found in the file."""
    rows = table(path)
    values = [float(r["stage"]) for r in rows]
    habits = []
    if statistics.fmean(values) < 0:
        habits.append("negative")
        if reading["negative"] == "take_the_size":
            values = [abs(v) for v in values]
    middle = statistics.median(abs(v) for v in values)
    if middle > 100:
        habits.append("millimetres")
        if reading["millimetres"] == "to_metres":
            values = [v / 1000.0 for v in values]
    elif middle > 5:
        habits.append("centimetres")
        if reading["centimetres"] == "to_metres":
            values = [v / 100.0 for v in values]
    return [(r["time"][:7], v) for r, v in zip(rows, values)], habits


def restlessness(stages):
    """The middle distance of a reading from the mean of its two neighbours."""
    return statistics.median(
        abs(stages[i] - (stages[i - 1] + stages[i + 1]) / 2.0)
        for i in range(1, len(stages) - 1))


def runoff(folder, reading):
    """{'G1/2027-01': thousand cubic metres} and what each file showed."""
    folder = pathlib.Path(folder)
    stations = {r["station"]: r for r in table(folder / "stations.csv")}
    sheet = {r["logger_file"]: r["station"]
             for r in table(folder / "field_sheet.csv")}
    logs, seen = {}, {}
    for name, station in sheet.items():
        series, habits = read_log(folder / "stage_logs" / (name + ".csv"),
                                  reading)
        logs[name] = series
        seen[name] = dict(habits=habits, sheet=station,
                          restless=restlessness([abs(v) for _, v in series]))
    came_from = dict(sheet)
    if reading["housings"] == "ask_the_water":
        order = sorted(seen, key=lambda n: seen[n]["restless"])
        weirs = sum(1 for s in stations.values() if "weir" in s["control"])
        for k, name in enumerate(order):
            seen[name]["looks"] = "weir" if k < weirs else "section"
        odd = [n for n in seen
               if (seen[n]["looks"] == "weir")
               != ("weir" in stations[sheet[n]]["control"])]
        for n in odd:             # its partner: the odd file with the same zero
            zero = stations[sheet[n]]["gauge_zero_m"]
            for other in odd:
                if other != n and stations[sheet[other]]["gauge_zero_m"] == zero:
                    came_from[n] = sheet[other]
    out = {}
    for name, station in came_from.items():
        seen[name]["from"] = station
        s = stations[station]
        c, zero = float(s["coefficient"]), float(s["gauge_zero_m"])
        p = 2.5 if "weir" in s["control"] else float(s["exponent"])
        for month, stage in logs[name]:
            head = max(stage - zero, 0.0)
            key = "%s/%s" % (station, month)
            out[key] = out.get(key, 0.0) + c * head ** p * EVERY_S
    return {k: round(v / 1000.0, 1) for k, v in out.items()}, seen


if __name__ == "__main__":
    where = base()
    answer, _ = runoff(where, THE_FILES)
    with open(where / "monthly_runoff.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["station", "month", "runoff_dam3"])
        for key in sorted(answer):
            station, month = key.split("/")
            sheet.writerow([station, month, "%.1f" % answer[key]])
    print("%d lines written" % len(answer))
