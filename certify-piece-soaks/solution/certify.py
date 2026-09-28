"""Soak minutes and mean soak temperature for every test piece.

    python certify.py [folder]        writes folder/soaks.csv

`soaks(folder, reading)` is the job; `reading` says, for each way the logger's
records can differ from the lab's note, which of the two to go by.
"""

import csv
import pathlib
import statistics
import sys

SOAK_AT_C = 840.0
EVERY_S = 10

THE_RECORDS = {"fahrenheit": "to_celsius", "kelvin": "to_celsius",
               "hundredths": "to_degrees", "leads": "ask_the_jitter"}
THE_NOTE = {"fahrenheit": "as_celsius", "kelvin": "as_celsius",
            "hundredths": "as_degrees", "leads": "as_scheduled"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "furnace"


def table(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def channels_of(path, reading):
    """{channel: readings in degC} and {channel: habits found}."""
    raw = {}
    for r in table(path):
        raw.setdefault(r["channel"], []).append(float(r["reading"]))
    out, habits = {}, {}
    for ch, values in raw.items():
        top, found = max(values), []
        if top > 20000:
            found.append("hundredths")
            if reading["hundredths"] == "to_degrees":
                values = [v / 100.0 for v in values]
        elif top > 1350:
            found.append("fahrenheit")
            if reading["fahrenheit"] == "to_celsius":
                values = [(v - 32) * 5 / 9 for v in values]
        elif top > 1000:
            found.append("kelvin")
            if reading["kelvin"] == "to_celsius":
                values = [v - 273.15 for v in values]
        out[ch], habits[ch] = values, found
    return out, habits


def jitter(values):
    """Middle distance of a reading from the mean of its neighbours, over the
    hot part of the run where the furnace is holding."""
    hot = 0.97 * max(values)
    steps = [abs(values[i] - (values[i - 1] + values[i + 1]) / 2.0)
             for i in range(1, len(values) - 1)
             if min(values[i - 1], values[i], values[i + 1]) > hot]
    return statistics.median(steps) if steps else 0.0


def soaks(folder, reading):
    """{piece: (soak_min, mean_soak_c)} and what each channel showed."""
    folder = pathlib.Path(folder)
    pieces = {r["piece"]: r for r in table(folder / "pieces.csv")}
    schedule = table(folder / "channel_schedule.csv")
    out, seen = {}, {}
    for load in sorted({r["load"] for r in schedule}):
        readings, habits = channels_of(folder / ("load_%s.csv" % load), reading)
        mine = {r["channel"]: r["piece"] for r in schedule if r["load"] == load}
        shake = {ch: jitter(v) for ch, v in readings.items()}
        carries = dict(mine)
        if reading["leads"] == "ask_the_jitter":
            ranked = sorted(shake, key=shake.get)
            steady = sum(1 for p in mine.values() if pieces[p]["probe"] == "Pt100")
            looks = {ch: "Pt100" if k < steady else "type K"
                     for k, ch in enumerate(ranked)}
            odd = [ch for ch in mine if looks[ch] != pieces[mine[ch]]["probe"]]
            if len(odd) == 2:
                carries[odd[0]], carries[odd[1]] = mine[odd[1]], mine[odd[0]]
        for ch, piece in carries.items():
            seen["%s/%s" % (load, ch)] = dict(
                scheduled=mine[ch], carries=piece, jitter=shake[ch],
                habits=habits[ch])
            p = pieces[piece]
            if p["probe"] == "type K":
                corrected = [v + float(p["offset_c"]) for v in readings[ch]]
            else:
                corrected = [v * float(p["scale"]) for v in readings[ch]]
            hot = [c for c in corrected if c >= SOAK_AT_C]
            out[piece] = (round(len(hot) * EVERY_S / 60.0, 1),
                          round(statistics.fmean(hot), 1) if hot else 0.0)
    return out, seen


if __name__ == "__main__":
    where = base()
    answer, _ = soaks(where, THE_RECORDS)
    with open(where / "soaks.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["piece", "soak_min", "mean_soak_c"])
        for piece in sorted(answer):
            sheet.writerow([piece, "%.1f" % answer[piece][0],
                            "%.1f" % answer[piece][1]])
    print("%d pieces certified" % len(answer))
