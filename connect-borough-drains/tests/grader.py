"""Mark the connections. The answer is data; nothing the agent wrote is run."""

from __future__ import annotations

import csv
import json
import pathlib

TESTS = pathlib.Path("/tests")
ANSWER = pathlib.Path("/app/connections.csv")
BAR = 37


def truth():
    return json.loads((TESTS / "truth.json").read_text())


def submitted():
    if not ANSWER.is_file():
        return None, "nothing was left at /app/connections.csv"
    try:
        with open(ANSWER, newline="") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as exc:                                  # noqa: BLE001
        return None, "/app/connections.csv could not be read: %s" % exc
    out = {}
    for row in rows:
        drain = (row.get("drain") or "").strip()
        manhole = (row.get("manhole") or "").strip()
        if drain:
            out[drain] = manhole
    return out, ""


def grade():
    want = truth()
    got, trouble = submitted()
    if got is None:
        return 0, len(want), [trouble]

    right, wrong = 0, []
    for drain in sorted(want):
        said = got.get(drain)
        if said == want[drain]:
            right += 1
        elif len(wrong) < 40:
            wrong.append("%s: %s against %s"
                         % (drain, said or "no row", want[drain]))
    return right, len(want), wrong
