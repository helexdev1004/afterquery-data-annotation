"""Mark the peaks. The answer is data; nothing the agent wrote is run."""

from __future__ import annotations

import json
import pathlib

TESTS = pathlib.Path("/tests")
ANSWER = pathlib.Path("/app/targets.txt")
BAR = 36


def truth():
    return json.loads((TESTS / "truth.json").read_text())


def submitted():
    if not ANSWER.is_file():
        return None, "nothing was left at /app/targets.txt"
    try:
        lines = ANSWER.read_text().splitlines()
    except Exception as exc:                                  # noqa: BLE001
        return None, "/app/targets.txt could not be read: %s" % exc
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
    for anomaly in sorted(want):
        said = got.get(anomaly)
        if said == want[anomaly]:
            right += 1
        elif len(wrong) < 40:
            wrong.append("%s: %s against %s"
                         % (anomaly, said or "no row", want[anomaly]))
    return right, len(want), wrong
