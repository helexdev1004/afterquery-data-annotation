"""Marks /app/drying_times.json against the sealed table.

The file is parsed as JSON. Nothing the agent wrote is imported or run.
"""
import json
import pathlib

TABLE = pathlib.Path("/app/drying_times.json")
SEALED = pathlib.Path("/tests/sealed.json")
ENTRIES_THAT_MAY_BE_WRONG = 4
HOURS_WITHIN = 0.1


def submitted():
    """The table as written, or (None, why not)."""
    if not TABLE.is_file():
        return None, "no /app/drying_times.json was written"
    try:
        said = json.loads(TABLE.read_text())
    except Exception as trouble:                              # noqa: BLE001
        return None, "/app/drying_times.json is not JSON: %s" % trouble
    if not isinstance(said, dict):
        return None, "/app/drying_times.json is not one JSON object"
    return said, ""


def agrees(said, want):
    if not isinstance(said, dict) or said.get("resin") != want["resin"]:
        return False
    hours = said.get("hours")
    if isinstance(hours, bool) or not isinstance(hours, (int, float)):
        return False
    return abs(hours - want["hours"]) <= HOURS_WITHIN + 1e-9


def mark():
    """(entries wrong, entries in all, what was wrong with each)."""
    sealed = json.loads(SEALED.read_text())
    said, why_not = submitted()
    if said is None:
        return len(sealed), len(sealed), [why_not]
    wrong = ["%s: %s, should be %s" % (h, said.get(h, "no entry"), sealed[h])
             for h in sorted(sealed) if not agrees(said.get(h), sealed[h])]
    return len(wrong), len(sealed), wrong
