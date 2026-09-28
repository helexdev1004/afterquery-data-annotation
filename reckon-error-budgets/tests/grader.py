"""Checks /app/error_budget.csv against the sealed figures.

The agent's file is read with the csv module; none of the agent's code is
imported or run.
"""
import csv
import json
import pathlib

FIGURES = pathlib.Path("/app/error_budget.csv")
SEALED = pathlib.Path("/tests/sealed.json")
LINES_THAT_MAY_BE_WRONG = 1
WITHIN_GOOD_PCT = 0.002
WITHIN_BUDGET_PCT = 0.5


def figure_lines():
    """({'svc/1': (good_pct, budget_used_pct) as written}, '') or (None, why)."""
    if not FIGURES.is_file():
        return None, "/app/error_budget.csv was not written"
    try:
        with open(FIGURES, newline="") as handle:
            return {"%s/%s" % ((r.get("service") or "").strip(),
                               (r.get("week") or "").strip()):
                    ((r.get("good_pct") or "").strip(),
                     (r.get("budget_used_pct") or "").strip())
                    for r in csv.DictReader(handle)}, ""
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/error_budget.csv will not parse: %s" % why


def line_right(line, sealed):
    if line is None:
        return False
    try:
        return abs(float(line[0]) - sealed[0]) <= WITHIN_GOOD_PCT + 1e-9 \
            and abs(float(line[1]) - sealed[1]) <= WITHIN_BUDGET_PCT + 1e-9
    except ValueError:
        return False


def lines_wrong():
    """(lines wrong, lines in all, a remark on each wrong line)."""
    sealed = json.loads(SEALED.read_text())
    lines, why = figure_lines()
    if lines is None:
        return len(sealed), len(sealed), [why]
    wrong = ["%s: %s, sealed %s" % (k, lines.get(k, "no line"), sealed[k])
             for k in sorted(sealed) if not line_right(lines.get(k), sealed[k])]
    return len(wrong), len(sealed), wrong
