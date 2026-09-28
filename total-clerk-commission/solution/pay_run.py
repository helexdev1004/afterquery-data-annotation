"""Each clerk's commission for each month of the quarter.

    python pay_run.py [folder]        writes folder/commission.csv

`commission(folder, reading)` is the job. `reading` says, for each point on
which the books can differ from the accounts note, which to go by.
"""

import collections
import csv
import pathlib
import re
import sys

# every way a clerk starts a description, and the kind of order it means
HANDS = {
    "capitals": (r"^TRADE A/C\b", r"^CASH SALE\b", r"^SPECIAL ORDER\b",
                 r"^PLANT HIRE\b"),
    "initials": (r"^T/A\b", r"^C/S\b", r"^S/O\b", r"^P/H\b"),
    "dashes": (r"^Account -", r"^Cash -", r"^Special -", r"^Hire -"),
    "dotted": (r"^acc\.", r"^csh\.", r"^spec\.", r"^hire eqpt\b"),
    "lower": (r"^trade acct\b", r"^cash\b", r"^special ord\.", r"^hire\b"),
    "brackets": (r"^\(trade\)", r"^\(cash\)", r"^\(special\)", r"^\(plant\)"),
}
KINDS = ("trade account", "cash sale", "special order", "plant hire")

THE_BOOKS = {"initials": "read", "dotted": "read", "brackets": "read",
             "desks": "ask_the_hands"}
THE_NOTE = {"initials": "unclassed", "dotted": "unclassed",
            "brackets": "unclassed", "desks": "as_listed"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "counter"


def table(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def hand_and_kind(text, reading):
    """(whose way of writing this is, the kind of order) or (hand, None)."""
    for hand, starts in HANDS.items():
        for pattern, kind in zip(starts, KINDS):
            if re.match(pattern, text):
                if reading.get(hand, "read") != "read":
                    return hand, None
                return hand, kind
    return None, None


def commission(folder, reading):
    """{'A. Hartley/2026-07': pounds} and what was found about each login."""
    folder = pathlib.Path(folder)
    rates = {r["kind_of_order"]: float(r["commission_pct"]) / 100.0
             for r in table(folder / "rates.csv")}
    listed = {r["login"]: r["clerk"] for r in table(folder / "clerks.csv")}
    orders = table(folder / "order_book.csv")
    credits = table(folder / "credit_notes.csv")

    hand_of_login = collections.defaultdict(collections.Counter)
    for o in orders:
        hand_of_login[o["login"]][hand_and_kind(o["description"], {})[0]] += 1
    hand_of_clerk = collections.defaultdict(collections.Counter)
    for c in credits:
        hand_of_clerk[c["signed"]][hand_and_kind(c["description"], {})[0]] += 1
    whose_hand = {hands.most_common(1)[0][0]: clerk
                  for clerk, hands in hand_of_clerk.items()}
    at_login, seen = {}, {}
    for login, hands in hand_of_login.items():
        hand = hands.most_common(1)[0][0]
        by_hand = whose_hand.get(hand, listed[login])
        at_login[login] = by_hand \
            if reading["desks"] == "ask_the_hands" else listed[login]
        seen[login] = dict(listed=listed[login], hand=hand, by_hand=by_hand,
                           share=hands[hand] / sum(hands.values()))

    kind_of_order, out = {}, collections.defaultdict(float)
    for o in orders:
        _, kind = hand_and_kind(o["description"], reading)
        kind_of_order[o["order"]] = kind
        if kind:
            out["%s/%s" % (at_login[o["login"]], o["date"][:7])] += \
                float(o["net_gbp"]) * rates[kind]
    for c in credits:
        kind = kind_of_order.get(c["against_order"])
        if kind:
            out["%s/%s" % (c["signed"], c["date"][:7])] -= \
                float(c["net_gbp"]) * rates[kind]
    return {k: round(v, 2) for k, v in out.items()}, seen


if __name__ == "__main__":
    where = base()
    answer, _ = commission(where, THE_BOOKS)
    with open(where / "commission.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["clerk", "month", "commission_gbp"])
        for key in sorted(answer):
            clerk, month = key.split("/")
            sheet.writerow([clerk, month, "%.2f" % answer[key]])
    print("%d lines written" % len(answer))
