"""Score the submitted inspection report against the sealed one.

The report is DATA, not code: the verifier reads a JSON file and never
executes anything the submission wrote. There is nothing to sandbox.
"""

from __future__ import annotations

import json
import pathlib

TESTS = pathlib.Path("/tests")
REPORT = pathlib.Path("/app/inspection.json")
EXPECTED = TESTS / "expected"

PASS_MARK = 50
VALUE_TOLERANCE = 0.004


def expected_reports() -> dict:
    out = {}
    for path in sorted(EXPECTED.glob("*.json")):
        doc = json.loads(path.read_text())
        out[doc["plate"]] = doc["callouts"]
    return out


def load_submission():
    if not REPORT.is_file():
        return None, "no report was left at /app/inspection.json"
    try:
        doc = json.loads(REPORT.read_text())
    except Exception as exc:
        return None, f"/app/inspection.json is not readable JSON: {exc}"
    if isinstance(doc, dict) and "plates" in doc:
        doc = doc["plates"]
    if not isinstance(doc, list):
        return None, "the report should be a list of plates"
    index = {}
    for entry in doc:
        if not isinstance(entry, dict):
            continue
        name = entry.get("plate")
        callouts = entry.get("callouts")
        if isinstance(name, str) and isinstance(callouts, list):
            index[name] = callouts
    return index, ""


def grade() -> tuple[int, int, list[str]]:
    expected = expected_reports()
    submitted, problem = load_submission()
    total = sum(len(v) for v in expected.values())
    if submitted is None:
        return 0, total, [problem]

    right = 0
    wrong = []
    for plate, callouts in sorted(expected.items()):
        got = submitted.get(plate)
        if got is None:
            wrong.append(f"{plate}: missing from the report")
            continue
        index = {}
        for c in got:
            if isinstance(c, dict) and "callout" in c and "feature" in c:
                index[(c["callout"], c["feature"])] = c
        for want in callouts:
            key = (want["callout"], want["feature"])
            have = index.get(key)
            if have is None:
                wrong.append(f"{plate} {key[0]} {key[1]}: missing")
                continue
            try:
                value = float(have.get("actual"))
            except (TypeError, ValueError):
                wrong.append(f"{plate} {key[0]} {key[1]}: no numeric actual")
                continue
            verdict_ok = bool(have.get("pass")) == bool(want["pass"])
            value_ok = abs(value - want["actual"]) <= VALUE_TOLERANCE
            if verdict_ok and value_ok:
                right += 1
            elif not verdict_ok:
                wrong.append(f"{plate} {key[0]} {key[1]}: reported "
                             f"{'pass' if have.get('pass') else 'fail'}")
            else:
                wrong.append(f"{plate} {key[0]} {key[1]}: {value:.4f} "
                             f"is not within {VALUE_TOLERANCE} of the measured value")
    return right, total, wrong
