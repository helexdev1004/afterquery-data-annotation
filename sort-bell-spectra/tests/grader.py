"""Score the submitted attribution and tuning book. Both are data; nothing is
executed."""

from __future__ import annotations

import json
import pathlib

TESTS = pathlib.Path("/tests")
TRUTH = TESTS / "truth"
ATTRIBUTION = pathlib.Path("/app/attribution.json")
BOOK = pathlib.Path("/app/tuning.json")

PASS_MARK = 171
CENTS_TOLERANCE = 2.0


def load(path):
    if not path.is_file():
        return None, f"nothing was left at {path}"
    try:
        return json.loads(path.read_text()), ""
    except Exception as exc:                                  # noqa: BLE001
        return None, f"{path} is not readable JSON: {exc}"


def grade_attribution(wrong: list) -> tuple[int, int]:
    want = json.loads((TRUTH / "attribution.json").read_text())
    got, problem = load(ATTRIBUTION)
    if got is None:
        wrong.append(problem)
        return 0, len(want)
    if isinstance(got, dict) and "runs" in got:
        got = got["runs"]
    if not isinstance(got, dict):
        wrong.append("the attribution should be an object of run id -> bell")
        return 0, len(want)
    right = 0
    for run, bell in sorted(want.items()):
        said = got.get(run)
        if isinstance(said, str) and said.strip().lower() == bell:
            right += 1
        elif len(wrong) < 40:
            wrong.append(f"{run}: said {said!r}, was {bell}")
    return right, len(want)


def grade_book(wrong: list) -> tuple[int, int]:
    want = {}
    for path in sorted(TRUTH.glob("bell-*.json")):
        doc = json.loads(path.read_text())
        want[doc["bell"]] = doc["partials"]
    total = sum(len(v) for v in want.values())

    got, problem = load(BOOK)
    if got is None:
        wrong.append(problem)
        return 0, total
    if isinstance(got, dict) and "bells" in got:
        got = got["bells"]
    if not isinstance(got, list):
        wrong.append("the tuning book should be a list of bells")
        return 0, total
    index = {}
    for entry in got:
        if isinstance(entry, dict) and isinstance(entry.get("partials"), list):
            index[entry.get("bell")] = entry["partials"]

    right = 0
    for bell, partials in sorted(want.items()):
        reported = index.get(bell)
        if reported is None:
            wrong.append(f"{bell}: missing from the book")
            continue
        seen = {}
        for p in reported:
            if isinstance(p, dict) and "partial" in p:
                seen[p["partial"]] = p
        for expected in partials:
            name = expected["partial"]
            have = seen.get(name)
            if have is None:
                wrong.append(f"{bell} {name}: missing")
                continue
            try:
                value = float(have.get("cents"))
            except (TypeError, ValueError):
                wrong.append(f"{bell} {name}: no numeric cents")
                continue
            if (abs(value - expected["cents"]) <= CENTS_TOLERANCE
                    and bool(have.get("in_true")) == bool(expected["in_true"])):
                right += 1
            elif len(wrong) < 40:
                wrong.append(f"{bell} {name}: {value:+.1f} against "
                             f"{expected['cents']:+.1f}")
    return right, total


def grade() -> tuple[int, int, list[str]]:
    wrong: list[str] = []
    a_right, a_total = grade_attribution(wrong)
    b_right, b_total = grade_book(wrong)
    return a_right + b_right, a_total + b_total, wrong
