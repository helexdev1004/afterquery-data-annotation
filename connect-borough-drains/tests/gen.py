"""Build the estate, truth first, and prove the evidence settles it.

    python gen.py [outdir]

The connections are chosen before anything is surveyed. The levels, the gauges
and the traces are then written the way a survey of THAT estate would have come
out. So every answer is exact by construction rather than a judgement made
afterwards.
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import sys

import world

SEED = 20260918
MANHOLES = 18
DRAINS = 52
KNOWN = 12
GRADED = 40
# No account that ignores the gauges may come near the bar.
CHEAP_CEILING = 24


def build_network(rng):
    estate = world.Estate()
    estate.parent["MH01"] = None
    estate.invert["MH01"] = 9000
    estate.at["MH01"] = (0, 0)

    names = ["MH%02d" % i for i in range(1, MANHOLES + 1)]
    frontier = ["MH01"]
    for name in names[1:]:
        parent = rng.choice(frontier)
        run = rng.randint(28, 62)
        angle = rng.uniform(0, 6.283)
        east = estate.at[parent][0] + int(run * 0.9 * rng.choice((1, -1)))
        north = estate.at[parent][1] + int(run * 0.9 * rng.choice((1, -1)))
        if (east, north) in estate.at.values():
            east += 7
        estate.parent[name] = parent
        estate.at[name] = (east, north)
        estate.invert[name] = estate.invert[parent] + rng.randint(350, 900)
        frontier.append(name)
        if len(estate.children(parent)) >= 3:
            frontier = [f for f in frontier if f != parent]

    for name in estate.parent:
        estate.cover[name] = estate.invert[name] + rng.randint(1300, 2900)
    return estate


def hang_drains(rng, estate):
    # A property's discharge is booked to the nearest five litres an hour, and
    # houses on an estate are much of a muchness. So the flows repeat, and a
    # manhole's reading can be made up in more ways than one - which is what
    # stops the gauges settling the estate by themselves.
    bench = [n for n in range(40, 301, 5)]
    flows = [rng.choice(bench) for _ in range(DRAINS)]
    manholes = [m for m in estate.parent]
    truth = {}
    # A property is NOT put next to the chamber it drains into. The first build
    # of this task placed every one a few metres from its own chamber, so the
    # true answer was simply the nearest chamber 27 times in 40 and a solver
    # that corrected the datum and took the closest candidate scored 37 of 40
    # without touching the flows at all. The easiness probe found that in two
    # minutes. A drain runs where the ground and the old plumbing put it, often
    # past a nearer chamber it is not connected to, so each property here is
    # placed where at least two OTHER chambers are closer than its own.
    for index in range(DRAINS):
        name = "D%02d" % (index + 1)
        manhole = rng.choice(manholes)
        # How many chambers stand between the property and its own, as a target
        # rather than a floor: a rule of "never the nearest" would be a
        # signature of its own, and a solver could use it. Sometimes the drain
        # does go to the chamber at the end of the garden.
        # Most properties stand past a nearer chamber the drain could plausibly
        # have gone to but did not; some do drain to the chamber at the end of
        # the garden. Making it ALWAYS the far one would be as much of a
        # signature as always the near one.
        want_decoy = rng.random() < 0.72
        spot = None
        for _ in range(1500):
            run = rng.randint(14, 58)
            angle = rng.uniform(0, 6.2832)
            trial = (estate.at[manhole][0] + int(run * math.cos(angle)),
                     estate.at[manhole][1] + int(run * math.sin(angle)))
            # The fall is taken from the distance as the borough would MEASURE
            # it, not from the run I meant to place it at; rounding the
            # position moves the one without the other.
            actual = world.distance(trial, estate.at[manhole])
            if actual < 12 or actual > 60:
                continue
            # It is not enough that other chambers are closer. At least one of
            # them must be a chamber the drain could PLAUSIBLY have been laid
            # to, or the fall rule quietly throws the nearer ones out and the
            # true chamber is the nearest survivor all over again. That is what
            # the first build got wrong.
            least, most = world.fall_band(actual)
            drop = rng.randint(least, most)
            invert = estate.invert[manhole] + drop
            decoy = False
            for other in manholes:
                if other == manhole:
                    continue
                gap = world.distance(trial, estate.at[other])
                if gap == 0 or gap >= actual:
                    continue
                low, high = world.fall_band(gap)
                if low <= invert - estate.invert[other] <= high:
                    decoy = True
                    break
            if decoy != want_decoy:
                continue

            spot = trial
            break
        if spot is None:
            return None

        estate.drains[name] = {
            "at": spot,
            "invert": invert,
            "flow": flows[index],
        }
        truth[name] = manhole
    return truth


def attached_from(truth):
    out = {}
    for drain, manhole in truth.items():
        out.setdefault(manhole, []).append(drain)
    return out


ROUNDS = 6
PLUGGED_ROUNDS = (3, 4)
STORM_FROM, STORM_TO = 2040, 2400        # minutes from the start of the survey
# A quarter of a metre a second: a private drain runs slow at a dry-weather
# flow, and it has to, or no trace could be dosed in the dry and seen in the wet.
VELOCITY_NUM, VELOCITY_DEN = 25, 100


def pipe_run(estate, drain, manhole, observer):
    """Metres of pipe from a property to an observer's chamber."""
    run = world.distance(estate.drains[drain]["at"], estate.at[manhole])
    path = estate.path_down(manhole)
    for step in range(len(path) - 1):
        run += world.distance(estate.at[path[step]], estate.at[path[step + 1]])
        if path[step] == observer:
            break
    if observer == manhole:
        return world.distance(estate.drains[drain]["at"], estate.at[manhole])
    total = world.distance(estate.drains[drain]["at"], estate.at[manhole])
    for step in range(len(path) - 1):
        total += world.distance(estate.at[path[step]], estate.at[path[step + 1]])
        if path[step + 1] == observer:
            return total
    return total


