"""Marks /app/expected_protein.csv against the sealed figures.

The file is read as text with the csv module. Nothing the agent wrote is
imported or run.
"""
import csv
import json
import pathlib

ANSWER = pathlib.Path("/app/expected_protein.csv")
SEALED = pathlib.Path("/tests/sealed.json")
SAMPLES_THAT_MAY_BE_OUT = 4
PROTEIN_WITHIN = 0.05


def lines_written():
    """{sample: (formula, protein as written)} or (None, why not)."""
    if not ANSWER.is_file():
        return None, "no /app/expected_protein.csv was written"
    try:
        with open(ANSWER, newline="") as handle:
            rows = list(csv.DictReader(handle))
    except Exception as trouble:                              # noqa: BLE001
        return None, "/app/expected_protein.csv could not be read: %s" % trouble
    return {(r.get("sample") or "").strip():
            ((r.get("formula") or "").strip(),
             (r.get("protein_pct") or "").strip()) for r in rows}, ""


def good(written, sealed):
    if written is None or written[0] != sealed[0]:
        return False
    try:
        return abs(float(written[1]) - sealed[1]) <= PROTEIN_WITHIN + 1e-9
    except ValueError:
        return False


def mark():
    """(samples out, samples in all, a line about each one out)."""
    sealed = json.loads(SEALED.read_text())
    written, why_not = lines_written()
    if written is None:
        return len(sealed), len(sealed), [why_not]
    out = ["%s: %s, should be %s" % (tag, written.get(tag, "no line"),
                                       sealed[tag])
           for tag in sorted(sealed) if not good(written.get(tag), sealed[tag])]
    return len(out), len(sealed), out
