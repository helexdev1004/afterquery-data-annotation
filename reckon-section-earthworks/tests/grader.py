"""Marks /app/areas.csv against the sealed figures.

The sheet is read as text with the csv module; nothing the agent wrote is
imported or run.
"""
import csv
import json
import pathlib

SHEET = pathlib.Path("/app/areas.csv")
SEALED = pathlib.Path("/tests/sealed.json")
ROWS_ALLOWED_WRONG = 4
AREA_WITHIN = 0.2
COLUMNS = ("cut_m2", "fill_m2", "strip_m2")


def rows_written():
    """{section: [cut, fill, strip] as written} or (None, why not)."""
    if not SHEET.is_file():
        return None, "no /app/areas.csv was written"
    try:
        with open(SHEET, newline="") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as trouble:                              # noqa: BLE001
        return None, "/app/areas.csv could not be read: %s" % trouble
    return {(r.get("section") or "").strip():
            [(r.get(c) or "").strip() for c in COLUMNS] for r in rows}, ""


def close_enough(written, sealed):
    try:
        return all(abs(float(w) - s) <= AREA_WITHIN + 1e-9
                   for w, s in zip(written, sealed))
    except (TypeError, ValueError):
        return False


def mark():
    """(rows wrong, rows in all, a line about each wrong row)."""
    sealed = json.loads(SEALED.read_text())
    written, why_not = rows_written()
    if written is None:
        return len(sealed), len(sealed), [why_not]
    wrong = ["%s: %s, should be %s" % (k, written.get(k, "no row"), sealed[k])
             for k in sorted(sealed)
             if k not in written or not close_enough(written[k], sealed[k])]
    return len(wrong), len(sealed), wrong
