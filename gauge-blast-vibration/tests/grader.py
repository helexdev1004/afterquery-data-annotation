"""Marks /app/blast_pgv.csv, one station at a time, against the sealed peaks.

Only the csv module reads the agent's file; nothing the agent wrote is imported
or run.
"""
import csv
import json
import pathlib

REPORT = pathlib.Path("/app/blast_pgv.csv")
SEALED = json.loads(pathlib.Path("/tests/sealed.json").read_text())
PGV_WITHIN = 0.01
SECONDS_WITHIN = 0.02


def report_rows():
    """The report's rows as dictionaries; an empty list when there is no usable file."""
    if not REPORT.is_file():
        return []
    try:
        with open(REPORT, newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:                                         # noqa: BLE001
        return []


def station_line(station):
    """(pgv_um_s, peak_time_s) as floats for one station, or None."""
    for r in report_rows():
        if (r.get("station") or "").strip().upper() == station:
            try:
                return float(r.get("pgv_um_s")), float(r.get("peak_time_s"))
            except (TypeError, ValueError):
                return None
    return None


def fault(station):
    """'' when the station's line is right; otherwise what is wrong with it."""
    pgv, at = SEALED[station]
    line = station_line(station)
    if line is None:
        return "%s: no line with two numbers" % station
    if abs(line[0] - pgv) > PGV_WITHIN * pgv + 1e-9:
        return "%s: velocity %s, sealed %s" % (station, line[0], pgv)
    if abs(line[1] - at) > SECONDS_WITHIN + 1e-9:
        return "%s: peak time %s, sealed %s" % (station, line[1], at)
    return ""
