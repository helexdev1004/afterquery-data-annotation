"""Mark the altitudes. The answer is data; nothing the agent wrote is run."""

from __future__ import annotations

import json
import pathlib

TESTS = pathlib.Path("/tests")
ANSWER = pathlib.Path("/app/probe_altitudes.jsonl")
MAY_BE_WRONG = 4
HALF_METRE = 0.5


def truth():
    return json.loads((TESTS / "truth.json").read_text())


def submitted():
    if not ANSWER.is_file():
        return None, "nothing was left at /app/probe_altitudes.jsonl"
    try:
        lines = ANSWER.read_text().splitlines()
    except Exception as exc:                                  # noqa: BLE001
        return None, "/app/probe_altitudes.jsonl could not be read: %s" % exc
    out = {}
    for line in lines:
        try:
            entry = json.loads(line)
            out[str(entry["reading"])] = (entry.get("altitude_m"),
                                          entry.get("surface"))
        except Exception:                                     # noqa: BLE001
            continue
    return out, ""


def agrees(said, want):
    high, surface = want.split(None, 1)
    if said is None or isinstance(said[0], bool) or said[1] != surface:
        return False
    try:
        return abs(float(said[0]) - float(high)) <= HALF_METRE + 1e-9
    except (TypeError, ValueError):
        return False


def grade():
    want = truth()
    got, trouble = submitted()
    if got is None:
        return len(want), len(want), [trouble]

    wrong = []
    for reading in sorted(want):
        said = got.get(reading)
        if not agrees(said, want[reading]):
            wrong.append("%s: %s against %s"
                         % (reading, "no line" if said is None
                            else "%s %s" % said, want[reading]))
    return len(wrong), len(want), wrong
