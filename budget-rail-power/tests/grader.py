"""Marks /app/rail_power.csv against the sealed budget figures.

Only the csv module touches the agent's file. Nothing the agent wrote is
imported or executed.
"""
import csv
import json
import pathlib

BUDGET = pathlib.Path("/app/rail_power.csv")
SEALED = pathlib.Path("/tests/sealed.json")
WITHIN = 0.005
ALLOWED_WRONG = 2


def budget_lines():
    """({'RAIL/phase': mean_mw text}, None) or (None, what went wrong)."""
    if not BUDGET.is_file():
        return None, "/app/rail_power.csv is missing"
    found = {}
    try:
        with open(BUDGET, newline="") as handle:
            for r in csv.DictReader(handle):
                rail = (r.get("rail") or "").strip()
                phase = (r.get("phase") or "").strip().lower()
                found[rail + "/" + phase] = (r.get("mean_mw") or "").strip()
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/rail_power.csv cannot be read: %s" % why
    return found, None


def close_enough(text, sealed_mw):
    try:
        return abs(float(text) - sealed_mw) <= WITHIN * sealed_mw + 1e-9
    except (TypeError, ValueError):
        return False


def mark():
    """(lines wrong, lines in all, one remark per wrong line)."""
    sealed = json.loads(SEALED.read_text())
    found, trouble = budget_lines()
    if found is None:
        return len(sealed), len(sealed), [trouble]
    remarks = ["%s: wrote %s, sealed %.2f" % (k, found.get(k, "nothing"), sealed[k])
               for k in sorted(sealed) if not close_enough(found.get(k), sealed[k])]
    return len(remarks), len(sealed), remarks
