"""The laziest program that could be handed in: the note's arithmetic and
nothing else, every plate taken to have gone into the reader the way the
lay-out is written.  It is here to show what that scores; nothing runs it.

On the marker's unseen days it gets about three lines in four right, because
every line of a plate that went in end for end is some other mosquito's figure,
and nine in ten are needed.
"""
import json
import math
import sys


def od(value, mode):
    if mode == "milli-absorbance":
        return value / 1000.0
    if mode == "transmittance":
        return -math.log10(value / 100.0)
    return value


def slope(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


for plate in json.load(sys.stdin)["plates"]:
    scale = 1.0 if plate["time_unit"] == "min" else 1.0 / 60.0
    minutes = [t * scale for t in plate["read_times"]]
    series = {w: [od(v, plate["mode"]) for v in vs] for w, vs in plate["reads"].items()}
    rate = {w: slope(minutes, ys) for w, ys in series.items()}
    roles = plate["layout"]
    blanks = [rate[w] for w, d in roles.items() if d["role"] == "blank"]
    blank = sum(blanks) / len(blanks)
    ladder = [(d["nmol"], sum(series[w]) / len(series[w]))
              for w, d in roles.items() if d["role"] == "standard"]
    per_nmol = slope([a for a, _ in ladder], [b for _, b in ladder])
    to_25 = 2.0 ** ((25.0 - plate["chamber_c"]) / 10.0)
    for w, d in roles.items():
        if d["role"] == "sample":
            print("%s %.2f" % (d["id"], (rate[w] - blank) / per_nmol * d["dilution"] * to_25))
