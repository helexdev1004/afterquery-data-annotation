"""Walk the site, truth first, then dump it as the instrument logged it.

    python gen.py [outdir]

The buried features are laid down before anything is surveyed: compact
anomalies of the kind a corer is sent to, and a scatter of lesser ones. The
gradiometer's readings over every half-metre cell follow from those, and the
logger dumps are then written the way five surveyors walked and booked forty
grids. So every answer is exact by construction rather than a judgement made
afterwards.

Internally everything is whole decimetres on the site grid and whole
nanotesla.
"""

from __future__ import annotations

import csv
import json
import pathlib
import random
import sys

import survey

SEED = 20260922
COLUMNS, ROWS = 8, 5                    # forty grids in a block
ORIGIN_E, ORIGIN_N = 4000, 2000         # the block's south-west corner, in dm
TO_LOCATE = 40

SURVEYORS = {
    "Ashby": "units",       # instrument left on its 0.1 nT range: values x10
    "Brough": "centre",     # books a grid's position by its centre
    "Calder": "swapped",    # books northing before easting
    "Denholm": "fine",      # logged at a quarter-metre sample interval
    "Elsdon": None,         # keeps to the specification
}


def lay_site(rng):
    """The buried features, as a reading for every cell of the whole block."""
    wide, high = COLUMNS * survey.CELLS, ROWS * survey.CELLS
    # The ground is noisy - eight nanotesla either way, which is ordinary for
    # pasture over boulder clay. It matters: with quiet ground the heading
    # error stood out in every single traverse, and every cold solver that
    # so much as listed the traverse means saw the stripes. Against this
    # ground one traverse says nothing; it takes the four hundred readings
    # walked each way, set against one another, to show it.
    field = [[rng.randint(-8, 8) for _ in range(high)] for _ in range(wide)]

    # Nothing on this site runs from one grid into the next. An earlier build
    # crossed it with ditches and drains, and every cold solver laid each grid
    # out every way about and kept the way that let the ditches run straight
    # through - across traverses and across grid edges - without being asked
    # to. What is left is compact: it lies inside one grid and says nothing
    # about how that grid was walked.
    anomalies = []
    tries = 0
    while len(anomalies) < 64 and tries < 600000:
        tries += 1
        t = rng.randrange(8, wide - 8)
        c = rng.randrange(8, high - 8)
        # well inside a grid, so that a peak and its image in the grid's own
        # east-west midline are both clear of the grid's edges
        if not 7 <= t % survey.CELLS <= survey.CELLS - 8:
            continue
        if not 7 <= c % survey.CELLS <= survey.CELLS - 8:
            continue
        # and off that midline, where turning the grid over would leave the
        # peak where it was
        if abs(c % survey.CELLS - survey.CELLS // 2) < 3:
            continue
        if any(abs(t - a["t"]) < 9 and abs(c - a["c"]) < 86 for a in anomalies):
            continue                    # one strong anomaly to any one window
        amp = rng.randint(40, 90)
        anomalies.append({"t": t, "c": c, "amp": amp})
        for dt in range(-4, 5):
            for dc in range(-4, 5):
                d2 = dt * dt + dc * dc
                field[t + dt][c + dc] += amp * 100 // (100 + 60 * d2)

    # A scatter of lesser anomalies - bits of iron in the ploughsoil. None
    # comes near a strong one in size, but read ten times too high one of them
    # out-reads anything on the site, which is what the wrong instrument range
    # does to a window that runs into such a grid.
    lesser = []
    tries = 0
    while len(lesser) < 170 and tries < 60000:
        tries += 1
        t = rng.randrange(4, wide - 4)
        c = rng.randrange(4, high - 4)
        if not 3 <= t % survey.CELLS <= survey.CELLS - 4:
            continue
        if not 3 <= c % survey.CELLS <= survey.CELLS - 4:
            continue
        if any(abs(t - a["t"]) < 8 and abs(c - a["c"]) < 8 for a in anomalies):
            continue
        if any(abs(t - a[0]) < 7 and abs(c - a[1]) < 7 for a in lesser):
            continue
        amp = rng.randint(10, 22)
        lesser.append((t, c))
        for dt in range(-2, 3):
            for dc in range(-2, 3):
                d2 = dt * dt + dc * dc
                field[t + dt][c + dc] += amp * 100 // (100 + 80 * d2)
    return field, anomalies


def main() -> int:
    outdir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                          pathlib.Path(__file__).resolve().parent.parent / "yard")
    rng = random.Random(SEED)
    field, anomalies = lay_site(rng)

    names = list(SURVEYORS)
    walkers = [names[i % len(names)] for i in range(COLUMNS * ROWS)]
    rng.shuffle(walkers)

    # Which end each grid was begun from. The specification has every grid
    # begun at its south-west corner, but a surveyor begins a grid from
    # whichever end he finished the last one at, and no field sheet says which.
    # Four of the eight grids of every surveyor but one were begun from the
    # north. The one is the surveyor who kept to the specification in
    # everything: all eight of his were begun where it says, and so his dumps
    # show what a grid begun from the south looks like in the readings.
    begun = {}
    for who in names:
        mine = [i for i, w in enumerate(walkers) if w == who]
        rng.shuffle(mine)
        for k, i in enumerate(mine):
            begun[i] = "N" if k < len(mine) // 2 and SURVEYORS[who] else "S"

    (outdir / "dumps").mkdir(parents=True, exist_ok=True)
    for old in (outdir / "dumps").glob("*.txt"):
        old.unlink()

    grids = []
    for j in range(ROWS):
        for i in range(COLUMNS):
            number = j * COLUMNS + i + 1
            name = "G%02d" % number
            who = walkers[number - 1]
            habit = SURVEYORS[who]
            east = ORIGIN_E + i * survey.GRID_DM
            north = ORIGIN_N + j * survey.GRID_DM

            lines = []
            for t in range(survey.CELLS):
                run = [field[i * survey.CELLS + t][j * survey.CELLS + c]
                       for c in range(survey.CELLS)]
                # The grid is walked zig-zag, as the specification requires:
                # out along one traverse and back along the next. Begun from
                # the south its first traverse is walked northwards; begun
                # from the north, southwards.
                northwards = (t % 2 == 0) == (begun[number - 1] == "S")
                # The instrument reads a nanotesla high carried northwards and
                # a nanotesla low carried southwards - its heading error, which
                # the specification does not mention. It is what says, in the
                # readings themselves, which way each traverse was walked.
                run = [v + (survey.HEADING if northwards else -survey.HEADING)
                       for v in run]
                if habit == "fine":
                    # two readings to the cell, a quarter of a metre apart,
                    # whose mean is the cell's own reading exactly
                    fine = []
                    for v in run:
                        # whichever of the pair is the higher comes first as
                        # often as not: a fixed order turned round with the
                        # traverse, and a cold solver read the direction of
                        # walking off it
                        e = rng.randint(0, 2) * rng.choice((-1, 1))
                        fine.extend((v + e, v - e))
                    run = fine
                # The logger knows nothing of where the instrument is; it
                # writes readings down in the order they are taken.
                if not northwards:
                    run = run[::-1]
                if habit == "units":
                    run = [v * 10 for v in run]
                lines.extend(run)
            (outdir / "dumps" / (name + ".txt")).write_text(
                "\n".join(str(v) for v in lines) + "\n", newline="\n")

            booked_e, booked_n = east, north
            if habit == "centre":
                booked_e += survey.GRID_DM // 2
                booked_n += survey.GRID_DM // 2
            if habit == "swapped":
                booked_e, booked_n = booked_n, booked_e
            grids.append({"grid": name, "surveyor": who,
                          "east_m": "%d.%d" % divmod(booked_e, 10),
                          "north_m": "%d.%d" % divmod(booked_n, 10)})

    with open(outdir / "grids.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, ["grid", "surveyor", "east_m", "north_m"],
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(grids)

    # Every anomaly gets a window, all of them written down for now; the forty
    # that go out are chosen afterwards on what the records' habits do to them.
    rows, truth = [], {}
    for index, a in enumerate(sorted(anomalies, key=lambda a: (a["t"], a["c"])),
                              1):
        name = "A%02d" % index
        # Five traverses wide, and not centred on the anomaly: a cold solver
        # noticed that every peak it found lay in the middle traverse of its
        # window, and used that to check how it had laid the grids out.
        first = a["t"] - 2 + rng.randint(-1, 1)
        e_from = ORIGIN_E + first * survey.CELL_DM
        e_to = ORIGIN_E + (first + 5) * survey.CELL_DM
        row = a["c"] // survey.CELLS
        # the window runs the height of the peak's own grid and the grid next
        # to it, north or south
        other = row + 1 if row + 1 < ROWS and (row == 0 or index % 2) else row - 1
        # Where one of the two neighbours was walked on the wrong range and the
        # peak's own grid was not, take that one: a grid reading ten times too
        # high beside one that does not is what the range mistake does to a
        # window, and it should be met as often as the other habits are.
        column = a["t"] // survey.CELLS
        if SURVEYORS[walkers[row * COLUMNS + column]] != "units":
            for near in (row + 1, row - 1):
                if 0 <= near < ROWS and SURVEYORS[
                        walkers[near * COLUMNS + column]] == "units":
                    other = near
        n_from = ORIGIN_N + min(row, other) * survey.GRID_DM
        n_to = ORIGIN_N + (max(row, other) + 1) * survey.GRID_DM
        rows.append({"anomaly": name,
                     "east_from_m": "%d.%d" % divmod(e_from, 10),
                     "east_to_m": "%d.%d" % divmod(e_to, 10),
                     "north_from_m": "%d.%d" % divmod(n_from, 10),
                     "north_to_m": "%d.%d" % divmod(n_to, 10)})
        # The answer is the cell that READS highest in the window, as the
        # instrument read it - heading error and all, since the specification
        # defines a peak on the readings and has nothing in the log corrected
        # - and not the spot the anomaly was laid at.
        best, where = None, None
        for t in range(first, first + 5):
            for c in range(min(row, other) * survey.CELLS,
                           (max(row, other) + 1) * survey.CELLS):
                grid = (c // survey.CELLS) * COLUMNS + t // survey.CELLS
                northwards = ((t % survey.CELLS) % 2 == 0) == (
                    begun[grid] == "S")
                read = field[t][c] + (survey.HEADING if northwards
                                      else -survey.HEADING)
                key = (read, -t, -c)
                if best is None or key > best:
                    best, where = key, (t, c)
        truth[name] = survey.cell_ref(ORIGIN_E + where[0] * survey.CELL_DM,
                                      ORIGIN_N + where[1] * survey.CELL_DM)

    def write_anomalies(wanted):
        with open(outdir / "anomalies.csv", "w", newline="") as fh:
            writer = csv.DictWriter(fh, list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(r for r in rows if r["anomaly"] in wanted)
        (outdir / "truth.json").write_text(json.dumps(
            {k: v for k, v in truth.items() if k in wanted},
            indent=1, sort_keys=True), newline="\n")

    write_anomalies(set(truth))

    import ref
    right = ref.run(outdir)
    wrong = [k for k in truth if right.get(k) != truth[k]]
    if wrong:
        print("FAILED: the reference and the site disagree on %d of %d"
              % (len(wrong), len(truth)))
        for k in wrong[:5]:
            print("   %s said %s was %s" % (k, right.get(k), truth[k]))
        return 1

    moved = {k: set() for k in truth}
    for axis, other in ref.OTHERS.items():
        got = ref.run(outdir, dict(ref.TRUE_READING, **{axis: other}))
        for k in truth:
            if got.get(k) != truth[k]:
                moved[k].add(axis)

    pool = [k for k in sorted(truth) if moved[k]]
    rng.shuffle(pool)
    cover = {axis: 0 for axis in ref.OTHERS}
    wanted = set()
    while len(wanted) < TO_LOCATE and pool:
        need = min(cover, key=lambda a: cover[a])
        pick = next((k for k in pool if need in moved[k]), pool[0])
        pool.remove(pick)
        wanted.add(pick)
        for axis in moved[pick]:
            cover[axis] += 1
    # A few that nothing moves - anomalies in the grids of the surveyor who
    # kept to the specification - so that the forty are not conspicuously
    # drawn from the grids of the four who did not.
    spare = [k for k in sorted(truth) if not moved[k]]
    rng.shuffle(spare)
    while len(wanted) < TO_LOCATE and spare:
        wanted.add(spare.pop())
    if len(wanted) < TO_LOCATE:
        print("FAILED: only %d anomalies were laid" % len(wanted))
        return 1

    write_anomalies(wanted)
    (outdir / "begun.json").write_text(json.dumps(
        {"G%02d" % (i + 1): end for i, end in sorted(begun.items())},
        indent=1), newline="\n")
    print("grids %d  anomalies laid %d  to locate %d"
          % (len(grids), len(truth), len(wanted)))
    print("anomalies each habit moves among the forty: %s" % cover)
    print("wrote %s" % outdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
