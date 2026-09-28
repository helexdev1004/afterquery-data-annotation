"""Esterase activity of every homogenate on an assay day.

    python3 activities.py < day.json

One line a homogenate, `M-041207 38.61`: nmol of p-nitrophenol a minute for the
whole mosquito, brought to 25 C.
"""
import json
import sys

ROWS = "ABCDEFGH"
Q10 = 2.0


def absorbance(value, mode):
    import math
    if mode == "absorbance":
        return value
    if mode == "milli-absorbance":
        return value / 1000.0
    return -math.log10(value / 100.0)


def line_through(xs, ys, ws=None):
    ws = ws or [1.0] * len(xs)
    sw = sum(ws)
    mx = sum(w * x for w, x in zip(ws, xs)) / sw
    my = sum(w * y for w, y in zip(ws, ys)) / sw
    sxx = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    sxy = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys))
    slope = sxy / sxx
    return slope, my - slope * mx


def turned(name):
    return "%s%d" % (ROWS[7 - ROWS.index(name[0])], 13 - int(name[1:]))


def fits(plate):
    """Slope in OD a minute and level at the first read, by the reader's well names."""
    per_min = 1.0 if plate["time_unit"] == "min" else 1.0 / 60.0
    minutes = [t * per_min for t in plate["read_times"]]
    out = {}
    for name, series in plate["reads"].items():
        od = [absorbance(v, plate["mode"]) for v in series]
        out[name] = line_through(minutes, od)
    return out


def carry_over(plate, fitted):
    """By the reader's well names, how far a well's departures from its line
    follow one another: near nothing for a clear well, well above it for a
    cloudy one, whose reads wander where a clear one's scatter."""
    per_min = 1.0 if plate["time_unit"] == "min" else 1.0 / 60.0
    minutes = [t * per_min for t in plate["read_times"]]
    out = {}
    for name, series in plate["reads"].items():
        slope, level = fitted[name]
        off = [absorbance(v, plate["mode"]) - level - slope * t
               for v, t in zip(series, minutes)]
        out[name] = sum(a * b for a, b in zip(off, off[1:])) / sum(a * a for a in off)
    return out


def went_in_end_for_end(plate, fitted):
    """Do the wandering wells sit where the lay-out has the crude homogenates,
    or where it would have them with the plate turned round?

    The lay-out of roles reads the same either way round, so blanks and
    standards cannot say.  The spread of a well's reads about its line cannot
    either: it is the same for a crude homogenate as a spun one.
    """
    carried = carry_over(plate, fitted)

    def apart(at):
        crude, spun = [], []
        for w, d in plate["layout"].items():
            if d["role"] == "sample":
                (crude if d["prep"] == "crude" else spun).append(carried[at(w)])
        if not crude or not spun:
            return 0.0
        return sum(crude) / len(crude) - sum(spun) / len(spun)

    return apart(turned) > apart(lambda w: w)


def work_up(day, judge="evidence"):
    answers = []
    for plate in day["plates"]:
        fitted = fits(plate)
        if judge == "evidence":
            flip = went_in_end_for_end(plate, fitted)
        else:
            flip = False
        at = (lambda w: turned(w)) if flip else (lambda w: w)
        layout = plate["layout"]
        blanks = [w for w, d in layout.items() if d["role"] == "blank"]
        ladder = [w for w, d in layout.items() if d["role"] == "standard"]
        blank_rate = sum(fitted[at(w)][0] for w in blanks) / len(blanks)
        mean_od = {}
        for w in ladder:
            series = [absorbance(v, plate["mode"]) for v in plate["reads"][at(w)]]
            mean_od[w] = sum(series) / len(series)
        xs = [layout[w]["nmol"] for w in ladder]
        ys = [mean_od[w] for w in ladder]
        od_per_nmol, _ = line_through(xs, ys)
        to_25 = Q10 ** ((25.0 - plate["chamber_c"]) / 10.0)
        for w, d in layout.items():
            if d["role"] != "sample":
                continue
            rate = fitted[at(w)][0] - blank_rate
            answers.append((d["id"], rate / od_per_nmol * d["dilution"] * to_25))
    return answers


if __name__ == "__main__":
    for ident, value in work_up(json.load(sys.stdin)):
        print("%s %.2f" % (ident, value))
