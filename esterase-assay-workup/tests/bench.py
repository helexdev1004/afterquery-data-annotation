"""Make one assay day of esterase plates, and the figures that are true of it.

A day is a handful of 96-well plates.  Each holds eighty mosquito homogenates,
four blanks in the corners and two ladders of p-nitrophenol standards down the
outside columns, one running down and one running up, so the lay-out of roles
reads the same from either end of the plate.

Substrate goes on to the whole plate at once, so every well has had the same
head start by the first read and nothing first-order runs along the plate.

Homogenates come in runs: some were cleared in the centrifuge before plating,
the rest went on as ground.  A crude homogenate is cloudy, and what is in it
drifts through the beam, so its reads wander slowly about their line where a
spun one's scatter read to read.  The wander is scaled so that the spread of a
well's reads about its fitted line is the same for both; only how the
departures follow one another differs.

Some plates are put into the reader end for end.  The reader names wells by
where they sit in its carriage, so on such a plate what it calls B2 is the well
the lay-out calls G11.
"""
import math
import random

ROWS = "ABCDEFGH"
COLS = range(1, 13)
LADDER = [5.0, 10.0, 20.0, 40.0, 60.0, 80.0]          # nmol p-nitrophenol a well
READ_EVERY_S = 20
N_READS = 16
Q10 = 2.0
MODES = ["absorbance", "absorbance", "milli-absorbance", "transmittance"]

KNOBS = {"delay_sd": 0.4, "tint_sd": 0.004, "read_sd": 0.0018,
         "wander": 0.8,                # how much of a crude well's departure carries over
         "run": (4, 14),               # homogenates in a run of one preparation
         "crude_share": (0.35, 0.5),
         "unlike_its_turn": 0.40}      # share of wells whose preparation differs end for end


def well(r, c):
    return "%s%d" % (ROWS[r], c)


def turned(name):
    r, c = ROWS.index(name[0]), int(name[1:])
    return well(7 - r, 13 - c)


def _residual_spread(series_of, trials=3000):
    """Mean squared departure from a fitted line, per read, for a noise maker."""
    xs = list(range(N_READS))
    mx = sum(xs) / N_READS
    sxx = sum((x - mx) ** 2 for x in xs)
    total = 0.0
    for _ in range(trials):
        ys = series_of()
        my = sum(ys) / N_READS
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
        total += sum((y - my - slope * (x - mx)) ** 2 for x, y in zip(xs, ys))
    return total / trials / (N_READS - 2)


def wandering(rng, carry, sd):
    """A stationary run of departures, each carrying over a share of the last."""
    fresh = sd * math.sqrt(1.0 - carry * carry)
    e = rng.gauss(0.0, sd)
    out = []
    for _ in range(N_READS):
        out.append(e)
        e = carry * e + rng.gauss(0.0, fresh)
    return out


def _crude_scale(carry):
    """What a wandering well's departures are scaled by to leave the same
    spread about a fitted line as an unwandering one's."""
    rng = random.Random(20310905)
    white = _residual_spread(lambda: [rng.gauss(0.0, 1.0) for _ in range(N_READS)])
    crude = _residual_spread(lambda: wandering(rng, carry, 1.0))
    return math.sqrt(white / crude)


CRUDE_SCALE = _crude_scale(KNOBS["wander"])


def preparations(rng, knobs):
    """Spun or crude for the eighty homogenates in plating order, in runs, and
    not reading alike from the two ends of the plate."""
    lo, hi = knobs["run"]
    while True:
        share = rng.uniform(*knobs["crude_share"])
        seq = []
        while len(seq) < 80:
            kind = "crude" if rng.random() < share else "spun"
            seq.extend([kind] * rng.randint(lo, hi))
        seq = seq[:80]
        crude = seq.count("crude") / 80.0
        unlike = sum(1 for a, b in zip(seq, reversed(seq)) if a != b) / 80.0
        if 0.3 <= crude <= 0.55 and unlike >= knobs["unlike_its_turn"]:
            return seq


