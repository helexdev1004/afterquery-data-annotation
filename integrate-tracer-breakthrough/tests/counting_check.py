"""Every reading of the scaler's dump, marked against the sealed figures.

    python counting_check.py            run the columns afresh in a scratch folder
    python counting_check.py <folder>   use a lab run already written there

Sixteen readings: the three block habits taken as the dump shows them or as the
note says, and the cables taken as listed or as each channel's scatter says.
Only the dump's own reading may get every line.
"""
import itertools
import json
import pathlib
import subprocess
import sys
import tempfile

import breakthrough as bt

NET_WITHIN, SECONDS_WITHIN = 0.005, 0.5
WAYS = {"running_total": ("difference", "as_counts"),
        "per_minute": ("divide", "as_counts"),
        "late_start": ("shift", "from_zero"),
        "cables": ("ask_the_scatter", "as_listed")}


def lines_right(got, sealed):
    right = 0
    for column, (net, mean_s) in sealed.items():
        mine = got.get(column)
        if mine and abs(mine[0] - net) <= NET_WITHIN * abs(net) \
                and abs(mine[1] - mean_s) <= SECONDS_WITHIN:
            right += 1
    return right


def every_reading(folder, sealed):
    rungs, names = [], sorted(WAYS)
    for picks in itertools.product(*(WAYS[n] for n in names)):
        reading = dict(zip(names, picks))
        rungs.append((lines_right(bt.work_up(folder, reading)[0], sealed), reading))
    return sorted(rungs, key=lambda r: -r[0])


def facts(folder):
    folder = pathlib.Path(folder)
    sealed = json.loads((folder / "sealed.json").read_text())
    cabling = json.loads((folder / "cabling.json").read_text())
    rungs = every_reading(folder, sealed)
    total = len(sealed)
    assert rungs[0][0] == total and rungs[0][1] == bt.AS_DUMPED, \
        "the dump's own reading does not get every line"
    assert rungs[1][0] < total, "a wrong reading gets every line"
    _, seen = bt.work_up(folder, bt.AS_DUMPED)
    by_channel = {c["channel"]: c for c in cabling.values()}
    assert all(by_channel[ch]["detector"] == s["detector"] for ch, s in seen.items()), \
        "the scatter does not find the cables"
    tubes = [s["scatter"] for ch, s in seen.items() if by_channel[ch]["type"] == "GM"]
    crystals = [s["scatter"] for ch, s in seen.items() if by_channel[ch]["type"] == "NaI"]
    without = {}
    for name in WAYS:
        reading = dict(bt.AS_DUMPED)
        reading[name] = WAYS[name][1]
        without[name] = lines_right(bt.work_up(folder, reading)[0], sealed)
    return dict(total=total, readings=len(rungs), second=rungs[1][0],
                by_note=[n for n, r in rungs if r == bt.AS_NOTED][0],
                without=without,
                bins=max(len(s["counts"]) for s in seen.values()),
                crossed=sum(1 for c in cabling.values() if c["channel"] != c["listed"]),
                tube_scatter=round(max(tubes), 2),
                crystal_scatter=round(min(crystals), 2))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        found = facts(sys.argv[1])
    else:
        here = pathlib.Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as scratch:
            subprocess.run([sys.executable, str(here / "pulse_columns.py"), scratch],
                           check=True, stdout=subprocess.DEVNULL)
            found = facts(scratch)
    print(json.dumps(found, indent=1))
