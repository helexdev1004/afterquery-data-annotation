"""Every reading of the bench recordings, scored against the sealed figures.

    python bench_check.py            regenerate the bench in a scratch folder
    python bench_check.py <folder>   use a bench already written there

Sixteen readings: each of the three channel habits taken as the recordings
show it or as the note says, and the probes taken as mapped or as the ripple
on each rail says. Only the recordings' reading may close the budget.
"""
import itertools
import json
import pathlib
import subprocess
import sys
import tempfile

import power_budget as pb

WITHIN = 0.005
ALLOWED_WRONG = 2
CHOICES = {"millivolts": ("to_volts", "as_volts"),
           "microvolts": ("to_millivolts", "as_millivolts"),
           "reversed": ("take_the_size", "as_logged"),
           "probes": ("ask_the_ripple", "as_mapped")}


def right(got, sealed):
    return sum(1 for k, v in sealed.items()
               if k in got and abs(got[k] - v) <= WITHIN * abs(v) + 1e-9)


def ladder(folder, sealed):
    rungs = []
    names = sorted(CHOICES)
    for picks in itertools.product(*(CHOICES[n] for n in names)):
        reading = dict(zip(names, picks))
        got, _ = pb.budget(folder, reading)
        rungs.append((right(got, sealed), reading))
    return sorted(rungs, key=lambda r: -r[0])


def facts(folder):
    folder = pathlib.Path(folder)
    sealed = json.loads((folder / "sealed.json").read_text())
    clips = json.loads((folder / "clips.json").read_text())
    rungs = ladder(folder, sealed)
    total = len(sealed)
    assert rungs[0][0] == total and rungs[0][1] == pb.THE_RECORDINGS, \
        "the recordings' reading does not get every line"
    assert rungs[1][0] < total - ALLOWED_WRONG, "a wrong reading closes the budget"
    _, seen = pb.budget(folder, pb.THE_RECORDINGS)
    assert all(clips[s["rail"]]["probe"] == p for p, s in seen.items()), \
        "the ripple does not find the clips"
    bucks = [s["ripple"] for s in seen.values()
             if clips[s["rail"]]["regulator"] == "buck"]
    ldos = [s["ripple"] for s in seen.values()
            if clips[s["rail"]]["regulator"] == "LDO"]
    without = {}
    for name in CHOICES:
        reading = dict(pb.THE_RECORDINGS)
        reading[name] = CHOICES[name][1]
        without[name] = right(pb.budget(folder, reading)[0], sealed)
    with open(folder / "phase_active.csv") as handle:
        samples = sum(1 for _ in handle) - 1
    return dict(total=total, readings=len(rungs), second=rungs[1][0],
                by_note=[n for n, r in rungs if r == pb.THE_NOTE][0],
                without=without, samples=samples,
                crossed=sum(1 for p, s in seen.items() if s["mapped"] != s["rail"]),
                gap=int(min(bucks) / max(ldos)))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        found = facts(sys.argv[1])
    else:
        here = pathlib.Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as scratch:
            subprocess.run([sys.executable, str(here / "bench_run.py"), scratch],
                           check=True, stdout=subprocess.DEVNULL)
            found = facts(scratch)
    print(json.dumps(found, indent=1))
