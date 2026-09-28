"""Run the mill for three days, then write the records the way it keeps them.

    python run_mill.py [outdir]

Truth first. Every bin's changes of formula and every press's pressing happen
on one clock, each press drawing from the bin it is REALLY connected to, and a
sample's expected protein is taken from that. Then the records are written:
the routing table as the office believes it, each press log in its logger's
own notation.

A press is fed at a set rate whatever the ration, a bin is switched on the run,
stoppages fall at random and no two logs begin together, so no mean and no
event ties a press to a bin. What does is second order: how evenly the press
runs from one ten seconds to the next depends on the ration, so it steps when
the bin the press is drawing from changes formula. The plain spread of a
press's rate is mostly its own slow wander and the odd minute of fuss at the
feeder.
"""

import csv
import json
import pathlib
import random
import sys

import millrules

SEED = 2718281
BEGAN = millrules.clock("2026-10-05 00:00:00")
DAYS = 3
SAMPLES_WANTED = 8

PRESSES = (
    # press, bin on the routing table, bin it really draws from, logger's way
    ("P1", "B1", "B1", "kilograms"),
    ("P2", "B2", "B4", None),
    ("P3", "B3", "B3", "increments"),
    ("P4", "B4", "B2", "pounds"),
    ("P5", "B5", "B5", "elapsed"),
)
KEEPERS = ("Asquith", "Broadbent", "Clough", "Dewhirst", "Entwhistle")
INGREDIENTS = (
    # name, protein %, moisture %, the basis its assay is quoted on
    ("wheat", 11.2, 13.5, "as fed"), ("barley", 10.4, 13.8, "as fed"),
    ("maize", 8.3, 13.0, "as fed"), ("oats", 11.9, 12.5, "dry matter"),
    ("soya bean meal", 53.1, 11.5, "dry matter"),
    ("rapeseed meal", 35.2, 10.8, "as fed"),
    ("sunflower meal", 38.9, 10.2, "dry matter"),
    ("field beans", 25.6, 14.0, "as fed"), ("peas", 23.9, 13.6, "dry matter"),
    ("wheatfeed", 15.8, 12.4, "as fed"),
    ("sugar beet pulp", 9.9, 11.0, "dry matter"),
    ("oat hulls", 4.1, 9.5, "as fed"), ("distillers grains", 30.4, 10.6,
                                        "dry matter"),
    ("molasses", 4.4, 26.0, "as fed"), ("limestone", 0.0, 1.0, "as fed"),
    ("vegetable oil", 0.0, 0.5, "as fed"),
)
RAGGEDNESS_KG = (0.12, 0.28, 0.55)      # of ten seconds' pressing, by ration


def _lf(path, text):
    path.write_bytes(text.encode("utf-8"))


