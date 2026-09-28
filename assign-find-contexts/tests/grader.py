"""Mark the contexts. The answer is data; nothing the agent wrote is run."""

from __future__ import annotations

import csv
import json
import pathlib

TESTS = pathlib.Path("/tests")
ANSWER = pathlib.Path("/app/contexts.csv")
BAR = 36


def truth():
    return json.loads((TESTS / "truth.json").read_text())


def submitted():
    if not ANSWER.is_file():
        return None, "nothing was left at /app/contexts.csv"
    try:
        with open(ANSWER, newline="") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as exc:                                  # noqa: BLE001
        return None, "/app/contexts.csv could not be read: %s" % exc
    out = {}
    for row in rows:
        find = (row.get("find") or "").strip()
        context = (row.get("context") or "").strip()
        if find:
            out[find] = context
    return out, ""


def grade():
    want = truth()
    got, trouble = submitted()
    if got is None:
        return 0, len(want), [trouble]

    right, wrong = 0, []
    for find in sorted(want):
        said = got.get(find)
        if said == want[find]:
            right += 1
        elif len(wrong) < 40:
            wrong.append("%s: %s against %s"
                         % (find, said or "no row", want[find]))
    return right, len(want), wrong
