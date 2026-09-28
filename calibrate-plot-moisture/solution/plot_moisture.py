"""Mean and driest-day volumetric water content for every plot of the trial.

    python plot_moisture.py [folder]      writes folder/plot_moisture.json

work_up(folder, files=..., probes=...) does it under one reading of the
records:
  files   the logger-file quirks that are undone (any of QUIRKS)
  probes  "sheet"  - each plot has the probe the installation sheet gives it
          "traces" - each plot has the probe its own trace points to
"""

import csv
import json
import math
import pathlib
import sys

QUIRKS = ("preamble", "index", "hundredths")


def trial_folder():
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "trial"


def rows_of(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def topp(e):
    return -0.053 + 0.0292 * e - 0.00055 * e * e + 0.0000043 * e ** 3


def logger_file(path, undone):
    """Hourly apparent permittivity from one logger file, and the quirks met."""
    with open(path, newline="") as handle:
        table = list(csv.reader(handle))
    met = []
    if table[0][0] == "TOA5":
        met.append("preamble")
        if "preamble" not in undone:
            return None, met
        head, body = table[1], table[4:]
        column = head.index("Ka")
    else:
        head, body = table[0], table[1:]
        column = 1
    values = [float(r[column]) for r in body]
    if head[column] == "refractive_index":
        met.append("index")
        if "index" in undone:
            values = [v * v for v in values]
    if min(values) > 100:
        met.append("hundredths")
        if "hundredths" in undone:
            values = [v / 100.0 for v in values]
    return values, met


def daily_swell(values):
    """Half the range of the median hour-of-day departure from a 24-hour running
    mean, as a fraction of the file's mean reading."""
    n = len(values)
    by_hour = [[] for _ in range(24)]
    for i in range(12, n - 12):
        window = values[i - 12:i + 13]
        centre = (sum(window) - 0.5 * window[0] - 0.5 * window[-1]) / 24.0
        by_hour[i % 24].append(values[i] - centre)
    shape = [sorted(h)[len(h) // 2] for h in by_hour]        # medians: wettings do not count
    return (max(shape) - min(shape)) / 2.0 / (sum(values) / n)


def water_content(probe, e):
    if probe["kind"] == "TDR":
        return topp(e - float(probe["cable_offset"]))
    return float(probe["lab_slope"]) * math.sqrt(e) + float(probe["lab_intercept"])


def work_up(folder, files=QUIRKS, probes="traces"):
    """({plot: {"mean_vwc":, "driest_daily_vwc":}}, what each file showed)."""
    folder = pathlib.Path(folder)
    sheet = {r["plot"]: r["probe"] for r in rows_of(folder / "plots.csv")}
    probe_list = {r["probe"]: r for r in rows_of(folder / "probes.csv")}
    seen = {}
    for plot in sheet:
        values, met = logger_file(folder / "loggers" / (plot + ".csv"), files)
        seen[plot] = dict(quirks=met, values=values,
                          swell=None if values is None else daily_swell(values))
    usable = [p for p in seen if seen[p]["values"] is not None]
    fitted = dict(sheet)
    if probes == "traces":
        capacitance = sum(1 for p in usable if probe_list[sheet[p]]["kind"] == "capacitance")
        ranked = sorted(usable, key=lambda p: -seen[p]["swell"])
        for k, plot in enumerate(ranked):
            seen[plot]["looks"] = "capacitance" if k < capacitance else "TDR"
        odd = [p for p in usable if seen[p]["looks"] != probe_list[sheet[p]]["kind"]]
        if len(odd) == 2:
            a, b = odd
            fitted[a], fitted[b] = sheet[b], sheet[a]
    out = {}
    for plot in usable:
        seen[plot]["probe"] = fitted[plot]
        theta = [water_content(probe_list[fitted[plot]], e) for e in seen[plot]["values"]]
        days = [theta[d:d + 24] for d in range(0, len(theta), 24)]
        out[plot] = dict(mean_vwc=round(sum(theta) / len(theta), 5),
                         driest_daily_vwc=round(min(sum(d) / len(d) for d in days), 5))
    return out, seen


if __name__ == "__main__":
    folder = trial_folder()
    figures, _ = work_up(folder)
    (folder / "plot_moisture.json").write_bytes(
        (json.dumps(figures, indent=1, sort_keys=True) + "\n").encode())
    print("%d plots written" % len(figures))
