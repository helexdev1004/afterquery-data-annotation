"""Checks /app/cost_to_target.csv against the sealed figures.

The agent's file is read with the csv module; none of the agent's code is
imported or run.
"""
import csv
import json
import pathlib

COSTS = pathlib.Path("/app/cost_to_target.csv")
SEALED = pathlib.Path("/tests/sealed.json")
WITHIN_GPU_HOURS = 0.1


def cost_lines():
    """({run: (steps, tokens, gpu_hours) as written}, '') or (None, the fault)."""
    if not COSTS.is_file():
        return None, "/app/cost_to_target.csv was not written"
    try:
        with open(COSTS, newline="") as handle:
            return {(r.get("run") or "").strip():
                    ((r.get("steps_to_target") or "").strip(),
                     (r.get("tokens_to_target") or "").strip(),
                     (r.get("gpu_hours") or "").strip())
                    for r in csv.DictReader(handle)}, ""
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/cost_to_target.csv will not parse: %s" % why


def line_right(line, sealed):
    if line is None:
        return False
    try:
        return float(line[0]) == sealed[0] and float(line[1]) == sealed[1] \
            and abs(float(line[2]) - sealed[2]) <= WITHIN_GPU_HOURS + 1e-9
    except ValueError:
        return False


def lines_wrong():
    """(lines wrong, lines in all, a remark on each wrong line)."""
    sealed = json.loads(SEALED.read_text())
    lines, fault = cost_lines()
    if lines is None:
        return len(sealed), len(sealed), [fault]
    wrong = ["%s: %s, sealed %s" % (k, lines.get(k, "no line"), sealed[k])
             for k in sorted(sealed) if not line_right(lines.get(k), sealed[k])]
    return len(wrong), len(sealed), wrong
