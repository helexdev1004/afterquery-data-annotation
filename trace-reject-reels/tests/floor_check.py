"""Try every reading of the die-cutter's record against the sealed reels.

    python floor_check.py
"""

import itertools
import json
import statistics

import claim

JOB = claim.base()
LINES_THAT_MAY_BE_OUT = 4
WITHIN_UM = 2


def right(said, want):
    return said is not None and said[0] == want[0] \
        and abs(said[1] - want[1]) <= WITHIN_UM


def main():
    sealed = json.loads((JOB / "sealed.json").read_text())
    turner = json.loads((JOB / "turner.json").read_text())
    total, trouble = len(sealed), []
    names = list(claim.BY_THE_RECORD)
    scores = {}
    for combo in itertools.product(*[[claim.BY_THE_RECORD[n],
                                      claim.BY_THE_NOTE[n]] for n in names]):
        got, _ = claim.claim(JOB, dict(zip(names, combo)))
        scores[combo] = sum(right(got.get(t), sealed[t]) for t in sealed)
    record = tuple(claim.BY_THE_RECORD[n] for n in names)
    note = tuple(claim.BY_THE_NOTE[n] for n in names)
    second = max(v for k, v in scores.items() if k != record)
    print("readings: %d" % len(scores))
    print("  %2d  by the record" % scores[record])
    print("  %2d  by the note" % scores[note])
    without = {}
    for i, n in enumerate(names):
        c = list(record)
        c[i] = claim.BY_THE_NOTE[n]
        without[n] = scores[tuple(c)]
        print("  %2d  by the record except %s" % (without[n], n))
    print("  %2d  the best reading that is not the record's" % second)

    got, found = claim.claim(JOB, claim.BY_THE_RECORD)
    calipers, _ = claim.diecutter_record(JOB, claim.BY_THE_RECORD)
    ticket = claim.press_ticket(JOB)
    unturned, least, most_wrong, level_gap = 0, 9.9, 0.0, 0.0
    for pallet, f in sorted(found.items()):
        truly = turner[pallet]["turned"]
        unturned += not truly
        good, bad = f["fit"][truly], f["fit"][not truly]
        least, most_wrong = min(least, good / max(bad, 0.05)), max(most_wrong, bad)
        # the level of the reading, reel by reel, the right way round
        sheets, changes = ticket[pallet]
        c = calipers[pallet] if truly else calipers[pallet][::-1]
        firsts = [first for first, _ in changes] + [sheets + 1]
        means = [statistics.fmean(c[a - 1:b - 1])
                 for a, b in zip(firsts, firsts[1:]) if b - a > 300]
        level_gap = max(level_gap, max(means) - min(means))
        print("  %s  %s  evenness steps at the booked changes by %.2f the "
              "right way round, %.2f the wrong way   [gauge in %s]"
              % (pallet, "turned    " if truly else "NOT TURNED", good, bad,
                 f["gauge"]))
        if f["turned"] != truly:
            trouble.append("the board misreads %s" % pallet)
    if least < 1.8:
        trouble.append("the board's evenness does not settle a pallet")
    print("  reel means of the caliper differ by at most %.1f um on a pallet"
          % level_gap)

    if scores[record] != total:
        trouble.append("the record's reading does not place every reject")
    if second > total - LINES_THAT_MAY_BE_OUT - 1:
        trouble.append("a wrong reading is within the allowance")
    for line in trouble:
        print("TROUBLE: %s" % line)
    if not trouble:
        (JOB / "check.json").write_bytes(json.dumps(dict(
            total=total, may_be_out=LINES_THAT_MAY_BE_OUT, second=second,
            by_the_note=scores[note], without=without, readings=len(scores),
            pallets=len(found), unturned=unturned, least="%.2f" % least,
            most_wrong="%.2f" % most_wrong, level_gap="%.1f" % level_gap,
            sheets=sum(len(v) for v in calipers.values())),
            indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
