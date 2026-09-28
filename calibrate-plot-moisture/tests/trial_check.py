"""Other readings of the trial's records, each marked against the sealed figures.

    python trial_check.py            run the trial afresh in a scratch folder
    python trial_check.py <folder>   use a trial already written there

Readings tried: no quirk undone and the sheet believed; every quirk undone and
the sheet believed; the traces believed but one quirk left in, for each quirk.
The reference reading must get every plot and no other reading may.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import plot_moisture as pm

WITHIN = 0.002


def plots_right(figures, sealed):
    return sum(1 for plot, want in sealed.items()
               if plot in figures and all(abs(figures[plot][k] - want[k]) <= WITHIN + 1e-9
                                          for k in want))


def examine(folder):
    folder = pathlib.Path(folder)
    sealed = json.loads((folder / "sealed.json").read_text())
    ground = json.loads((folder / "ground.json").read_text())
    total = len(sealed)
    figures, seen = pm.work_up(folder)
    assert plots_right(figures, sealed) == total, "the reference misses a plot"
    assert all(ground[p]["probe"] == s["probe"] for p, s in seen.items()), \
        "the traces do not find the probes"
    readings = {"nothing undone, sheet believed": dict(files=(), probes="sheet"),
                "quirks undone, sheet believed": dict(files=pm.QUIRKS, probes="sheet")}
    for quirk in pm.QUIRKS:
        readings["%s left in" % quirk] = dict(
            files=tuple(q for q in pm.QUIRKS if q != quirk), probes="traces")
    scores = {name: plots_right(pm.work_up(folder, **how)[0], sealed)
              for name, how in readings.items()}
    assert max(scores.values()) < total, "another reading gets every plot"
    by_sheet = pm.work_up(folder, probes="sheet")[0]
    gaps = [max(abs(by_sheet[p][k] - sealed[p][k]) for k in sealed[p]) for p in sealed]
    wrong = [g for g in gaps if g > WITHIN]
    swell = {"TDR": [], "capacitance": []}
    for plot, s in seen.items():
        swell[ground[plot]["kind"]].append(s["swell"])
    return dict(total=total, readings=len(scores), best_other=max(scores.values()),
                nothing_undone=scores["nothing undone, sheet believed"],
                sheet_believed=scores["quirks undone, sheet believed"],
                misplaced=sum(1 for g in ground.values() if g["probe"] != g["listed"]),
                hours=1008, least_gap=round(min(wrong), 3),
                capacitance_swell_pct=round(100 * min(swell["capacitance"]), 2),
                tdr_swell_pct=round(100 * max(swell["TDR"]), 2), scores=scores)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        found = examine(sys.argv[1])
    else:
        here = pathlib.Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as scratch:
            subprocess.run([sys.executable, str(here / "run_trial.py"), scratch],
                           check=True, stdout=subprocess.DEVNULL)
            found = examine(scratch)
    print(json.dumps(found, indent=1))