def emit(outdir, estate, truth, known, watched, traced, sightings, gauges, rng,
         quiet=False):
    import csv

    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    # --- the gauge set the wrong way round -----------------------------------
    # One gauge was put in the chamber's INCOMING channel instead of the
    # outgoing one, so it reads only the drains on that chamber and not the
    # whole of what stands above it. It reads the same on every visit, so there
    # is no spoiled round to throw away and no average that repairs it - the
    # first build's stopped chamber could be sidestepped by taking the median
    # across rounds, which is what let the probe solve it in seventy seconds.
    # The only way past this one is to notice that the chamber reads LESS than
    # the chambers falling into it, which nothing above them can.
    live = [m for m in estate.parent
            if m != "MH01" and estate.children(m)
            and gauges[m] > sum(gauges[c] for c in estate.children(m))]
    crossed = sorted(live)[len(live) // 2]
    own = gauges[crossed] - sum(gauges[c] for c in estate.children(crossed))

    with open(out / "flows.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, ["manhole", "litres_hour"],
                                lineterminator="\n")
        writer.writeheader()
        for manhole in sorted(estate.parent):
            writer.writerow({
                "manhole": manhole,
                "litres_hour": own if manhole == crossed else gauges[manhole]})

    # --- the old datum -------------------------------------------------------
    # One of the level books was worked to the old borough datum, which stands
    # 2.740 m below Ordnance. Nothing in the book says so. What says so is that
    # those chambers stand higher than the ones that fall into them, and a
    # sewer does not run uphill.
    trunks = [m for m in estate.parent if estate.parent.get(m) == "MH01"]
    branch = max((sorted(estate.above(t)) for t in trunks), key=len)
    book = set(branch[:max(4, (len(branch) * 2) // 3)])

    with open(out / "manholes.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["manhole", "falls_to", "east", "north", "cover_mm",
                         "invert_mm", "level_book"])
        for manhole in sorted(estate.parent):
            shift = world.OLD_DATUM_MM if manhole in book else 0
            writer.writerow([manhole, estate.parent[manhole] or "OUTFALL",
                             estate.at[manhole][0], estate.at[manhole][1],
                             estate.cover[manhole] + shift,
                             estate.invert[manhole] + shift,
                             "B" if manhole in book else "A"])

    with open(out / "drains.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["drain", "east", "north", "invert_mm", "litres_hour"])
        for drain in sorted(estate.drains):
            spec = estate.drains[drain]
            writer.writerow([drain, spec["at"][0], spec["at"][1],
                             spec["invert"], spec["flow"]])

    # --- the storm -----------------------------------------------------------
    # The estate surcharges in heavy rain and the dye backs up into a branch it
    # would never reach. A trace is affected if the dye was in the pipe WHILE
    # the estate was surcharged - which is settled by when it was SEEN, not by
    # when it was put in. Some traces were dosed before the rain and sighted
    # during it, and those are the ones the two readings part company over.
    def travel(drain, manhole, observer):
        run = pipe_run(estate, drain, manhole, observer)
        return (run * VELOCITY_DEN) // (VELOCITY_NUM * 60)

    order = sorted(traced)
    gradedset = [d for d in order if d not in known]
    # Seven traces are dosed just BEFORE the rain and seen during it. They are
    # what the two readings of "which traces ran in the storm" disagree about,
    # and seven against an allowance of four is what decides the task.
    # Only a drain whose dye takes a few minutes to reach the first observer
    # can be dosed in the dry and seen in the wet; a trace that arrives in a
    # minute straddles nothing.
    def lag(drain):
        manhole = truth[drain]
        lags = [travel(drain, manhole, o) for o in watched
                if o in estate.path_down(manhole)]
        return min(lags) if lags else 0

    slow = [d for d in gradedset if lag(d) >= 3]
    boundary = slow[:10]
    inside = [d for d in gradedset if d not in boundary][:5]

    storm_traces, tracer = [], []
    for index, drain in enumerate(order):
        manhole = truth[drain]
        seen_at = [(o, travel(drain, manhole, o)) for o in watched
                   if o in estate.path_down(manhole)]
        if not seen_at:
            continue
        first = min(lag for _, lag in seen_at)

        if drain in boundary:
            dosed = STORM_FROM + 1 - first   # before the rain, seen inside it
        elif drain in inside:
            dosed = rng.randint(STORM_FROM + 30, STORM_TO - 60)
        else:
            dosed = rng.choice([rng.randrange(0, STORM_FROM - 400),
                                rng.randrange(STORM_TO + 200, 4600)])

        rows = [(o, dosed + lag) for o, lag in seen_at]
        if any(STORM_FROM <= at <= STORM_TO for _, at in rows):
            storm_traces.append(drain)
            spurious = [o for o in watched
                        if o not in estate.path_down(manhole)]
            if spurious:
                rows.append((rng.choice(spurious),
                             rng.randint(max(STORM_FROM, dosed), STORM_TO)))
        for observer, at in sorted(rows):
            tracer.append({"trace": "T%02d" % (index + 1), "drain": drain,
                           "dosed_min": dosed, "observer": observer,
                           "seen_min": at})

    with open(out / "tracer.csv", "w", newline="") as fh:
        writer = csv.DictWriter(
            fh, ["trace", "drain", "dosed_min", "observer", "seen_min"],
            lineterminator="\n")
        writer.writeheader()
        writer.writerows(tracer)

    with open(out / "rain.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["from_min", "to_min", "mm"])
        # The rain is booked in twenty minute periods so the storm's edge is
        # sharp. A trace dosed in the dry and seen in the wet is then a real
        # distinction and not an artefact of a coarse rain gauge.
        for start in range(0, 4800, 20):
            wet = STORM_FROM <= start < STORM_TO
            writer.writerow([start, start + 20,
                             rng.randint(6, 12) if wet else 0])

    with open(out / "known.csv", "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["drain", "manhole"])
        for drain in sorted(known):
            writer.writerow([drain, known[drain]])

    graded = sorted(d for d in truth if d not in known)
    (out / "truth.json").write_text(
        json.dumps({d: truth[d] for d in graded}, indent=1), newline="\n")
    (out / "survey.json").write_text(json.dumps({
        "crossed": crossed, "crossed_own": own,
        "level_book_B": sorted(book), "storm_traces": sorted(storm_traces),
        "watched": watched, "graded": graded,
    }, indent=1), newline="\n")

    if quiet:
        return
    print("gauge at %s reads its own %d l/h, not the %d above it; level book B "
          "holds %d chambers; %d traces ran in the storm"
          % (crossed, own, gauges[crossed], len(book), len(storm_traces)))


def main() -> int:
    outdir = sys.argv[1] if len(sys.argv) > 1 else str(
        pathlib.Path(__file__).resolve().parent.parent / "yard")
    # The estate is drawn from one fixed seed and the records are then static
    # files. Nothing is generated at marking time, so the answer cannot drift
    # between runs and the reference scores the same on every one.
    rng = random.Random(SEED)

    for attempt in range(600):
        estate = build_network(rng)
        truth = hang_drains(rng, estate)
        if truth is None:
            continue
        level_cands = {d: estate.candidates(d, estate.invert)
                       for d in estate.drains}
        if any(truth[d] not in level_cands[d] for d in level_cands):
            continue
        spread = sorted(len(c) for c in level_cands.values())
        if spread[len(spread) // 2] < 3 or spread[-1] > 12:
            continue

        # A gauge is not got into every chamber. Gauging them all would settle
        # the estate on the flows alone and leave the traces doing nothing.
        # The observers are put INSIDE the regions the gauges cut, so that the
        # two kinds of evidence answer different questions: the flows say which
        # region a drain is in and cannot see inside one, the traces say where
        # inside a region and cannot add up.
        others = [m for m in estate.parent if m != "MH01"]
        # An observer can only be posted where a man can work a chamber, so the
        # dye is watched for at a handful of them. A sighting says the drain
        # stands somewhere above that chamber - reachability, not adjacency -
        # and only the traces and the gauges together settle the estate.
        attached = attached_from(truth)
        gauges = {m: estate.gauge(m, attached) for m in estate.parent}
        # Every chamber on the estate must carry something. A chamber with
        # nothing above it reads a flat zero on every round, which is a second
        # and quite different reason for a zero reading and muddies the stopped
        # chamber that the task turns on.
        if any(rate == 0 for rate in gauges.values()):
            continue
        want = world.residuals(estate, gauges)
        known = dict(sorted(truth.items())[:KNOWN])

        watched = sorted(rng.sample(others, 6))
        traced = set(rng.sample(sorted(estate.drains), 30))
        sightings = {d: {o for o in watched if o in estate.path_down(truth[d])}
                     for d in traced}

        cands = {}
        for drain, options in level_cands.items():
            if drain in traced:
                keep = [m for m in options
                        if {o for o in watched if o in estate.path_down(m)}
                        == sightings[drain]]
            else:
                keep = list(options)
            cands[drain] = keep
        if any(truth[d] not in cands[d] for d in cands):
            continue

        # The flows must be load-bearing too, and the first build proved that
        # cannot be assumed. There, a solver that corrected the datum, took the
        # traces at face value and then simply picked the CLOSEST remaining
        # chamber scored 37 of 40 and cleared the bar without looking at a
        # single gauge - and the easiness probe found it in two minutes. So the
        # nearest-candidate heuristic is scored here, and an estate where it
        # does well is thrown away rather than shipped.
        def nearest_candidate(drain):
            spot = estate.drains[drain]["at"]
            best, far = None, None
            for option in cands[drain] or sorted(estate.parent):
                gap = world.distance(spot, estate.at[option])
                if far is None or gap < far:
                    best, far = option, gap
            return best

        graded_now = [d for d in truth if d not in dict(sorted(truth.items())[:KNOWN])]
        cheap = sum(1 for d in graded_now if nearest_candidate(d) == truth[d])
        if cheap > CHEAP_CEILING:
            print("attempt %2d  the nearest candidate alone gets %d of %d"
                  % (attempt, cheap, len(graded_now)))
            continue

        # The traces must be load-bearing: without them the gauges and the
        # levels have to leave the estate unsettled, or the survey is carrying
        # a set of records that does nothing.
        without = world.solve(estate, want, level_cands, known, cap=2)
        if len(without) < 2:
            print("attempt %2d  traces are inert (flows alone give %d answers)"
                  % (attempt, len(without)))
            continue

        narrowed = sorted(len(c) for c in cands.values())
        answers = world.solve(estate, want, cands, known, cap=2)
        print("attempt %2d  levels %s  after traces %s  flows-alone %d  answers %d"
              % (attempt, (spread[0], spread[len(spread) // 2], spread[-1]),
                 (narrowed[0], narrowed[len(narrowed) // 2], narrowed[-1]),
                 len(without), len(answers)))
        if len(answers) != 1 or answers[0] != {
                d: m for d, m in truth.items() if d not in known}:
            continue

        # The checks above work on what the generator KNOWS. The solver works
        # on what actually ships, and the two are not the same: a trace spoiled
        # by the storm loses its filter altogether in the shipped view, so the
        # candidate sets are wider there. Verifying in the generator's own view
        # and shipping on that basis is how the first build came out at 38 of
        # 40. So the records are written, and then read back and solved exactly
        # as the agent's container would, before the estate is accepted.
        import shutil
        import tempfile

        import solver as shipped

        room = tempfile.mkdtemp(prefix="drains-")
        try:
            emit(room, estate, truth, known, watched, traced, sightings,
                 gauges, rng, quiet=True)
            got = shipped.run(room)
            want_graded = {d: m for d, m in truth.items() if d not in known}
            if got != want_graded:
                agree = sum(1 for d in want_graded if got.get(d) == want_graded[d])
                print("attempt %2d  the shipped records give %d of %d"
                      % (attempt, agree, len(want_graded)))
                continue

            estate2, want2, cands2, known2 = shipped.build(
                room, shipped.TRUE_READING)
            if len(world.solve(estate2, want2, cands2, known2, cap=2)) != 1:
                print("attempt %2d  the shipped records allow more than one "
                      "answer" % attempt)
                continue

            print("the shipped records settle the estate uniquely")
            out = pathlib.Path(outdir)
            if out.exists():
                shutil.rmtree(out)
            shutil.copytree(room, out)
            print("manholes %d  drains %d  known %d  graded %d"
                  % (len(estate.parent), len(estate.drains), len(known),
                     len(want_graded)))
            print("wrote %s" % out)
            return 0
        finally:
            shutil.rmtree(room, ignore_errors=True)
    print("could not find an estate the evidence settles")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
