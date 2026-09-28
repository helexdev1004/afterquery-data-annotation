"""Read the founder's sessions and write up where the ring now stands.

Nothing says which bell a session is, and no single cue settles it:

  * Pitch does not. A bell drops two to three hundred cents over its cuts and
    the ring is spaced two hundred, so the runs interleave - a bell's early
    cuts sit above its neighbour's late ones. Sessions from other jobs sit
    inside the same range.

  * The casting signature does, mostly. The untuned upper partials sit where
    the shape put them and tuning the five lower ones barely moves them, so
    they persist across a bell's cuts and differ between bells. But the
    analyser did not always catch them, and on three sessions it caught none.

  * The day-book does not. It names a bell for about half the runs and some of
    those names are wrong.

So the work is a joint assignment consistent with all three at once:

1. Find the nominal in each peak list - the peak with four others beneath it at
   a quarter, a half, three fifths and three quarters.
2. Read each session's signature off the peaks above the nominal.
3. Group by signature. A group of three or more cuts is a bell; a job from
   another bench appears once.
4. Order each group by the day-book's dates. Every cut takes metal off, so the
   nominals must fall as the dates advance - which is a check the book's dates
   make possible and nothing else does.
5. Place the sessions that have no signature. The book names them. Accept a
   name only if the descent still holds with the session in place; where it
   does not, the book is wrong and the session goes to the one bell it does
   fit.
6. The last cut is the bell as it now stands.
"""

from __future__ import annotations

import csv
import math
import pathlib
import re

PARTIALS = {"hum": 1 / 4, "prime": 1 / 2, "tierce": 3 / 5,
            "quint": 3 / 4, "nominal": 1.0}
ORDER = ["hum", "prime", "tierce", "quint", "nominal"]
UPPER_RATIOS = (1.33, 1.78, 2.37)

MATCH_WINDOW_CENTS = 60.0
# A casting sits at one of three levels, 42 cents either side of the ratio or
# on it, and a reading is good to a few cents. Searching 70 cents out let
# clutter inside the window; 60 covers every real partial with room to spare.
UPPER_WINDOW_CENTS = 60.0
IN_TRUE_CENTS = 4.0
SIGNATURE_WINDOW_CENTS = 11.0
ASSIGN_MARGIN_CENTS = 5.0
# Generous: a partly recorded casting is only used to rule a bell OUT, so this
# has to be wide enough never to rule out the right one.
CASTING_VETO_CENTS = 16.0
# A bell went back on the lathe several times and its casting was recorded in
# full on at least three of those runs. Two runs that agree are not enough to
# call a bell: a job from another bench matched one run of bell-01 closely
# enough to form a spurious ninth group that way.
MIN_SEED_RUNS = 3
MIN_CUTS_PER_BELL = 3
RING_SIZE = 8
# A bell went back on the frame to be measured rather than cut, and the same
# tape was read twice and filed under two ids. Both leave a step of nothing in
# a chain, so a chain is non-increasing rather than strictly falling - within a
# reading's precision.
TIE_CENTS = 2.5
# How much wider than a normal bell's run of cuts a group has to be before it
# is two bells sharing a mould rather than one.
WIDE_GROUP_FACTOR = 1.6


def cents_between(a: float, b: float) -> float:
    return 1200.0 * math.log2(a / b)


def find_nominal(peaks: list[float]):
    """The peak that has the other four standing beneath it, or nothing.

    More than one peak can pass that test. The window has to be wide, because
    an early cut's partials are tens of cents out, and a peak from the bell on
    the next pit a few tens of cents away then sees the same four partials
    inside it too. The first such candidate used to win, which put one run of
    bell-06's nominal on a stray peak 29 cents below the real one and read
    every partial about 35 cents sharp. Among the candidates that account for
    all five, the right one is the one they fit best.
    """
    best = None
    for candidate in peaks:
        found, total = {}, 0.0
        for name, ratio in PARTIALS.items():
            target = candidate * ratio
            nearest, distance = None, None
            for peak in peaks:
                gap = abs(cents_between(peak, target))
                if gap <= MATCH_WINDOW_CENTS and (distance is None or gap < distance):
                    nearest, distance = peak, gap
            if nearest is not None:
                found[name] = nearest
                total += distance
        if len(found) < len(PARTIALS):
            continue
        if best is None or total < best[0]:
            best = (total, candidate, found)
    if best is None:
        return None, {}
    return best[1], best[2]


