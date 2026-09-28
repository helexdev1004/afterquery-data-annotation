"""Work out each sample's expected protein from the shipped records alone.

Nothing here looks at the sealed figures. `IN_FACT` is how the records have to
be read; mill_proof.py scores every other way.

Four of the five press loggers do not log the way the mill's note says: one
counts kilograms, one pounds, one writes what was pressed in each ten seconds
and not the running total, one writes the seconds since its log began and not
the time of day. Each shows at once and each is only a notation.

The fifth thing is not like those. The routing table says which bin feeds
which press, and for two presses it is wrong: a diverter was left over after a
repair, and each has been running off the other's bin. Nothing says so and
nothing breaks - a bin always holds some formula, so every sample gets a
formula and a protein. No mean says it either: a press is fed at a set rate,
whatever the ration. What says it is how evenly the press runs. Some rations
pellet sweetly and some raggedly, so the tonnage pressed from one ten seconds
to the next is steadier on one formula than on another, and that steadiness
steps when the formula in the press's bin changes - the bin it is really
drawing from.
"""

import csv
import math
import pathlib

import millrules

IN_FACT = {"kilograms": "convert", "pounds": "convert",
           "increments": "sum", "elapsed": "to_clock", "routing": "ask_the_press"}
ON_PAPER = {"kilograms": "leave", "pounds": "leave", "increments": "leave",
            "elapsed": "leave", "routing": "as_tabled"}
WINDOW_S = 25 * 60


def sheet(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def base():
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    return yard if (yard / "sealed.json").is_file() else pathlib.Path("/app")


def middle(values):
    values = sorted(values)
    return values[len(values) // 2]


class PressLog:
    def __init__(self, rows, began, counter_at_start, top_reading, reading):
        self.ways = []
        raw_t = [r["time"] for r in rows]
        raw_w = [float(r["tonnes"]) for r in rows]
        if ":" in raw_t[0]:
            self.times = [millrules.clock(t) for t in raw_t]
        else:
            self.ways.append("elapsed")
            shift = millrules.clock(began) if reading["elapsed"] == "to_clock" \
                else 0.0
            self.times = [shift + float(t) for t in raw_t]
        if any(b < a for a, b in zip(raw_w, raw_w[1:])):
            self.ways.append("increments")
            if reading["increments"] == "sum":
                total, summed = counter_at_start, []
                for w in raw_w:
                    total += w
                    summed.append(total)
                raw_w = summed
        unit = 1.0
        # the highest counter reading any sample was tagged with says what
        # the counter is counted in
        if raw_w[-1] > 100 * top_reading:
            way, size = ("pounds", 1 / millrules.LB_PER_TONNE) \
                if raw_w[-1] > 1500 * top_reading else ("kilograms", 0.001)
            self.ways.append(way)
            if reading[way] == "convert":
                unit = size
        self.tonnes = [w * unit for w in raw_w]

    def waver(self):
        """(when, how far a ten seconds' pressing stands from the mean of the
        ten seconds either side of it), stoppages left out."""
        steps = [b - a for a, b in zip(self.tonnes, self.tonnes[1:])]
        usual = middle(steps)
        out = []
        for k in range(1, len(steps) - 1):
            trio = steps[k - 1:k + 2]
            if min(trio) > 0.5 * usual:
                out.append((self.times[k + 1],
                            abs(trio[1] - (trio[0] + trio[2]) / 2.0)))
        return out


def steps_at(wavering, changes):
    """How much the waver steps, up or down, at a bin's changes of formula:
    the mean absolute log ratio of the middle waver after to before."""
    when = [w for w, _ in wavering]
    import bisect
    total, counted = 0.0, 0
    for (t0, _), (t1, _), nxt in zip(changes, changes[1:],
                                     changes[2:] + [(None, None)]):
        lo = max(t1 - WINDOW_S, t0)
        hi = t1 + WINDOW_S if nxt[0] is None else min(t1 + WINDOW_S, nxt[0])
        before = [v for _, v in wavering[bisect.bisect_left(when, lo):
                                         bisect.bisect_left(when, t1)]]
        after = [v for _, v in wavering[bisect.bisect_left(when, t1):
                                        bisect.bisect_left(when, hi)]]
        if len(before) >= 40 and len(after) >= 40:
            total += abs(math.log(max(middle(after), 1e-9)
                                  / max(middle(before), 1e-9)))
            counted += 1
    return total / counted if counted else 0.0


def read_mill(app, reading):
    app = pathlib.Path(app)
    assays = {r["ingredient"]: (float(r["protein_pct"]),
                                float(r["moisture_pct"]), r["basis"])
              for r in sheet(app / "assays.csv")}
    recipes = {}
    for r in sheet(app / "formulas.csv"):
        recipes.setdefault(r["formula"], []).append(
            (r["ingredient"], float(r["inclusion_pct"])))
    protein = {f: millrules.formula_protein(recipe, assays)
               for f, recipe in recipes.items()}
    bins = {}
    for r in sheet(app / "bin_changes.csv"):
        bins.setdefault(r["bin"], []).append((millrules.clock(r["time"]),
                                              r["formula"]))
    for changes in bins.values():
        changes.sort()
    samples = {}
    for tag in (app / "samples.txt").read_text().split():
        press, at = tag.split("@")
        samples.setdefault(press, []).append((tag, float(at)))

    presses = {}
    for r in sheet(app / "routing.csv"):
        name = r["press"]
        top = max(at for _, at in samples.get(name, [("", 1.0)]))
        log = PressLog(sheet(app / "press_logs" / (name + ".csv")),
                       r["log_began"], float(r["counter_at_start_t"]), top,
                       reading)
        wavering = log.waver()
        steps = {b: steps_at(wavering, changes) for b, changes in bins.items()}
        fed_by = max(steps, key=steps.get) \
            if reading["routing"] == "ask_the_press" else r["bin"]
        presses[name] = dict(log=log, tabled=r["bin"], steps=steps,
                             fed_by=fed_by)
    return presses, bins, protein, samples


def expected(app, reading=None):
    presses, bins, protein, samples = read_mill(app, reading or IN_FACT)
    out = {}
    for name, tags in samples.items():
        p = presses[name]
        for tag, at in tags:
            moment = millrules.time_at(p["log"].times, p["log"].tonnes, at)
            formula = millrules.formula_in(bins[p["fed_by"]], moment)
            if formula:
                out[tag] = [formula, round(protein[formula], 2)]
    return out


if __name__ == "__main__":
    import sys

    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else base()
    lines = ["sample,formula,protein_pct"]
    for tag, (formula, value) in sorted(expected(target).items()):
        lines.append("%s,%s,%.2f" % (tag, formula, value))
    (target / "expected_protein.csv").write_text("\n".join(lines) + "\n")
