"""Mark the dig sheet. The answer is data; nothing the agent wrote is run."""

from __future__ import annotations

import csv
import json
import pathlib

TESTS = pathlib.Path("/tests")
ANSWER = pathlib.Path("/app/dig_sheet.csv")
MAY_BE_WRONG = 4
WITHIN_M = 2.0


def truth():
    return json.loads((TESTS / "truth.json").read_text())


def submitted():
    if not ANSWER.is_file():
        return None, "nothing was left at /app/dig_sheet.csv"
    try:
        with open(ANSWER, newline="") as handle:
            table = list(csv.DictReader(handle))
    except Exception as exc:                                  # noqa: BLE001
        return None, "/app/dig_sheet.csv could not be read: %s" % exc
    out = {}
    for row in table:
        alarm = (row.get("alarm") or "").strip()
        if alarm:
            out[alarm] = ((row.get("from_a_m") or "").strip(),
                          (row.get("duct") or "").strip())
    return out, ""


def agrees(said, want):
    far, duct = want.split(None, 1)
    if said is None or said[1] != duct:
        return False
    try:
        return abs(float(said[0]) - float(far)) <= WITHIN_M + 1e-9
    except ValueError:
        return False


def grade():
    want = truth()
    got, trouble = submitted()
    if got is None:
        return len(want), len(want), [trouble]

    wrong = []
    for alarm in sorted(want):
        said = got.get(alarm)
        if not agrees(said, want[alarm]):
            wrong.append("%s: %s against %s"
                         % (alarm, "no row" if said is None
                            else "%s %s" % said, want[alarm]))
    return len(wrong), len(want), wrong
