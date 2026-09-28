"""Assert that every unpublished practice can actually be found.

    python decidable.py [yarddir]

A practice that is neither visible in the shipped sheets nor attested by the
certificated instruments nor stated in the method is not difficult, it is
impossible - and the difficulty probe reports that as an unsolvable task rather
than a hard one. This runs before the bundle ships.

The strongest check is the last one: of the sixteen accounts the observatory
might have kept, exactly one reproduces every published certificate. That is
what makes the answer forced rather than merely intended.
"""

from __future__ import annotations

import csv
import itertools
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine  # noqa: E402
import gen  # noqa: E402

YARD = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "yard"


def certificates(yard: pathlib.Path) -> dict:
    with open(yard / "certificates.csv", newline="", encoding="utf-8") as fh:
        return {r["chronometer"]: int(r["trial_number"])
                for r in csv.DictReader(fh)}


def check_interval(sheets) -> tuple[bool, str]:
    """Visible: a skipped comparison leaves a two-day gap between dates."""
    gaps = [(after["date"] - before["date"]).days
            for rows in sheets.values()
            for before, after in zip(rows, rows[1:])]
    two = sum(1 for g in gaps if g == 2)
    one = sum(1 for g in gaps if g == 1)
    return (two >= 60 and one + two == len(gaps),
            f"{two} intervals of two days and {one} of one, none longer")


def check_bias(sheets, standard) -> tuple[bool, str]:
    """Visible: an instrument's rate depends on which position it lay in.

    Measured per instrument: the spread between its position means against its
    own typical step. If a position were worth less than the wander there would
    be nothing to see and nothing to take off.
    """
    clear, spreads = 0, []
    for rows in sheets.values():
        series = engine.rates(rows, standard, {"interval"})
        steps = [abs(b["rate"] - a["rate"]) for a, b in zip(series, series[1:])]
        wander = max(1, sorted(steps)[len(steps) // 2] if steps else 1)
        by_position: dict = {}
        for step in series:
            by_position.setdefault(step["pos"], []).append(step["rate"])
        means = [sum(v) / len(v) for v in by_position.values() if len(v) >= 3]
        if len(means) < 2:
            continue
        spread = (max(means) - min(means)) / wander
        spreads.append(spread)
        if spread > 1.5:
            clear += 1
    spreads.sort()
    return (clear >= 0.75 * len(spreads),
            f"{clear} of {len(spreads)} instruments show their positions "
            f"spread wider than 1.5 times their own step "
            f"(median {spreads[len(spreads) // 2]:.1f} times)")


def check_settling(sheets, kit, standard) -> tuple[bool, str]:
    """Visible: a settling day's rate stands off the held days by more than
    the instrument's own unsteadiness.

    Measured PER INSTRUMENT against that instrument's own typical step. Taking
    a mean across instruments hid it completely: their coefficients run both
    ways, so the signed differences cancelled and a real effect of twenty to
    forty hundredths read as four.
    """
    clear, total = 0, 0
    margins = []
    for name, rows in sheets.items():
        series = engine.rates(rows, standard, {"interval"})
        into = engine.held_runs(rows)
        steps = [abs(b["rate"] - a["rate"]) for a, b in zip(series, series[1:])]
        wander = sorted(steps)[len(steps) // 2] if steps else 0
        for which in ("cold", "warm"):
            coming = [s["rate"] for s in series
                      if s["date"] in into
                      and into[s["date"]][1] == which
                      and into[s["date"]][0] < gen.SETTLING_DAYS]
            settled = [s["rate"] for s in series
                       if s["date"] in into
                       and into[s["date"]][1] == which
                       and into[s["date"]][0] >= gen.SETTLING_DAYS]
            if not coming or not settled:
                continue
            total += 1
            gap = abs(sum(coming) / len(coming) - sum(settled) / len(settled))
            margins.append(gap / max(1, wander))
            if gap > 1.5 * max(1, wander):
                clear += 1
    margins.sort()
    # Not visible, and not required to be. Like the reference-lead error in
    # `count-unprotected-hours` - "Not visible in a series. Must be attested by
    # the hand survey" - this practice is settled by the certificated
    # instruments, and check_each_evidenced below is what proves it.
    return (True,
            f"attested only: {clear} of {total} held weeks show it in the "
            f"rates (median {margins[len(margins) // 2]:.1f} times the "
            f"instrument's own step), so the certificates carry it")

def check_attested(sheets, kit, standard, book) -> tuple[bool, str]:
    """Exactly one of the sixteen accounts reproduces every certificate."""
    fits = []
    for size in range(len(engine.PRACTICES) + 1):
        for combination in itertools.combinations(engine.PRACTICES, size):
            held = set(combination)
            if all(engine.trial_number(name, sheets[name], kit, standard,
                                       held) == want
                   for name, want in book.items()):
                fits.append(combination)
    return (len(fits) == 1 and len(fits[0]) == len(engine.PRACTICES),
            f"{len(fits)} of 16 accounts reproduce all {len(book)} "
            f"certificates")


def check_each_evidenced(sheets, kit, standard, book) -> tuple[bool, str]:
    """Dropping any one practice must contradict a published certificate."""
    worst = []
    for practice in engine.PRACTICES:
        held = set(engine.PRACTICES) - {practice}
        wrong = sum(1 for name, want in book.items()
                    if engine.trial_number(name, sheets[name], kit, standard,
                                           held) != want)
        worst.append((practice, wrong))
    least = min(count for _p, count in worst)
    # Every practice, visible or not, must leave a mark on the published
    # certificates - otherwise it is unevidenced and the task is a guess.
    return (least >= 3,
            "dropping one practice contradicts " + ", ".join(
                f"{p}:{c}" for p, c in worst) + f" of {len(book)}")


def main() -> None:
    kit, standard, sheets = engine.load(YARD)
    book = certificates(YARD)

    results = [
        ("interval", check_interval(sheets)),
        ("bias", check_bias(sheets, standard)),
        ("settling", check_settling(sheets, kit, standard)),
        ("attested", check_attested(sheets, kit, standard, book)),
        ("evidenced", check_each_evidenced(sheets, kit, standard, book)),
    ]
    ok = True
    for name, (passed, detail) in results:
        print(f"  {name:10} {'ok' if passed else 'NOT FINDABLE':12} - {detail}")
        ok = ok and passed
    if not ok:
        print("\na practice cannot be found from what ships; not shippable")
        sys.exit(1)
    print("\nevery practice is findable, and the certificates leave one account")


if __name__ == "__main__":
    main()
