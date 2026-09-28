"""Mark the grades. The answer is data; nothing the agent wrote is run."""

from __future__ import annotations

import csv
import json
import pathlib

TESTS = pathlib.Path("/tests")
ANSWER = pathlib.Path("/app/grades.csv")
BAR = 36


def truth():
    return json.loads((TESTS / "truth.json").read_text())


def submitted():
    if not ANSWER.is_file():
        return None, "nothing was left at /app/grades.csv"
    try:
        with open(ANSWER, newline="") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as exc:                                  # noqa: BLE001
        return None, "/app/grades.csv could not be read: %s" % exc
    out = {}
    for row in rows:
        board = (row.get("board") or "").strip()
        grade = (row.get("grade") or "").strip()
        if board:
            out[board] = grade
    return out, ""


def grade():
    want = truth()
    got, trouble = submitted()
    if got is None:
        return 0, len(want), [trouble]

    right, wrong = 0, []
    for board in sorted(want):
        said = got.get(board)
        if said == want[board]:
            right += 1
        elif len(wrong) < 40:
            wrong.append("%s: %s against %s"
                         % (board, said or "no row", want[board]))
    return right, len(want), wrong
