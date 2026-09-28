"""Mark the recall. The answer is data; nothing the agent wrote is run."""

from __future__ import annotations

import json
import pathlib

TESTS = pathlib.Path("/tests")
ANSWER = pathlib.Path("/app/recall.json")
MAY_BE_WRONG = 4


def truth():
    return json.loads((TESTS / "truth.json").read_text())


def submitted():
    if not ANSWER.is_file():
        return None, "nothing was left at /app/recall.json"
    try:
        loaded = json.loads(ANSWER.read_text())
    except Exception as exc:                                  # noqa: BLE001
        return None, "/app/recall.json could not be read: %s" % exc
    if not isinstance(loaded, dict):
        return None, "/app/recall.json could not be read: not a JSON object"
    return {str(k).strip(): str(v).strip() for k, v in loaded.items()}, ""


def grade():
    want = truth()
    got, trouble = submitted()
    if got is None:
        return len(want), len(want), [trouble]

    wrong = []
    for fault in sorted(want):
        said = got.get(fault)
        if said != want[fault]:
            wrong.append("%s: %s against %s"
                         % (fault, said or "no entry", want[fault]))
    return len(wrong), len(want), wrong