def signature(peaks: list[float], nominal: float) -> dict:
    """Where the casting left the partials the founder does not tune."""
    out = {}
    for ratio in UPPER_RATIOS:
        target = nominal * ratio
        nearest, distance = None, None
        for peak in peaks:
            gap = abs(cents_between(peak, target))
            if gap <= UPPER_WINDOW_CENTS and (distance is None or gap < distance):
                nearest, distance = peak, gap
        if nearest is not None:
            out[ratio] = cents_between(nearest, target)
    return out


def distance(a: dict, b: dict) -> float:
    """How far apart two castings look, over the partials both runs recorded."""
    shared = [r for r in UPPER_RATIOS if r in a and r in b]
    if not shared:
        return float("inf")
    return sum(abs(a[r] - b[r]) for r in shared) / len(shared)


def seed_groups(signatures: dict) -> list[list[str]]:
    """Group only the runs that recorded ALL THREE upper partials.

    Comparing two runs over a subset of components is unreliable: bells differ
    by tens of cents averaged over the three, but any one component can coincide
    by chance, and agglomerating on shared subsets put bell-06 with bell-08.
    The runs with a complete signature are unambiguous, so they form the seeds
    and everything else is measured against those.
    """
    complete = [sid for sid in sorted(signatures)
                if len(signatures[sid]) == len(UPPER_RATIOS)]
    groups = [[sid] for sid in complete]
    while True:
        best, pair = None, None
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                gaps = [distance(signatures[a], signatures[b])
                        for a in groups[i] for b in groups[j]]
                mean = sum(gaps) / len(gaps)
                if best is None or mean < best:
                    best, pair = mean, (i, j)
        if best is None or best > SIGNATURE_WINDOW_CENTS:
            return groups
        i, j = pair
        groups[i] = groups[i] + groups[j]
        del groups[j]