def write_formulas(rng):
    recipes, texture = {}, {}
    names = [i[0] for i in INGREDIENTS]
    for k in range(14):
        code = "F%03d" % (101 + k)
        chosen = rng.sample(names[:13], rng.randrange(5, 8)) + ["limestone"]
        if rng.random() < 0.6:
            chosen.append("molasses")
        weights = [rng.uniform(0.5, 3.0) for _ in chosen]
        shares = [round(w / sum(weights) * 100, 1) for w in weights]
        shares[0] = round(shares[0] + 100 - sum(shares), 1)
        recipes[code] = list(zip(chosen, shares))
        texture[code] = k % 3
    return recipes, texture


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "yard"
    (outdir / "press_logs").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    recipes, texture = write_formulas(rng)
    assays = {n: (p, m, b) for n, p, m, b in INGREDIENTS}
    protein = {f: millrules.formula_protein(r, assays)
               for f, r in recipes.items()}
    ended = BEGAN + DAYS * 86400

    bins = {}
    for b in ("B1", "B2", "B3", "B4", "B5"):
        changes, now, last = [], BEGAN - rng.uniform(1, 5) * 3600, None
        while now < ended:
            options = [f for f in recipes if last is None
                       or texture[f] != texture[last]]
            last = rng.choice(options)
            changes.append((float(int(now // 60) * 60), last))
            now += rng.uniform(3.0, 7.0) * 3600
        bins[b] = changes

    presses, samples = {}, []
    for (name, tabled, real, way), keeper in zip(PRESSES, KEEPERS):
        rate = rng.uniform(3.6, 4.6) * 1000 / 360.0          # kg in ten seconds
        start = BEGAN + rng.uniform(0.6, 5.5) * 3600 + rng.uniform(0, 600)
        stop = ended - rng.uniform(0.6, 5.5) * 3600
        counter0 = round(rng.uniform(800, 9000), 4)
        wander, fuss, halt = 0.0, 0, 0
        times, tonnes = [start], [counter0]
        now, total_kg = start, 0.0
        while now < stop:
            now += millrules.LOG_EVERY_S
            if halt:
                halt -= 1
                step = 0.0
            else:
                if rng.random() < 1 / 2600.0:
                    halt = rng.randrange(30, 150)             # a stoppage
                wander = 0.985 * wander + rng.gauss(0, 0.006)
                if fuss:
                    fuss -= 1
                elif rng.random() < 1 / 300.0:
                    fuss = rng.randrange(6, 20)
                ration = millrules.formula_in(bins[real], now)
                step = rate * (1 + wander) \
                    + rng.gauss(0, RAGGEDNESS_KG[texture[ration]]) \
                    + (rng.gauss(0, 0.9) if fuss else 0.0)
                step = max(step, 0.3 * rate)
            total_kg += step
            times.append(now)
            tonnes.append(round(counter0 + total_kg / 1000.0, 4))
        presses[name] = dict(tabled=tabled, real=real, way=way, keeper=keeper,
                             times=times, tonnes=tonnes, counter0=counter0)
        for _ in range(160):
            at = round(rng.uniform(tonnes[0] + 2, tonnes[-1] - 2), 2)
            moment = millrules.time_at(times, tonnes, at)
            clear = min(abs(moment - t) for b in (tabled, real)
                        for t, _ in bins[b])
            truly = millrules.formula_in(bins[real], moment)
            on_paper = millrules.formula_in(bins[tabled], moment)
            # a log left in its own notation puts every reading before its
            # first line or after its last: the sample must not come out right
            # by that accident, or the notation would be decoration
            by_accident = {"kilograms": bins[real][0][1],
                           "pounds": bins[real][0][1],
                           "increments": millrules.formula_in(bins[real],
                                                              times[-1])}
            by_accident["kilograms"] = by_accident["pounds"] = \
                millrules.formula_in(bins[real], times[0])
            if by_accident.get(way) == truly:
                continue
            if clear >= 900 and (real == tabled or truly != on_paper):
                samples.append(dict(press=name, tag="%s@%.2f" % (name, at),
                                    answer=[truly, round(protein[truly], 2)]))

    wanted = []
    for name in presses:
        mine = [s for s in samples if s["press"] == name]
        rng.shuffle(mine)
        wanted += mine[:SAMPLES_WANTED]

    with open(outdir / "routing.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["press", "bin", "logger_kept_by", "log_began",
                      "counter_at_start_t"])
        for name, p in presses.items():
            out.writerow([name, p["tabled"], p["keeper"],
                          millrules.as_clock(p["times"][0]),
                          "%.4f" % p["counter0"]])
    with open(outdir / "bin_changes.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["bin", "time", "formula"])
        for t, b, f in sorted((t, b, f) for b, ch in bins.items()
                              for t, f in ch):
            out.writerow([b, millrules.as_clock(t), f])
    with open(outdir / "formulas.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["formula", "ingredient", "inclusion_pct"])
        for f, recipe in recipes.items():
            for ingredient, share in recipe:
                out.writerow([f, ingredient, "%.1f" % share])
    with open(outdir / "assays.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["ingredient", "protein_pct", "moisture_pct", "basis"])
        for n, p, m, b in INGREDIENTS:
            out.writerow([n, p, m, b])
    for name, p in presses.items():
        with open(outdir / "press_logs" / (name + ".csv"), "w",
                  newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            out.writerow(["time", "tonnes"])
            before = p["tonnes"][0]
            for t, w in zip(p["times"], p["tonnes"]):
                when = millrules.as_clock(t)
                shown = "%.4f" % w
                if p["way"] == "kilograms":
                    shown = "%.1f" % (w * 1000)
                elif p["way"] == "pounds":
                    shown = "%.1f" % (w * millrules.LB_PER_TONNE)
                elif p["way"] == "increments":
                    shown = "%.4f" % (w - before)
                    before = w
                elif p["way"] == "elapsed":
                    when = "%d" % round(t - p["times"][0])
                out.writerow([when, shown])
    _lf(outdir / "samples.txt", 
        "".join(s["tag"] + "\n" for s in sorted(wanted, key=lambda s: s["tag"])))
    _lf(outdir / "sealed.json", json.dumps(
        {s["tag"]: s["answer"] for s in wanted}, indent=1, sort_keys=True))
    _lf(outdir / "plumbing.json", json.dumps(
        {name: p["real"] for name, p in presses.items()}, indent=1))
    print("presses %d  log lines %d  bin changes %d  samples %d"
          % (len(presses), sum(len(p["times"]) for p in presses.values()),
             sum(len(c) for c in bins.values()), len(wanted)))
    return 0 if len(wanted) == SAMPLES_WANTED * len(presses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
