"""Checks /app/service_due.csv against the sealed plan.

The agent's file is read with the csv module; none of the agent's code is
imported or run.
"""
import csv
import json
import pathlib
from datetime import date

PLAN = pathlib.Path("/app/service_due.csv")
SEALED = pathlib.Path("/tests/sealed.json")
WITHIN_HOURS = 0.2
WITHIN_DAYS = 1


def plan_lines():
    """({compressor: (hours, starts, due) as written}, '') or (None, why)."""
    if not PLAN.is_file():
        return None, "/app/service_due.csv was not written"
    try:
        with open(PLAN, newline="") as handle:
            return {(r.get("compressor") or "").strip():
                    ((r.get("run_hours") or "").strip(),
                     (r.get("starts") or "").strip(),
                     (r.get("due_date") or "").strip())
                    for r in csv.DictReader(handle)}, ""
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/service_due.csv will not parse: %s" % why


def line_right(line, sealed):
    if line is None:
        return False
    try:
        days = abs((date.fromisoformat(line[2])
                    - date.fromisoformat(sealed[2])).days)
        return abs(float(line[0]) - sealed[0]) <= WITHIN_HOURS + 1e-9 \
            and float(line[1]) == sealed[1] and days <= WITHIN_DAYS
    except ValueError:
        return False


def lines_wrong():
    """(lines wrong, lines in all, a remark on each wrong line)."""
    sealed = json.loads(SEALED.read_text())
    lines, why = plan_lines()
    if lines is None:
        return len(sealed), len(sealed), [why]
    wrong = ["%s: %s, sealed %s" % (k, lines.get(k, "no line"), sealed[k])
             for k in sorted(sealed) if not line_right(lines.get(k), sealed[k])]
    return len(wrong), len(sealed), wrong
