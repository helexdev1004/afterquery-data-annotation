"""Name the lot the store releases for each request.

    python3 releases.py  < campaign.json

One campaign arrives on standard input as JSON. Every REQUEST in it is answered
with one line: the name of the lot the store releases for it, or `-` if it has
nothing it can release.

Where the store's note leaves a matter open, this follows:

  * a lot holding exactly the minimum may go;
  * a lot split off carries the date of the test it inherits;
  * a test recorded on the day of a request is in effect for it;
  * a lot that has been grown out is off the list, whatever seed is left;
  * a lot topped up is only as current as the older of the two tests.

And the reading the note does not signpost: the store releases its oldest seed
first, and it is the age of the SEED that counts, not the age of the lot. Seed
keeps the day it was first deposited wherever it goes afterwards, so a lot made
up by topping one lot from another is as old as the older part of it.
"""

import json
import sys

MIN_SEEDS = 100
VALID_DAYS = 365
NOTHING = "-"


def play(campaign):
    standards = campaign["standards"]
    lots, answers = {}, []

    for event in campaign["events"]:
        kind, day = event["kind"], event["day"]

        if kind == "DEPOSIT":
            lots[event["lot"]] = dict(
                accession=event["accession"], seeds=event["seeds"],
                test=event["test"], test_day=day, retired=False,
                held=event["test"] < standards[event["accession"]],
                seed_day=day)

        elif kind == "TEST":
            lot = lots[event["lot"]]
            lot["test"], lot["test_day"] = event["test"], day
            lot["held"] = event["test"] < standards[lot["accession"]]

        elif kind == "SPLIT":
            parent = lots[event["parent"]]
            parent["seeds"] -= event["seeds"]
            lots[event["child"]] = dict(
                accession=parent["accession"], seeds=event["seeds"],
                test=parent["test"], test_day=parent["test_day"],
                retired=False, held=parent["held"], seed_day=parent["seed_day"])

        elif kind == "TOPUP":
            giver, taker, moved = lots[event["from"]], lots[event["into"]], event["seeds"]
            giver["seeds"] -= moved
            total = taker["seeds"] + moved
            taker["test"] = int(round(
                (taker["test"] * taker["seeds"] + giver["test"] * moved) / total))
            taker["seeds"] = total
            taker["held"] = taker["test"] < standards[taker["accession"]]
            taker["test_day"] = min(taker["test_day"], giver["test_day"])
            taker["seed_day"] = min(taker["seed_day"], giver["seed_day"])

        elif kind == "REGEN":
            old = lots[event["lot"]]
            old["retired"] = True
            lots[event["new_lot"]] = dict(
                accession=old["accession"], seeds=event["seeds"], test=event["test"],
                test_day=day, retired=False, seed_day=day,
                held=event["test"] < standards[old["accession"]])

        elif kind == "WITHDRAW":
            lot = lots[event["lot"]]
            lot["seeds"] = max(0, lot["seeds"] - event["seeds"])

        elif kind == "DISCARD":
            lots[event["lot"]]["retired"] = True

        elif kind == "REQUEST":
            answers.append(pick(lots, event["accession"], day))

    return answers


def pick(lots, accession, day):
    able = []
    for name, lot in lots.items():
        if lot["accession"] != accession or lot["retired"] or lot["held"]:
            continue
        if lot["seeds"] < MIN_SEEDS:
            continue
        if day - lot["test_day"] > VALID_DAYS:
            continue
        able.append((lot["seed_day"], name))
    return min(able)[1] if able else NOTHING


def main():
    print("\n".join(play(json.load(sys.stdin))))


if __name__ == "__main__":
    main()