def roles(first_id, preps):
    """The lay-out of one plate, by the names printed on the plate."""
    layout, n = {}, first_id
    preps = iter(preps)
    for c in COLS:
        for r in range(8):
            name = well(r, c)
            if c in (1, 12) and r in (0, 7):
                layout[name] = {"role": "blank"}
            elif c == 1:
                layout[name] = {"role": "standard", "nmol": LADDER[r - 1]}
            elif c == 12:
                layout[name] = {"role": "standard", "nmol": LADDER[6 - r]}
            else:
                layout[name] = {"role": "sample", "id": "M-%06d" % n, "prep": next(preps)}
                n += 1
    return layout, n


def one_plate(rng, label, first_id, reader, end_for_end, knobs):
    layout, next_id = roles(first_id, preparations(rng, knobs))
    mode = rng.choice(MODES)
    minutes = rng.random() < 0.35
    chamber = round(rng.uniform(24.0, 29.5), 1)
    base = rng.uniform(0.041, 0.049)
    eps = 0.0105 * rng.uniform(0.97, 1.03)              # OD a nmol
    blank_rate = rng.uniform(0.0008, 0.0016) / 60.0     # OD a second
    gap = rng.uniform(40.0, 75.0)                       # substrate on to first read
    resistant_share = rng.uniform(0.15, 0.5)
    dilution = rng.choice([10, 20, 20, 40])

    curves = {}
    for name, what in layout.items():
        delay = gap + rng.gauss(0.0, knobs["delay_sd"])
        if what["role"] == "blank":
            level, rate = base + rng.gauss(0, 0.0012), blank_rate
        elif what["role"] == "standard":
            level, rate = base + eps * what["nmol"] * rng.uniform(0.992, 1.008), 0.0
        else:
            median = 0.115 if rng.random() < resistant_share else 0.030
            v = median * math.exp(rng.gauss(0.0, 0.42)) / 60.0
            v = min(v, 0.30 / 60.0)
            level = base + abs(rng.gauss(0.0, knobs["tint_sd"]))
            rate = v + blank_rate
            what["dilution"] = dilution
        if what.get("prep") == "crude":
            off = wandering(rng, knobs["wander"], knobs["read_sd"] * CRUDE_SCALE)
        else:
            off = [rng.gauss(0.0, knobs["read_sd"]) for _ in range(N_READS)]
        curves[name] = [level + rate * (k * READ_EVERY_S + delay) + off[k]
                        for k in range(N_READS)]

    seen = {}
    for name, series in curves.items():
        where = turned(name) if end_for_end else name
        seen[where] = [as_exported(od, mode) for od in series]
    times = [k * READ_EVERY_S for k in range(N_READS)]
    if minutes:
        times = [round(t / 60.0, 4) for t in times]
    plate ={"plate": label, "reader": reader, "mode": mode,
             "time_unit": "min" if minutes else "s", "chamber_c": chamber,
             "read_times": times, "layout": layout,
             "reads": {k: seen[k] for k in sorted(seen, key=lambda w: (w[0], int(w[1:])))}}
    return plate, next_id


def as_exported(od, mode):
    if mode == "absorbance":
        return round(od, 4)
    if mode == "milli-absorbance":
        return round(od * 1000.0, 1)
    return round(100.0 * 10.0 ** (-od), 3)


def one_day(seed, knobs=None):
    """Returns the day as the program is handed it, and which plates were turned."""
    knobs = knobs or KNOBS
    rng = random.Random(seed)
    n_plates = rng.choice([4, 5, 5, 6])
    # always some, never as many as went in the right way round
    n_turned = rng.choice([1, 1, 2]) if n_plates > 4 else 1
    flags = [False] * n_plates
    for i in rng.sample(range(n_plates), n_turned):
        flags[i] = True
    month, dom = rng.randint(3, 10), rng.randint(1, 28)
    # the insectary numbers mosquitoes on through the year: a day's run starts
    # at a number no other day of that year reaches
    next_id = 500 * ((month - 1) * 31 + dom) + rng.randint(1, 20)
    plates, was_turned = [], {}
    for i, flag in enumerate(flags, 1):
        label = "P%d" % i
        plate, next_id = one_plate(rng, label, next_id, rng.choice(["R1", "R2", "R3"]),
                                   flag, knobs)
        plates.append(plate)
        was_turned[label] = flag
    day = {"day": "2031-%02d-%02d" % (month, dom), "plates": plates}
    return day, was_turned
