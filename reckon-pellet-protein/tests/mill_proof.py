"""Put every short cut to the test against the sealed figures.

    python mill_proof.py
"""

import itertools
import json
import statistics

import expected
import millrules

YARD = expected.base()
SAMPLES_THAT_MAY_BE_OUT = 4


def good(said, want):
    return said is not None and said[0] == want[0] \
        and abs(said[1] - want[1]) <= millrules.PROTEIN_WITHIN + 1e-9


def main():
    sealed = json.loads((YARD / "sealed.json").read_text())
    total, trouble = len(sealed), []
    names = list(expected.IN_FACT)
    grid = [[expected.IN_FACT[n], expected.ON_PAPER[n]] for n in names]
    scores = {}
    for combo in itertools.product(*grid):
        got = expected.expected(YARD, dict(zip(names, combo)))
        scores[combo] = sum(1 for k in sealed if good(got.get(k), sealed[k]))
    fact = tuple(expected.IN_FACT[n] for n in names)
    paper = tuple(expected.ON_PAPER[n] for n in names)
    second = max(v for k, v in scores.items() if k != fact)
    print("readings: %d" % len(scores))
    print("  %2d  in fact" % scores[fact])
    print("  %2d  on paper" % scores[paper])
    without = {}
    for i, n in enumerate(names):
        c = list(fact)
        c[i] = expected.ON_PAPER[n]
        without[n] = scores[tuple(c)]
        print("  %2d  in fact except %s" % (without[n], n))
    print("  %2d  the best reading that is not the fact" % second)

    answers = [tuple(v) for v in sealed.values()]
    same = max(answers.count(a) for a in answers)
    print("  %2d  one formula given for every sample" % same)

    presses, bins, protein, samples = expected.read_mill(YARD, expected.IN_FACT)
    plumbing = json.loads((YARD / "plumbing.json").read_text())
    least, most_other, crossed = None, 0.0, 0
    for name, p in sorted(presses.items()):
        real = plumbing[name]
        other = max(v for b, v in p["steps"].items() if b != real)
        least = p["steps"][real] if least is None else min(least,
                                                           p["steps"][real])
        most_other = max(most_other, other)
        crossed += real != p["tabled"]
        print("  %s  steadiness steps at the changes of the bin it draws from "
              "(%s) by %.2f, at any other bin's by at most %.2f   [%s]"
              % (name, real, p["steps"][real], other,
                 ", ".join(p["log"].ways) or "logged as the note says"))
        if p["fed_by"] != real:
            trouble.append("the press log misreads %s" % name)
    if least < 0.6 or most_other > 0.4:
        trouble.append("a press's steadiness does not settle its bin")

    # no mean may say it: the pressing rate by formula texture is the feeder's
    gap = 0.0
    for name, p in presses.items():
        log = p["log"]
        steps = [(t, b - a) for t, a, b in zip(log.times[1:], log.tonnes,
                                               log.tonnes[1:])]
        usual = statistics.median(s for _, s in steps)
        for b, changes in bins.items():
            by_formula = {}
            for t, s in steps:
                if s > 0.5 * usual:
                    f = millrules.formula_in(changes, t)
                    by_formula.setdefault(f, []).append(s)
            means = [statistics.fmean(v) for v in by_formula.values()
                     if len(v) > 200]
            gap = max(gap, (max(means) - min(means)) / usual)
    print("  mean pressing rate differs between formulas by at most %.1f in a "
          "hundred, whichever bin a press is set against" % (100 * gap))

    if scores[fact] != total:
        trouble.append("the facts do not get every sample")
    if second > total - SAMPLES_THAT_MAY_BE_OUT - 1:
        trouble.append("a wrong reading is within the allowance")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (YARD / "proof.json").write_text(json.dumps(dict(
            total=total, may_be_out=SAMPLES_THAT_MAY_BE_OUT, second=second,
            on_paper=scores[paper], without=without, same=same,
            readings=len(scores), crossed=crossed, presses=len(presses),
            least="%.2f" % least, most_other="%.2f" % most_other,
            rate_gap="%.1f" % (100 * gap),
            lines=sum(len(p["log"].times) for p in presses.values()),
            changes=sum(len(c) for c in bins.values()),
            formulas=len(protein)), indent=1))
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
