"""Holds /app/out_of_band.csv against the sealed hours.

Only the csv module reads the agent's file. None of the agent's code is
imported or run.
"""
import csv
import json
import pathlib

RESULT = pathlib.Path("/app/out_of_band.csv")
SEALED = pathlib.Path("/tests/sealed.json")
LINES_THAT_MAY_BE_OUT = 4
WITHIN_HOURS = 0.25


def result_lines():
    """({'Z01/1': hours as written}, '') or (None, the trouble)."""
    if not RESULT.is_file():
        return None, "/app/out_of_band.csv is missing"
    try:
        with open(RESULT, newline="") as handle:
            rows = list(csv.DictReader(handle))
        return {"%s/%d" % ((r.get("zone") or "").strip(),
                           int(float(r.get("week") or "nan"))):
                (r.get("hours") or "").strip() for r in rows}, ""
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/out_of_band.csv cannot be read: %s" % why


def accepted(written, true):
    try:
        return abs(float(written) - true) <= WITHIN_HOURS + 1e-9
    except (TypeError, ValueError):
        return False


def lines_out():
    """(lines out, lines in all, a note on each line out)."""
    sealed = json.loads(SEALED.read_text())
    lines, trouble = result_lines()
    if lines is None:
        return len(sealed), len(sealed), [trouble]
    out = ["%s: wrote %r, true %.2f" % (k, lines.get(k), sealed[k])
           for k in sorted(sealed) if not accepted(lines.get(k), sealed[k])]
    return len(out), len(sealed), out
