"""Score the submitted trial numbers. The answer is data; nothing is executed."""

from __future__ import annotations

import csv
import json
import pathlib

TESTS = pathlib.Path("/tests")
ANSWER = pathlib.Path("/app/trials.csv")
PASS_MARK = 37


def truth() -> dict:
    return json.loads((TESTS / "truth.json").read_text())


def submitted():
    if not ANSWER.is_file():
        return None, "nothing was left at /app/trials.csv"
    try:
        with open(ANSWER, newline="") as fh:
            rows = list(csv.DictReader(fh))
    except Exception as exc:                                  # noqa: BLE001
        return None, f"/app/trials.csv is not readable: {exc}"
    out = {}
    for row in rows:
        name = (row.get("chronometer") or "").strip()
        figure = (row.get("trial_number") or "").strip()
        if name:
            out[name] = figure
    return out, ""


def grade() -> tuple[int, int, list[str]]:
    want = truth()
    got, problem = submitted()
    if got is None:
        return 0, len(want), [problem]

    right, wrong = 0, []
    for name in sorted(want):
        said = got.get(name)
        if said is None:
            wrong.append(f"{name}: no row")
            continue
        try:
            value = int(said)
        except ValueError:
            wrong.append(f"{name}: {said!r} is not a whole number")
            continue
        if value == want[name]:
            right += 1
        elif len(wrong) < 40:
            wrong.append(f"{name}: {value} against {want[name]}")
    return right, len(want), wrong
