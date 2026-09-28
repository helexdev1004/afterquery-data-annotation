"""Mark the ring numbers. The answer is data; nothing the agent wrote is run."""

from __future__ import annotations

import json
import pathlib

TESTS = pathlib.Path("/tests")
ANSWER = pathlib.Path("/app/rings.tsv")
ENOUGH = 36


def truth():
    return json.loads((TESTS / "truth.json").read_text())


def submitted():
    if not ANSWER.is_file():
        return None, "nothing was left at /app/rings.tsv"
    try:
        lines = ANSWER.read_text().splitlines()
    except Exception as exc:                                  # noqa: BLE001
        return None, "/app/rings.tsv could not be read: %s" % exc
    out = {}
    for line in lines:
        parts = line.split()
        if len(parts) == 2:
            out[parts[0]] = parts[1]
    return out, ""


def grade():
    want = truth()
    got, trouble = submitted()
    if got is None:
        return 0, len(want), [trouble]

    right, wrong = 0, []
    for defect in sorted(want):
        said = got.get(defect)
        if said == want[defect]:
            right += 1
        else:
            wrong.append("%s: %s against %s"
                         % (defect, said or "no line", want[defect]))
    return right, len(want), wrong
