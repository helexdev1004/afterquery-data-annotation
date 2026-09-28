"""Marks /app/load_batches.csv against the sealed answers.

The file is parsed with the csv module. No code written by the agent is
imported or run.
"""
import csv
import json
import pathlib

ANSWERS = pathlib.Path("/app/load_batches.csv")
SEALED = pathlib.Path("/tests/sealed.json")
LINES_THAT_MAY_BE_WRONG = 4
WITHIN_LITRES = 25


def answers():
    """({load: (batch, litres as written)}, '') or (None, why not)."""
    if not ANSWERS.is_file():
        return None, "/app/load_batches.csv has not been written"
    try:
        with open(ANSWERS, newline="") as handle:
            return {(r.get("load") or "").strip():
                    ((r.get("batch") or "").strip(),
                     (r.get("litres_15") or "").strip())
                    for r in csv.DictReader(handle)}, ""
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/load_batches.csv will not read: %s" % why


def line_is_right(line, sealed):
    if line is None or line[0] != sealed[0]:
        return False
    try:
        return abs(float(line[1]) - sealed[1]) <= WITHIN_LITRES + 1e-9
    except ValueError:
        return False


def wrong_lines():
    """(lines wrong, lines in all, a remark on each wrong line)."""
    sealed = json.loads(SEALED.read_text())
    lines, why = answers()
    if lines is None:
        return len(sealed), len(sealed), [why]
    wrong = ["%s: %s, sealed %s" % (k, lines.get(k, "no line"), sealed[k])
             for k in sorted(sealed) if not line_is_right(lines.get(k), sealed[k])]
    return len(wrong), len(sealed), wrong
