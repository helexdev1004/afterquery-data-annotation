"""Compares /app/no2_report.csv with the sealed means, site by site.

The csv module reads the agent's file. Nothing the agent wrote is imported or
run.
"""
import csv
import json
import pathlib

REPORT = pathlib.Path("/app/no2_report.csv")
SEALED = pathlib.Path("/tests/sealed.json")
WITHIN = 0.005


def load_report():
    """Returns {site: (monitor_mean, facade_mean)} as floats where they parse.

    Raises FileNotFoundError or ValueError with a plain message otherwise."""
    if not REPORT.is_file():
        raise FileNotFoundError("/app/no2_report.csv was not written")
    with open(REPORT, newline="") as handle:
        table = list(csv.DictReader(handle))
    if not table:
        raise ValueError("/app/no2_report.csv has no lines")
    out = {}
    for r in table:
        site = (r.get("site") or "").strip().upper()
        try:
            out[site] = (float(r.get("monitor_mean")), float(r.get("facade_mean")))
        except (TypeError, ValueError):
            out[site] = None
    return out


def sites_out():
    """[(site, what is wrong)] for every site not within tolerance."""
    sealed = json.loads(SEALED.read_text())
    report = load_report()
    out = []
    for site in sorted(sealed):
        want = (sealed[site]["monitor_mean"], sealed[site]["facade_mean"])
        got = report.get(site)
        if got is None:
            out.append((site, "no line with two numbers"))
        elif any(abs(g - w) > WITHIN * w + 1e-9 for g, w in zip(got, want)):
            out.append((site, "wrote %s, sealed %s" % (got, want)))
    return out
