"""Mark the table of beds. The answer is data; nothing the agent wrote is run."""

from __future__ import annotations

import json
import pathlib

TESTS = pathlib.Path("/tests")
ANSWER = pathlib.Path("/app/beds_for_paper.md")
MAY_BE_WRONG = 4


def truth():
    return json.loads((TESTS / "truth.json").read_text())


def submitted():
    if not ANSWER.is_file():
        return None, "nothing was left at /app/beds_for_paper.md"
    try:
        lines = ANSWER.read_text().splitlines()
    except Exception as exc:                                  # noqa: BLE001
        return None, "/app/beds_for_paper.md could not be read: %s" % exc
    out = {}
    for line in lines:
        if "|" not in line:
            continue
        cells = [cell.strip().strip("`") for cell in
                 line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and not set(cells[0]) <= set("-: "):
            out[cells[0]] = cells[1]
    return out, ""


def grade():
    want = truth()
    got, trouble = submitted()
    if got is None:
        return len(want), len(want), [trouble]

    wrong = []
    for sample in sorted(want):
        said = got.get(sample)
        if said != want[sample]:
            wrong.append("%s: %s against %s"
                         % (sample, said or "no row", want[sample]))
    return len(wrong), len(want), wrong
