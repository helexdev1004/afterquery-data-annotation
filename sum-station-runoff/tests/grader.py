"""Checks /app/monthly_runoff.csv against the sealed volumes.

The agent's file is read with the csv module; none of the agent's code is
imported or run.
"""
import csv
import json
import pathlib

VOLUMES = pathlib.Path("/app/monthly_runoff.csv")
SEALED = pathlib.Path("/tests/sealed.json")
LINES_THAT_MAY_BE_WRONG = 2
WITHIN_SHARE = 0.005


def volume_lines():
    """({'G1/2027-01': volume as written}, '') or (None, what is wrong)."""
    if not VOLUMES.is_file():
        return None, "/app/monthly_runoff.csv was not written"
    try:
        with open(VOLUMES, newline="") as handle:
            return {"%s/%s" % ((r.get("station") or "").strip(),
                               (r.get("month") or "").strip()):
                    (r.get("runoff_dam3") or "").strip()
                    for r in csv.DictReader(handle)}, ""
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/monthly_runoff.csv will not parse: %s" % why


def close_enough(written, true):
    try:
        return abs(float(written) - true) <= WITHIN_SHARE * true + 1e-9
    except (TypeError, ValueError):
        return False


def lines_wrong():
    """(lines wrong, lines in all, a remark on each wrong line)."""
    sealed = json.loads(SEALED.read_text())
    lines, problem = volume_lines()
    if lines is None:
        return len(sealed), len(sealed), [problem]
    wrong = ["%s: wrote %r, true %.1f" % (k, lines.get(k), sealed[k])
             for k in sorted(sealed) if not close_enough(lines.get(k), sealed[k])]
    return len(wrong), len(sealed), wrong
