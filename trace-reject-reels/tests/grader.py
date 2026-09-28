"""Checks /app/reject_reels.csv against the sealed reels and calipers.

The agent's file is read with the csv module. Nothing the agent wrote is
imported or executed.
"""
import csv
import json
import pathlib

CLAIM = pathlib.Path("/app/reject_reels.csv")
SEALED = pathlib.Path("/tests/sealed.json")
LINES_THAT_MAY_BE_OUT = 4
WITHIN_UM = 2


def claim_lines():
    """({reject: (reel, caliper as written)}, '') or (None, the reason)."""
    if not CLAIM.is_file():
        return None, "no /app/reject_reels.csv"
    try:
        with open(CLAIM, newline="") as handle:
            return {(r.get("reject") or "").strip():
                    ((r.get("reel") or "").strip(),
                     (r.get("caliper_um") or "").strip())
                    for r in csv.DictReader(handle)}, ""
    except Exception as why:                                  # noqa: BLE001
        return None, "/app/reject_reels.csv does not read: %s" % why


def placed(line, sealed):
    if line is None or line[0] != sealed[0]:
        return False
    try:
        return abs(float(line[1]) - sealed[1]) <= WITHIN_UM + 1e-9
    except ValueError:
        return False


def misplaced():
    """(lines out, lines in all, a word on each line out)."""
    sealed = json.loads(SEALED.read_text())
    lines, reason = claim_lines()
    if lines is None:
        return len(sealed), len(sealed), [reason]
    out = ["%s: %s, sealed %s" % (t, lines.get(t, "no line"), sealed[t])
           for t in sorted(sealed) if not placed(lines.get(t), sealed[t])]
    return len(out), len(sealed), out
