"""Other stances on the downloads, each marked against the sealed means.

    python town_check.py            monitor the town afresh in a scratch folder
    python town_check.py <folder>   use a town already written there

The stances: the note to the letter; the oddities put right and the site list
believed; each oddity left in turn; and each moved analyser put back where the
list has it, one pair at a time. Only the reference stance may get every site.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import no2_report as nr

WITHIN = 0.005


def sites_right(figures, sealed):
    right = 0
    for code, want in sealed.items():
        got = figures.get(code)
        if got and abs(got[0] - want["monitor_mean"]) <= WITHIN * want["monitor_mean"] \
                and abs(got[1] - want["facade_mean"]) <= WITHIN * want["facade_mean"]:
            right += 1
    return right


def weigh(folder):
    folder = pathlib.Path(folder)
    sealed = json.loads((folder / "sealed.json").read_text())
    cabinets = json.loads((folder / "cabinets.json").read_text())
    total = len(sealed)
    figures, shown = nr.report(folder, nr.BY_THE_RECORD)
    assert sites_right(figures, sealed) == total, "the reference misses a site"
    assert all(cabinets[a]["stands_at"] == v["stands"] for a, v in shown.items()), \
        "the records do not place the analysers"
    scores = {"to the letter": sites_right(nr.report(folder, nr.TO_THE_LETTER)[0], sealed),
              "oddities put right, list believed":
                  sites_right(nr.report(folder, nr.BY_THE_LIST)[0], sealed)}
    for oddity in nr.ODDITIES:
        stance = (frozenset(o for o in nr.ODDITIES if o != oddity), "record")
        scores["%s left in" % oddity] = sites_right(nr.report(folder, stance)[0], sealed)
    assert max(scores.values()) < total, "another stance gets every site"
    roads = [v["liveliness"] for a, v in shown.items() if cabinets[a]["type"] == "roadside"]
    parks = [v["liveliness"] for a, v in shown.items() if cabinets[a]["type"] != "roadside"]
    listed = nr.report(folder, nr.BY_THE_LIST)[0]
    misses = [max(abs(listed[c][0] - w["monitor_mean"]) / w["monitor_mean"],
                  abs(listed[c][1] - w["facade_mean"]) / w["facade_mean"])
              for c, w in sealed.items()]
    moved = [m for m in misses if m > WITHIN]
    return dict(total=total, stances=len(scores), best_other=max(scores.values()),
                to_the_letter=scores["to the letter"],
                list_believed=scores["oddities put right, list believed"],
                moved=sum(1 for c in cabinets.values() if c["stands_at"] != c["listed_at"]),
                rows=5376, least_miss_pct=round(100 * min(moved), 1),
                road_liveliness=round(min(roads), 2), park_liveliness=round(max(parks), 2),
                scores=scores)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        found = weigh(sys.argv[1])
    else:
        here = pathlib.Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as scratch:
            subprocess.run([sys.executable, str(here / "monitor_town.py"), scratch],
                           check=True, stdout=subprocess.DEVNULL)
            found = weigh(scratch)
    print(json.dumps(found, indent=1))
