"""Sets /app/plan_volumes.csv against the sealed counts.

The sheet is read with the csv module; no code of the agent's is imported or
run.
"""
import csv
import json
import pathlib

SHEET = pathlib.Path("/app/plan_volumes.csv")
SEALED = pathlib.Path("/tests/sealed.json")
RUNS_THAT_MAY_BE_OUT = 4
WITHIN = 0.02


def read_sheet():
    """({run: vehicles as written}, '') or (None, what went wrong)."""
    if not SHEET.is_file():
        return None, "/app/plan_volumes.csv was not written"
    try:
        with open(SHEET, newline="") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/plan_volumes.csv will not parse: %s" % why
    return {(r.get("run") or "").strip(): (r.get("vehicles") or "").strip()
            for r in rows}, ""


def close_enough(written, true):
    try:
        return abs(float(written) - true) <= WITHIN * true + 1e-9
    except (TypeError, ValueError):
        return False


def runs_out():
    """(runs out, runs asked about, a line for each run out)."""
    sealed = json.loads(SEALED.read_text())
    sheet, wrong = read_sheet()
    if sheet is None:
        return len(sealed), len(sealed), [wrong]
    out = ["%s: wrote %r, true %d" % (run, sheet.get(run), sealed[run])
           for run in sorted(sealed)
           if not close_enough(sheet.get(run), sealed[run])]
    return len(out), len(sealed), out
