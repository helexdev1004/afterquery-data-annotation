"""Compares /app/breakthrough.csv with the sealed figures for the eight columns.

The file is opened with the csv module and nothing else; no code written by
the agent is imported or run.
"""
import csv
import json
import pathlib

ANSWER = pathlib.Path("/app/breakthrough.csv")
SEALED = pathlib.Path("/tests/sealed.json")
NET_WITHIN = 0.005
SECONDS_WITHIN = 0.5


def answer_lines():
    """({column: (net_counts text, mean_residence_s text)}, '') or (None, why not)."""
    if not ANSWER.is_file():
        return None, "/app/breakthrough.csv does not exist"
    lines = {}
    try:
        with open(ANSWER, newline="") as handle:
            for r in csv.DictReader(handle):
                column = (r.get("column") or "").strip()
                lines[column] = ((r.get("net_counts") or "").strip(),
                                 (r.get("mean_residence_s") or "").strip())
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/breakthrough.csv could not be parsed: %s" % why
    return lines, ""


def agrees(line, sealed):
    if not line:
        return False
    try:
        net, seconds = float(line[0]), float(line[1])
    except ValueError:
        return False
    return abs(net - sealed[0]) <= NET_WITHIN * abs(sealed[0]) + 1e-9 \
        and abs(seconds - sealed[1]) <= SECONDS_WITHIN + 1e-9


def tally():
    """(columns wrong, columns in all, a remark for each wrong one)."""
    sealed = json.loads(SEALED.read_text())
    lines, why = answer_lines()
    if lines is None:
        return len(sealed), len(sealed), [why]
    remarks = ["%s: wrote %s, sealed %s" % (c, lines.get(c, "no line"), sealed[c])
               for c in sorted(sealed) if not agrees(lines.get(c), sealed[c])]
    return len(remarks), len(sealed), remarks
