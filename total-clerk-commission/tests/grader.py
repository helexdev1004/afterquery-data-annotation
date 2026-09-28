"""Checks /app/commission.csv against the sealed commission.

Only the csv module touches the agent's file; none of the agent's code is
imported or run.
"""
import csv
import json
import pathlib

SHEET = pathlib.Path("/app/commission.csv")
SEALED = pathlib.Path("/tests/sealed.json")
LINES_THAT_MAY_BE_WRONG = 2
WITHIN_GBP = 0.50


def sheet_lines():
    """({'A. Hartley/2026-07': amount as written}, '') or (None, the fault)."""
    if not SHEET.is_file():
        return None, "/app/commission.csv is not there"
    try:
        with open(SHEET, newline="") as handle:
            return {"%s/%s" % ((r.get("clerk") or "").strip(),
                               (r.get("month") or "").strip()):
                    (r.get("commission_gbp") or "").strip()
                    for r in csv.DictReader(handle)}, ""
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/commission.csv will not parse: %s" % why


def near_enough(written, true):
    try:
        return abs(float(written) - true) <= WITHIN_GBP + 1e-9
    except (TypeError, ValueError):
        return False


def lines_wrong():
    """(lines wrong, lines in all, a remark on each wrong line)."""
    sealed = json.loads(SEALED.read_text())
    lines, fault = sheet_lines()
    if lines is None:
        return len(sealed), len(sealed), [fault]
    wrong = ["%s: wrote %r, true %.2f" % (k, lines.get(k), sealed[k])
             for k in sorted(sealed) if not near_enough(lines.get(k), sealed[k])]
    return len(wrong), len(sealed), wrong
