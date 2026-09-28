"""A quarter at the trade counter, then the books as the counter system has them.

    python trade_quarter.py [outdir]

The people come first: each order is written up by one of six clerks, in that
clerk's own hand - the way they note the kind of order, their abbreviations,
their capitals - and so is each credit note, which the clerk signs by name.
Commission is reckoned from who really wrote what. Then the order book is
exported, and it knows a clerk only by the login on the terminal. Two clerks
changed desks at the start of the quarter and have worked all of it on each
other's terminals, still logged in.

Nothing in the figures says so: every login still has a clerk, and the two
clerks' months are much of a size. What says it is the writing. A login's
orders are in one hand throughout, and the signed credit notes show whose hand
that is.
"""

import csv
import json
import pathlib
import random
import sys
from datetime import date, timedelta

SEED = 4123105
QUARTER = (date(2026, 7, 1), date(2026, 9, 30))
RATES = {"trade account": 1.0, "cash sale": 1.5, "special order": 2.5,
         "plant hire": 2.0}

CLERKS = (
    # name, login, login really used, how they write each kind, joiner, times
    ("A. Hartley", "CT01", "CT01",
     ("TRADE A/C", "CASH SALE", "SPECIAL ORDER", "PLANT HIRE"), " + ", "X", str.upper),
    ("B. Ormerod", "CT02", "CT02",
     ("trade acct", "cash", "special ord.", "hire"), " and ", "x", str.lower),
    ("C. Pollard", "CT03", "CT05",
     ("T/A", "C/S", "S/O", "P/H"), ", ", " x ", None),
    ("D. Sagar", "CT04", "CT04",
     ("Account -", "Cash -", "Special -", "Hire -"), " & ", " no. ", None),
    ("E. Thwaite", "CT05", "CT03",
     ("acc.", "csh.", "spec.", "hire eqpt"), "; ", "x", None),
    ("F. Whiteley", "CT06", "CT06",
     ("(trade)", "(cash)", "(special)", "(plant)"), " / ", " off ", None),
)
GOODS = ("4x2 sawn 4.8m", "bags cement", "sheets 18mm ply", "lengths 110 soil pipe",
         "tonne bags sharp sand", "facing bricks", "rolls DPC", "padstones",
         "boxes 5x80 screws", "sheets 12.5 plasterboard", "lintels 1200",
         "bags multi-finish", "lengths 22mm copper", "concrete blocks 7N")
PLANT = ("mini digger", "cement mixer", "plate compactor", "tower scaffold")


def written(rng, clerk, kind):
    name, _, _, kinds, joiner, times, case = clerk
    label = kinds[list(RATES).index(kind)]
    if kind == "plant hire":
        body = "%s %d days" % (rng.choice(PLANT), rng.randrange(1, 8))
    else:
        items = rng.sample(GOODS, rng.randrange(1, 4))
        body = joiner.join("%d%s%s" % (rng.randrange(2, 60), times, g)
                           if times.strip() in ("x", "X") else
                           "%d%s%s" % (rng.randrange(2, 60), times, g)
                           for g in items)
    text = "%s %s" % (label, body)
    return case(text) if case else text


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "counter"
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    days = (QUARTER[1] - QUARTER[0]).days + 1
    orders, credits, owed = [], [], {}
    order_no, credit_no = 61000, 900

    for clerk in CLERKS:
        name, login, used = clerk[0], clerk[1], clerk[2]
        busy = rng.uniform(0.8, 1.3)
        for _ in range(int(rng.uniform(520, 640) * busy)):
            day = QUARTER[0] + timedelta(days=rng.randrange(days))
            if day.weekday() == 6:
                continue
            kind = rng.choices(list(RATES), weights=(50, 28, 12, 10))[0]
            amount = round(rng.lognormvariate(5.3, 0.9), 2)
            order_no += rng.randrange(1, 4)
            orders.append(dict(order=order_no, date=day.isoformat(),
                               login=used, description=written(rng, clerk, kind),
                               net_gbp="%.2f" % amount, _who=name, _kind=kind))
            key = (name, day.strftime("%Y-%m"))
            owed[key] = owed.get(key, 0.0) + amount * RATES[kind] / 100.0
    # the counter system numbers orders as they are taken, whoever takes them
    rng.shuffle(orders)
    orders.sort(key=lambda o: o["date"])
    for n, o in enumerate(orders):
        o["order"] = 61001 + 2 * n + rng.randrange(2)

    # credit notes: written and signed by the clerk who took the goods back,
    # and that clerk's commission is reduced at the rate of the order's kind
    for clerk in CLERKS:
        name = clerk[0]
        for _ in range(rng.randrange(40, 60)):
            against = rng.choice(orders)
            day = min(QUARTER[1], date.fromisoformat(against["date"])
                      + timedelta(days=rng.randrange(1, 15)))
            amount = round(float(against["net_gbp"]) * rng.uniform(0.1, 0.6), 2)
            credit_no += 1
            credits.append(dict(credit_note=credit_no, date=day.isoformat(),
                                signed=name, against_order=against["order"],
                                description=written(rng, clerk, against["_kind"]),
                                net_gbp="%.2f" % amount))
            key = (name, day.strftime("%Y-%m"))
            owed[key] = owed.get(key, 0.0) \
                - amount * RATES[against["_kind"]] / 100.0
    rng.shuffle(credits)
    credits.sort(key=lambda c: c["date"])
    for n, c in enumerate(credits):
        c["credit_note"] = 901 + n

    with open(outdir / "order_book.csv", "w", newline="") as handle:
        out = csv.DictWriter(handle, lineterminator="\n", extrasaction="ignore",
                             fieldnames=["order", "date", "login",
                                         "description", "net_gbp"])
        out.writeheader()
        out.writerows(orders)
    with open(outdir / "credit_notes.csv", "w", newline="") as handle:
        out = csv.DictWriter(handle, lineterminator="\n",
                             fieldnames=list(credits[0]))
        out.writeheader()
        out.writerows(credits)
    with open(outdir / "clerks.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["clerk", "login"])
        out.writerows((c[0], c[1]) for c in CLERKS)
    with open(outdir / "rates.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["kind_of_order", "commission_pct"])
        out.writerows(RATES.items())
    sealed = {"%s/%s" % k: round(v, 2) for k, v in owed.items()}
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "desks.json").write_bytes(json.dumps(
        {c[0]: dict(login=c[1], used=c[2]) for c in CLERKS}, indent=1).encode())
    print("orders %d  credit notes %d  lines %d"
          % (len(orders), len(credits), len(sealed)))


if __name__ == "__main__":
    main()
