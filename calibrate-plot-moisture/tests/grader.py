"""Checks /app/plot_moisture.json against the sealed figures for the ten plots.

The file is read with the json module. No code belonging to the agent is
imported or executed.
"""
import json
import pathlib

ANSWER = pathlib.Path("/app/plot_moisture.json")
SEALED = pathlib.Path("/tests/sealed.json")
WITHIN = 0.002
KEYS = ("mean_vwc", "driest_daily_vwc")


def answer():
    """The agent's object with plot codes upper-cased, or a string saying why not."""
    if not ANSWER.is_file():
        return "/app/plot_moisture.json is missing"
    try:
        loaded = json.loads(ANSWER.read_text())
    except Exception as why:                                  # noqa: BLE001
        return "/app/plot_moisture.json is not valid JSON: %s" % why
    if not isinstance(loaded, dict):
        return "/app/plot_moisture.json is not an object keyed by plot"
    return {str(k).strip().upper(): v for k, v in loaded.items()}


def plots_out():
    """{plot: what is wrong} for every plot that is not within tolerance."""
    sealed = json.loads(SEALED.read_text())
    given = answer()
    if isinstance(given, str):
        return {plot: given for plot in sealed}
    out = {}
    for plot, want in sealed.items():
        r = given.get(plot)
        if not isinstance(r, dict):
            out[plot] = "no object for this plot"
            continue
        try:
            got = (float(r.get("mean_vwc")), float(r.get("driest_daily_vwc")))
        except (TypeError, ValueError):
            out[plot] = "a figure is missing or not a number"
            continue
        if any(abs(g - want[k]) > WITHIN + 1e-9 for g, k in zip(got, KEYS)):
            out[plot] = "wrote %s, sealed %s" % (got, tuple(want[k] for k in KEYS))
    return out
