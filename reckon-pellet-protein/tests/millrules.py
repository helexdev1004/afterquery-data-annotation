"""The mill's note, as arithmetic."""

import bisect
import datetime as dt

EPOCH = dt.datetime(2026, 1, 1)
LOG_EVERY_S = 10
LB_PER_TONNE = 2204.62262
PROTEIN_WITHIN = 0.05


def clock(text):
    """'2026-10-05 07:31:20' -> seconds since the start of 2026."""
    return (dt.datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
            - EPOCH).total_seconds()


def as_clock(seconds):
    return (EPOCH + dt.timedelta(seconds=round(seconds))).strftime(
        "%Y-%m-%d %H:%M:%S")


def as_fed(protein_pct, moisture_pct, basis):
    """An assay on a dry-matter basis brought to the ingredient as it is fed."""
    if basis == "dry matter":
        return protein_pct * (1.0 - moisture_pct / 100.0)
    return protein_pct


def formula_protein(recipe, assays):
    """As-fed crude protein of a formula, per cent: `recipe` is a list of
    (ingredient, inclusion per cent), `assays` maps ingredient to (protein,
    moisture, basis)."""
    return sum(share / 100.0 * as_fed(*assays[name]) for name, share in recipe)


def time_at(times, tonnes, reading):
    """When a press's counter stood at `reading`, on the straight line between
    the two log lines either side of it."""
    k = bisect.bisect_left(tonnes, reading)
    if k == 0:
        return times[0]
    if k >= len(tonnes):
        return times[-1]
    t0, t1, a, b = times[k - 1], times[k], tonnes[k - 1], tonnes[k]
    return t0 if b == a else t0 + (t1 - t0) * (reading - a) / (b - a)


def formula_in(changes, moment):
    """The formula a bin held at `moment`: `changes` is [(time, formula)]."""
    k = bisect.bisect_right([t for t, _ in changes], moment) - 1
    return changes[k][1] if k >= 0 else None
