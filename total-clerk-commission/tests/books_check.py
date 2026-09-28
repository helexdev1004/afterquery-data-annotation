"""Every reading of the counter's books, against the sealed commission.

    python books_check.py
"""

import itertools
import json

import pay_run

COUNTER = pay_run.base()
LINES_THAT_MAY_BE_WRONG = 2


def right(said, want):
    return said is not None and abs(said - want) <= 0.50 + 1e-9


def main():
    sealed = json.loads((COUNTER / "sealed.json").read_text())
    desks = json.loads((COUNTER / "desks.json").read_text())
    total, trouble = len(sealed), []
    names = list(pay_run.THE_BOOKS)
    scores = {}
    for combo in itertools.product(*[[pay_run.THE_BOOKS[n],
                                      pay_run.THE_NOTE[n]] for n in names]):
        got, _ = pay_run.commission(COUNTER, dict(zip(names, combo)))
        scores[combo] = sum(right(got.get(k), sealed[k]) for k in sealed)
    books = tuple(pay_run.THE_BOOKS[n] for n in names)
    note = tuple(pay_run.THE_NOTE[n] for n in names)
    second = max(v for k, v in scores.items() if k != books)
    print("readings: %d" % len(scores))
    print("  %2d  by the books" % scores[books])
    print("  %2d  by the note" % scores[note])
    without = {}
    for i, n in enumerate(names):
        c = list(books)
        c[i] = pay_run.THE_NOTE[n]
        without[n] = scores[tuple(c)]
        print("  %2d  by the books except %s" % (without[n], n))
    print("  %2d  the best reading that is not the books'" % second)

    got, seen = pay_run.commission(COUNTER, pay_run.THE_BOOKS)
    naive, _ = pay_run.commission(COUNTER, dict(pay_run.THE_BOOKS,
                                                desks="as_listed"))
    used_by = {d["used"]: clerk for clerk, d in desks.items()}
    moved, least_share = 0, 1.0
    for login, s in sorted(seen.items()):
        moved += used_by[login] != s["listed"]
        least_share = min(least_share, s["share"])
        print("  %s  listed to %-12s in the hand of %-12s (%.2f of its orders)"
              "%s" % (login, s["listed"], s["by_hand"], s["share"],
                      "   DESKS CHANGED" if used_by[login] != s["listed"] else ""))
        if s["by_hand"] != used_by[login]:
            trouble.append("the hands misplace %s" % login)
    quarter = {}
    for k, v in naive.items():
        quarter[k.split("/")[0]] = quarter.get(k.split("/")[0], 0.0) + v
    sizes = sorted(quarter.values())
    print("  a clerk's quarter, read as listed: %.0f to %.0f pounds"
          % (sizes[0], sizes[-1]))

    if scores[books] != total:
        trouble.append("the books' reading does not get every line")
    if second > total - LINES_THAT_MAY_BE_WRONG - 1:
        trouble.append("a wrong reading is within the allowance")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (COUNTER / "check.json").write_bytes(json.dumps(dict(
            total=total, may_be_wrong=LINES_THAT_MAY_BE_WRONG, second=second,
            by_note=scores[note], without=without, readings=len(scores),
            clerks=len(seen), moved=moved, least_share="%.2f" % least_share,
            orders=len(pay_run.table(COUNTER / "order_book.csv")),
            credits=len(pay_run.table(COUNTER / "credit_notes.csv"))),
            indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
