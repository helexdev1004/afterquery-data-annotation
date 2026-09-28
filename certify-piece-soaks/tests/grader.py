"""Checks /app/soaks.csv against the sealed certificate figures.

The agent's file is read with the csv module; none of the agent's code is
imported or run.
"""
import csv
import json
import pathlib

SOAKS = pathlib.Path("/app/soaks.csv")
SEALED = pathlib.Path("/tests/sealed.json")
LINES_THAT_MAY_BE_WRONG = 1
WITHIN_MIN = 0.5
WITHIN_C = 0.3


def soak_lines():
    """({piece: (soak_min, mean_soak_c) as written}, '') or (None, the fault)."""
    if not SOAKS.is_file():
        return None, "/app/soaks.csv was not written"
    try:
        with open(SOAKS, newline="") as handle:
            return {(r.get("piece") or "").strip():
                    ((r.get("soak_min") or "").strip(),
                     (r.get("mean_soak_c") or "").strip())
                    for r in csv.DictReader(handle)}, ""
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/soaks.csv will not parse: %s" % why


def line_right(line, sealed):
    if line is None:
        return False
    try:
        return abs(float(line[0]) - sealed[0]) <= WITHIN_MIN + 1e-9 \
            and abs(float(line[1]) - sealed[1]) <= WITHIN_C + 1e-9
    except ValueError:
        return False


def lines_wrong():
    """(lines wrong, lines in all, a remark on each wrong line)."""
    sealed = json.loads(SEALED.read_text())
    lines, fault = soak_lines()
    if lines is None:
        return len(sealed), len(sealed), [fault]
    wrong = ["%s: %s, sealed %s" % (k, lines.get(k, "no line"), sealed[k])
             for k in sorted(sealed) if not line_right(lines.get(k), sealed[k])]
    return len(wrong), len(sealed), wrong
