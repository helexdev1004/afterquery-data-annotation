"""Replay every reading of the note against the graded campaigns.

    python rival_readings.py

The note leaves five matters open. With the one reading it does not signpost -
that the store releases its oldest SEED first, not its oldest lot - they make a
grid. This walks the whole grid and asserts what the task rests on:

  * exactly one reading reproduces all fourteen worked campaigns;
  * every reading that goes by the age of the seed clears the bar;
  * every reading that goes by the age of the lot falls short of it;
  * nothing lands between the two.

None of this runs at marking time; it is here so the claim can be checked.
"""

import itertools

import make_cases
import releases

MIN_FREE = 100
VALID_DAYS = 365
NOTHING = "-"
EXACT = 10
BAR = 2790


SIGNPOSTED = {
    "release_cmp": (">=", ">"),
    "split_test_day": ("parent", "split"),
    "same_day_test": ("counts", "later"),
    "retired_counts": ("no", "yes"),
    "topup_day": ("older", "keep", "topup"),
}
CRUX = {"age_of": ("seed", "lot")}
TRUTH = {"release_cmp": ">=", "split_test_day": "parent", "same_day_test": "counts",
         "retired_counts": "no", "topup_day": "older",
         "age_of": "seed"}
NOTHING = "-"


def meets(value, bar, how):
    return value >= bar if how == ">=" else value > bar


def run(case, reading):
    standards = case["standards"]
    lots, answers = {}, []

    for event in case["events"]:
        kind, day = event["kind"], event["day"]

        if kind == "DEPOSIT":
            lots[event["lot"]] = dict(
                accession=event["accession"], seeds=event["seeds"],
                test=event["test"], test_day=day, retired=False,
                held=event["test"] < standards[event["accession"]],
                seed_day=day, lot_day=day)

        elif kind == "TEST":
            lot = lots[event["lot"]]
            lot["test"], lot["test_day"] = event["test"], day
            lot["held"] = event["test"] < standards[lot["accession"]]

        elif kind == "SPLIT":
            parent = lots[event["parent"]]
            parent["seeds"] -= event["seeds"]
            lots[event["child"]] = dict(
                accession=parent["accession"], seeds=event["seeds"],
                test=parent["test"], retired=False, held=parent["held"],
                test_day=parent["test_day"] if reading["split_test_day"] == "parent" else day,
                seed_day=parent["seed_day"], lot_day=day)

        elif kind == "TOPUP":
            giver, taker, moved = lots[event["from"]], lots[event["into"]], event["seeds"]
            giver["seeds"] -= moved
            total = taker["seeds"] + moved
            taker["test"] = int(round(
                (taker["test"] * taker["seeds"] + giver["test"] * moved) / total))
            taker["seeds"] = total
            taker["held"] = taker["test"] < standards[taker["accession"]]
            # the seed in the lot is as old as its oldest part
            taker["seed_day"] = min(taker["seed_day"], giver["seed_day"])
            if reading["topup_day"] == "older":
                taker["test_day"] = min(taker["test_day"], giver["test_day"])
            elif reading["topup_day"] == "topup":
                taker["test_day"] = day

        elif kind == "REGEN":
            old = lots[event["lot"]]
            old["retired"] = True
            held = event["test"] < standards[old["accession"]]
            lots[event["new_lot"]] = dict(
                accession=old["accession"], seeds=event["seeds"], test=event["test"],
                test_day=day, retired=False, held=held, seed_day=day, lot_day=day)

        elif kind == "WITHDRAW":
            lot = lots[event["lot"]]
            lot["seeds"] = max(0, lot["seeds"] - event["seeds"])

        elif kind == "DISCARD":
            lots[event["lot"]]["retired"] = True

        elif kind == "REQUEST":
            answers.append(pick(lots, event["accession"], day, reading))

    return answers


def pick(lots, accession, day, reading):
    able = []
    for name, lot in lots.items():
        if lot["accession"] != accession:
            continue
        if lot["retired"] and reading["retired_counts"] == "no":
            continue
        if lot["held"]:
            continue
        if not meets(lot["seeds"], MIN_FREE, reading["release_cmp"]):
            continue
        age = day - lot["test_day"]
        if reading["same_day_test"] == "later" and age == 0:
            continue
        if age > VALID_DAYS:
            continue
        able.append((name, lot))
    if not able:
        return NOTHING
    key_day = "seed_day" if reading["age_of"] == "seed" else "lot_day"
    able.sort(key=lambda pair: (pair[1][key_day], pair[0]))
    return able[0][0]


def every_reading():
    keys = list(SIGNPOSTED) + list(CRUX)
    options = [SIGNPOSTED[k] for k in SIGNPOSTED] + [CRUX[k] for k in CRUX]
    for picks in itertools.product(*options):
        yield dict(zip(keys, picks))

def score(given, wanted):
    return sum(EXACT for a, b in zip(given, wanted) if a == b)


def main():
    worked, graded = make_cases.worked_set(), make_cases.graded_set()
    worked_truth = [releases.play(c) for c in worked]
    graded_truth = sum([releases.play(c) for c in graded], [])
    top = len(graded_truth) * EXACT

    survivors, by_seed, by_lot = [], [], []
    for reading in every_reading():
        if [run(c, reading) for c in worked] == worked_truth:
            survivors.append(reading)
        points = score(sum([run(c, reading) for c in graded], []), graded_truth)
        (by_seed if reading["age_of"] == "seed" else by_lot).append(points)

    print("worked answers %d, graded answers %d, top %d"
          % (sum(len(a) for a in worked_truth), len(graded_truth), top))
    print("readings in the grid %d, reproducing every worked answer %d"
          % (len(by_seed) + len(by_lot), len(survivors)))
    print("age of the seed : %d..%d" % (min(by_seed), max(by_seed)))
    print("age of the lot  : %d..%d" % (min(by_lot), max(by_lot)))
    print("bar %d, band %d..%d" % (BAR, max(by_lot), min(by_seed)))

    assert len(survivors) == 1, "the worked campaigns do not settle one reading"
    assert survivors[0] == TRUTH, "the surviving reading is not the reference"
    assert score(sum([run(c, TRUTH) for c in graded], []), graded_truth) == top
    assert max(by_lot) < BAR < min(by_seed), "the bar does not sit in the band"
    print("OK")


if __name__ == "__main__":
    main()
