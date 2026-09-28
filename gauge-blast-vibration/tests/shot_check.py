"""Alternative accounts of the loggers' files, each marked against the sealed peaks.

    python shot_check.py            fire the shot afresh in a scratch folder
    python shot_check.py <folder>   use a shot already written there

An account is the reference reading with some beliefs switched back to what the
note says. The accounts tried are the note throughout, each single belief
switched back, and the three file habits put right with the station stamps
believed. The reference must get every station; no other account may.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import blast_pgv as bp

PGV_WITHIN, SECONDS_WITHIN = 0.01, 0.02


def stations_right(got, sealed):
    return sum(1 for station, (pgv, at) in sealed.items()
               if station in got
               and abs(got[station][0] - pgv) <= PGV_WITHIN * pgv + 1e-9
               and abs(got[station][1] - at) <= SECONDS_WITHIN + 1e-9)


def accounts():
    yield "the note throughout", dict(bp.BY_THE_NOTE)
    for belief in bp.BY_THE_FILES:
        account = dict(bp.BY_THE_FILES)
        account[belief] = bp.BY_THE_NOTE[belief]
        yield "%s as the note has it" % belief, account


def sift(folder):
    folder = pathlib.Path(folder)
    sealed = json.loads((folder / "sealed.json").read_text())
    service = json.loads((folder / "service.json").read_text())
    total = len(sealed)
    got, files = bp.report(folder, bp.BY_THE_FILES)
    assert stations_right(got, sealed) == total, "the reference misses a station"
    assert all(service[name[:-6]]["stood_at"] == f["station"] for name, f in files.items()), \
        "the quiet minute does not place the loggers"
    scores = {name: stations_right(bp.report(folder, account)[0], sealed)
              for name, account in accounts()}
    assert max(scores.values()) < total, "another account gets every station"
    smooth = [f["jumpiness"] for n, f in files.items() if service[n[:-6]]["kind"] == "broadband"]
    rough = [f["jumpiness"] for n, f in files.items() if service[n[:-6]]["kind"] == "geophone"]
    return dict(total=total, accounts=len(scores), best_other=max(scores.values()),
                by_note=scores["the note throughout"],
                stamps_believed=scores["stamps as the note has it"],
                moved=sum(1 for s in service.values() if s["stood_at"] != s["stamps"]),
                samples=len(next(iter(files.values()))["samples"]),
                broadband_jumpiness=round(max(smooth), 2),
                geophone_jumpiness=round(min(rough), 2), scores=scores)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        found = sift(sys.argv[1])
    else:
        here = pathlib.Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as scratch:
            subprocess.run([sys.executable, str(here / "fire_shot.py"), scratch],
                           check=True, stdout=subprocess.DEVNULL)
            found = sift(scratch)
    print(json.dumps(found, indent=1))