def centroid(group: list[str], signatures: dict) -> dict:
    out = {}
    for ratio in UPPER_RATIOS:
        seen = [signatures[sid][ratio] for sid in group
                if ratio in signatures[sid]]
        if seen:
            out[ratio] = sorted(seen)[len(seen) // 2]
    return out

# A partly-recorded run is NOT matched against the groups. Where the analyser
# missed an upper partial, the nearest peak inside the search window is often
# clutter, and it comes back looking like a perfectly ordinary reading: one run
# of bell-06, whose casting puts its 1.2 partial 42 cents flat, reported it 40
# cents sharp. Two components with one of them spurious point confidently at
# the wrong bell, so such a run is left to the book and the descent instead.


def read_sessions(folder: pathlib.Path) -> dict[str, list[float]]:
    """Every run on the analyser's tapes, as run id -> peak frequencies.

    A run's block starts with `* RUN <id>` and each peak follows on its own
    `PEAK` line. The tapes carry no dates and the runs are not in any order, so
    nothing here says when anything happened or what it was of.
    """
    out: dict[str, list[float]] = {}
    for path in sorted(folder.glob("*.log")):
        current = None
        for line in path.read_text(encoding="utf-8").splitlines():
            run = re.match(r"\*\s*RUN\s+(\S+)", line)
            if run:
                current = run.group(1)
                out.setdefault(current, [])
                continue
            peak = re.match(r"\s+PEAK\s+([0-9.]+)\s*$", line)
            if peak and current:
                out[current].append(float(peak.group(1)))
    return {sid: peaks for sid, peaks in out.items() if peaks}


def read_daybook(path: pathlib.Path):
    dates, named = {}, {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            dates[row["session"]] = row["date"]
            if row["bell"]:
                named[row["session"]] = row["bell"]
    return dates, named


def drops(group: list[str], dates: dict, nominals: dict) -> list[float]:
    """Cents the pitch fell at each step, in date order. Negative means it rose."""
    ordered = sorted(group, key=lambda sid: dates[sid])
    return [cents_between(nominals[ordered[k]], nominals[ordered[k + 1]])
            for k in range(len(ordered) - 1)]


def cut_limit(groups: list[list[str]], dates: dict, nominals: dict) -> float:
    """The largest fall in pitch that can still be one bell's run of cuts.

    Two things pull against each other. A run missing from a seed makes the
    next step span two or three cuts, so the limit must allow several cuts'
    worth. But the ring's bells are only a couple of hundred cents apart, and a
    limit that large lets a session join its NEIGHBOUR'S chain as one more cut:
    at 202 cents, bell-03's last cut fitted bell-02 as well as its own. A
    percentile of the observed steps then swung the other way and refused a
    genuine two-cut gap on bell-05.

    Both quantities are measurable from the seeds, so neither is guessed: allow
    up to four ordinary cuts, but stay clearly short of the spacing between one
    bell and the next.
    """
    steps = sorted(step for group in groups
                   for step in drops(group, dates, nominals) if step > 0)
    if not steps:
        return float("inf")
    typical_cut = steps[len(steps) // 2]
    # The spacing between one bell and the next, from the MEDIAN gap between
    # the groups rather than the smallest. A group whose last runs are missing
    # sits higher than the bell really does, so the closest pair of groups can
    # be an artefact: on one draw it read 86 cents, which pulled the limit down
    # to 73 and left seven blind last cuts with nowhere to go at all.
    lowest = sorted(min(nominals[s] for s in group) for group in groups)
    gaps = sorted(cents_between(lowest[k + 1], lowest[k])
                  for k in range(len(lowest) - 1))
    spacing = gaps[len(gaps) // 2] if gaps else float("inf")
    return min(4.0 * typical_cut, 0.85 * spacing)


def accepts(group: list[str], sid: str, dates: dict, nominals: dict,
            limit: float) -> bool:
    """Can this run sit in that bell's chain, at the date the book gives it?

    Only the two steps either side of it are evidence. Re-checking the whole
    chain was wrong: where several of a bell's runs are missing from its seed
    one existing step spans them all, and if that step is wider than the limit
    the bell could never accept anything again - which is how a last cut named
    correctly by the book was refused by its own bell.
    """
    ordered = sorted(group, key=lambda s: dates[s])
    before = [s for s in ordered if dates[s] < dates[sid]]
    after = [s for s in ordered if dates[s] > dates[sid]]
    if before:
        step = cents_between(nominals[before[-1]], nominals[sid])
        if not -TIE_CENTS <= step <= limit:
            return False
    if after:
        step = cents_between(nominals[sid], nominals[after[0]])
        if not -TIE_CENTS <= step <= limit:
            return False
    return bool(before or after)


def span(group: list[str], nominals: dict) -> float:
    lo = min(nominals[s] for s in group)
    hi = max(nominals[s] for s in group)
    return cents_between(hi, lo)


def merge_recast_groups(groups: list[list[str]], named: dict) -> list[list[str]]:
    """Join two groups that are one bell recast, leaving the ring eight.

    A bell that cracked and was recast carries two castings, so its work
    arrives as two groups and the ring looks like nine bells. Nothing in the
    peaks links them - the metal is different - and pitch does not either,
    because the new casting was cut down through the same range the old one
    was. The only thing that says they are one bell is the book, which names
    runs in both by the same name.

    So the book is structural here, not a tidy-up: without it the ring cannot
    even be counted. Names are weighed rather than trusted, because a fifth of
    them are wrong; the pair joined is the one with the most agreement, and
    only while there are more groups than bells.
    """
    groups = [list(g) for g in groups]
    while len(groups) > RING_SIZE:
        # The shared name must be what the book mostly calls BOTH groups, and
        # must appear at least twice in each. Weighing raw agreement was not
        # enough: a fifth of the names are wrong, one coincidence was enough to
        # weld two unrelated bells together, and the attribution fell to 62%.
        best, pair = 0, None
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                left = [named[s] for s in groups[i] if s in named]
                right = [named[s] for s in groups[j] if s in named]
                if not left or not right:
                    continue
                top_left = max(set(left), key=left.count)
                top_right = max(set(right), key=right.count)
                if top_left != top_right:
                    continue
                if left.count(top_left) < 2 or right.count(top_right) < 2:
                    continue
                weight = left.count(top_left) + right.count(top_right)
                if weight > best:
                    best, pair = weight, (i, j)
        if pair is None:
            return groups
        i, j = pair
        groups[i] = groups[i] + groups[j]
        del groups[j]
    return groups


def split_wide_groups(groups: list[list[str]], nominals: dict) -> list[list[str]]:
    """Split a group that covers more pitch than one bell's work can.

    Two bells cast from the same mould carry the SAME casting, so nothing in
    their upper partials separates them and their runs arrive as one group of
    twenty odd. What gives them away is pitch: a single bell's run of cuts
    spans a few hundred cents, and this group spans far more than any other
    does, with a clear gap in the middle where one bell's work ends and the
    other's begins.

    So this is the one place pitch does the work - the reverse of everywhere
    else on these tapes, where the runs interleave and pitch settles nothing.
    """
    spans = sorted(span(g, nominals) for g in groups if len(g) > 1)
    if not spans:
        return groups
    typical = spans[len(spans) // 2]
    out: list[list[str]] = []
    for group in groups:
        if (len(group) >= 2 * MIN_SEED_RUNS
                and span(group, nominals) > typical * WIDE_GROUP_FACTOR):
            ordered = sorted(group, key=lambda s: nominals[s])
            gap, at = max(
                (cents_between(nominals[ordered[k + 1]], nominals[ordered[k]]), k)
                for k in range(len(ordered) - 1))
            out.append(ordered[:at + 1])
            out.append(ordered[at + 1:])
        else:
            out.append(group)
    return out


def place_one(groups: list[list[str]], sid: str, dates: dict, nominals: dict,
              named: dict, index_of: dict, limit: float,
              signatures: dict | None = None,
              centroids: list[dict] | None = None):
    """Which group a book-named run belongs in, or None if it cannot be told.

    Shared with the build's diagnostics so the two cannot drift apart: a
    diagnostic carrying its own copy of this reported placements the reference
    was not making, twice.

    Where the run recorded PART of its casting, that part overrules the book.
    Two components are not enough to pick a bell out of eight, but they are
    plenty to rule one out, and the book's names are the unreliable half of the
    evidence: one run of bell-03 was named bell-02, fitted both chains on pitch
    and date, and was taken at its word - and because it was dated late it then
    became bell-02's answer.
    """
    fits = [index for index, group in enumerate(groups)
            if accepts(group, sid, dates, nominals, limit)]
    sig = (signatures or {}).get(sid)
    if sig and centroids:
        consistent = [index for index in fits
                      if distance(sig, centroids[index]) <= CASTING_VETO_CENTS]
        if consistent:
            fits = consistent
    claimed = index_of.get(named.get(sid))
    if claimed in fits:
        return claimed, fits
    if len(fits) == 1:
        return fits[0], fits
    return None, fits


def descends(group: list[str], dates: dict, nominals: dict,
             limit: float) -> bool:
    """Ordered by date, does the pitch fall by a believable amount every time?

    Requiring only that it falls is not enough. A session that belongs to a
    light bell sits far below a heavy one's whole run, so appending it to the
    heavy bell's chain still "descends" - and that is exactly the placement the
    day-book's wrong name invites. A cut takes a bounded amount of metal off,
    so a step of eight hundred cents is not a cut, and the limit comes from the
    steps the confidently grouped runs actually show.
    """
    return all(0.0 < step <= limit for step in drops(group, dates, nominals))


def solve(root: pathlib.Path):
    """Read the tapes and the book and work out what every run was of.

    Returns the eight groups in pitch order (heaviest last) together with
    everything the caller needs to read an answer off them. Both the
    attribution and the tuning book come from this, so the two cannot disagree.
    """
    peaks_by_session = read_sessions(root / "logs")
    dates, named = read_daybook(root / "daybook.csv")

    nominals, partials_by_session, signatures = {}, {}, {}
    for sid, peaks in peaks_by_session.items():
        nominal, found = find_nominal(peaks)
        if nominal is None:
            continue
        nominals[sid] = nominal
        partials_by_session[sid] = found
        sig = signature(peaks, nominal)
        if sig:
            signatures[sid] = sig

    # The ring is the castings seen more than once. A job from another bench
    # was on the bench once and stands alone whatever its pitch.
    seeds = [g for g in seed_groups(signatures) if len(g) >= MIN_SEED_RUNS]
    # Before taking the eight largest: a group covering more pitch than one
    # bell's work can is two bells from one mould, and counting it once leaves
    # the ring a bell short.
    seeds = split_wide_groups(seeds, nominals)
    seeds = [g for g in seeds if len(g) >= MIN_SEED_RUNS]
    # And then the other way: a bell recast partway carries two castings, so
    # its work arrives as two groups. Split first, merge second - a group that
    # is two bells has to be broken before the book is asked which groups are
    # one bell, or the book is asked about the wrong things.
    seeds = merge_recast_groups(seeds, named)
    seeds.sort(key=len, reverse=True)
    groups = seeds[:RING_SIZE]

    # How big a cut is, measured on the SEEDS, before anything uncertain has
    # been added to them. Taking it after placement let one wrong assignment
    # stretch the limit to 1450 cents, which then admitted almost anything.
    limit = cut_limit(groups, dates, nominals)

    placed = {sid for group in groups for sid in group}

    # Everything else - the runs with no signature at all and the partly
    # recorded ones - is placed from the book and the descent.
    # What is left is placed only if the BOOK names it. The book is this ring's
    # book: a run it does not name is a job from another bench, and trying to
    # fit those by pitch alone put five of them inside the ring. A named run
    # goes where the book says, unless putting it there breaks the descent - in
    # which case the book is wrong about it, and it goes to the one bell it
    # does fit.
    # Name the groups before using the book, so a claim can be matched to a
    # group at all. The heaviest bell is the lowest in pitch, which is what
    # orders the answer anyway - and it is far steadier than asking what the
    # book calls a group. Reading the group's own majority book name put two
    # runs of bell-08 into bell-07, because the book happened to name one of
    # bell-07's runs wrongly and the vote tied.
    groups.sort(key=lambda g: min(nominals[s] for s in g))
    index_of = {f"bell-{RING_SIZE - i:02d}": i for i in range(len(groups))}

    # Runs whose attribution rests on strong evidence: a complete casting in a
    # seed, or the book naming them outright. The answer for a bell is read off
    # one single run, so it must never be read off a run placed by the weakest
    # rule below - one matching component plus a descent that fits. Those are
    # right often enough to be worth calling, and wrong often enough that when
    # one landed late in a group and became its "last cut" it cost that bell
    # all five partials.
    confident = set(placed)

    centroids = [centroid(group, signatures) for group in groups]
    unplaced = [sid for sid in nominals if sid not in placed and sid in named]
    for sid in sorted(unplaced, key=lambda s: dates[s]):
        chosen, _ = place_one(groups, sid, dates, nominals, named,
                              index_of, limit, signatures, centroids)
        if chosen is not None:
            groups[chosen] = groups[chosen] + [sid]
            placed.add(sid)
            confident.add(sid)

    # Runs the book never named and whose casting was only partly recorded.
    # They were left out entirely while only the eight last cuts were graded;
    # now every run's attribution is the answer, so each one has to be called.
    # A partial casting cannot pick a bell out of eight on its own, but with
    # the chains already built the descent settles most of them: take the one
    # group whose casting it matches and whose run of cuts it fits.
    for sid in sorted(set(nominals) - placed, key=lambda s: dates[s]):
        sig = signatures.get(sid)
        # Two components at least, and matched as tightly as the groups
        # themselves were. The generous veto window belongs to overruling the
        # book, not to claiming a run for the ring: at 16 cents it pulled five
        # jobs from other benches into it, because a job kept 22 cents clear of
        # every casting overall can still sit inside 16 on the two components
        # its run happened to record.
        # One component is enough when it is decisive. It cannot pick a bell
        # out of eight by itself, but combined with the descent - the run has
        # to fit that bell's chain at the date the book gives it - the pair is
        # often unique, and insisting on two left eight runs of the ring
        # uncalled.
        if not sig:
            continue
        fits = [index for index, group in enumerate(groups)
                if accepts(group, sid, dates, nominals, limit)
                and distance(sig, centroids[index]) <= SIGNATURE_WINDOW_CENTS]
        if len(fits) == 1:
            groups[fits[0]] = groups[fits[0]] + [sid]
            placed.add(sid)

    groups.sort(key=lambda g: min(nominals[s] for s in g))
    return groups, nominals, partials_by_session, dates, confident


def attribute(root: pathlib.Path) -> dict:
    """What every run on the tapes was of: a bell of this ring, or other work."""
    groups, nominals, _, _, _ = solve(root)
    out = {}
    for sid in read_sessions(root / "logs"):
        out[sid] = "other"
    for index, group in enumerate(groups, start=1):
        for sid in group:
            out[sid] = f"bell-{RING_SIZE + 1 - index:02d}"
    return out


def tune(root: pathlib.Path) -> list[dict]:
    groups, nominals, partials_by_session, dates, confident = solve(root)

    report = []
    for index, group in enumerate(groups, start=1):
        strong = [sid for sid in group if sid in confident] or group
        last = max(strong, key=lambda sid: dates[sid])
        nominal = nominals[last]
        found = partials_by_session[last]

        entries = []
        for name in ORDER:
            measured = found.get(name)
            if measured is None:
                entries.append({"partial": name, "cents": None, "in_true": False})
                continue
            offset = cents_between(measured, nominal * PARTIALS[name])
            entries.append({
                "partial": name,
                "cents": round(offset, 3),
                "in_true": bool(abs(offset) <= IN_TRUE_CENTS),
            })
        report.append({
            "bell": f"bell-{9 - index:02d}",
            "in_true": all(e["in_true"] for e in entries),
            "partials": entries,
        })

    report.sort(key=lambda r: r["bell"])
    return report


def _majority(group: list[str], named: dict) -> str | None:
    """What the book calls this group, where it says anything at all."""
    votes = {}
    for sid in group:
        if sid in named:
            votes[named[sid]] = votes.get(named[sid], 0) + 1
    if not votes:
        return None
    return max(votes, key=lambda k: votes[k])
