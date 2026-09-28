"""Checks /app/inbound_plan.csv against the sealed plan.

The agent's file is read with the csv module and nothing else of the agent's
is opened, imported or run.
"""
import csv
import json
import pathlib

PLAN = pathlib.Path("/app/inbound_plan.csv")
SEALED = pathlib.Path("/tests/sealed.json")
LINES_THAT_MAY_BE_WRONG = 4
WITHIN_KG = 0.5


def plan_lines():
    """({asn: (cartons, gross_kg, pallets) as written}, '') or (None, why)."""
    if not PLAN.is_file():
        return None, "/app/inbound_plan.csv was not written"
    try:
        with open(PLAN, newline="") as handle:
            return {(r.get("asn") or "").strip():
                    ((r.get("cartons") or "").strip(),
                     (r.get("gross_kg") or "").strip(),
                     (r.get("pallets") or "").strip())
                    for r in csv.DictReader(handle)}, ""
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/inbound_plan.csv does not parse: %s" % why


def line_right(line, sealed):
    if line is None:
        return False
    try:
        return float(line[0]) == sealed[0] and float(line[2]) == sealed[2] \
            and abs(float(line[1]) - sealed[1]) <= WITHIN_KG + 1e-9
    except ValueError:
        return False


def lines_wrong():
    """(lines wrong, lines to plan, a remark on each wrong line)."""
    sealed = json.loads(SEALED.read_text())
    lines, why = plan_lines()
    if lines is None:
        return len(sealed), len(sealed), [why]
    wrong = ["%s: %s, sealed %s" % (a, lines.get(a, "no line"), sealed[a])
             for a in sorted(sealed) if not line_right(lines.get(a), sealed[a])]
    return len(wrong), len(sealed), wrong
