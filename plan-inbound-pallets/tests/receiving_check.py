"""Every reading of the suppliers' notices, against the sealed plan.

    python receiving_check.py
"""

import itertools
import json
import statistics

import dock_plan

DOCK = dock_plan.base()
LINES_THAT_MAY_BE_WRONG = 4


def right(said, want):
    return said is not None and said[0] == want[0] and said[2] == want[2] \
        and abs(said[1] - want[1]) <= 0.5 + 1e-9


def main():
    sealed = json.loads((DOCK / "sealed.json").read_text())
    mapping = json.loads((DOCK / "mapping.json").read_text())
    total, trouble = len(sealed), []
    names = list(dock_plan.THE_NOTICES)
    scores = {}
    for combo in itertools.product(*[[dock_plan.THE_NOTICES[n],
                                      dock_plan.THE_NOTE[n]] for n in names]):
        got, _ = dock_plan.plan(DOCK, dict(zip(names, combo)))
        scores[combo] = sum(right(got.get(a), sealed[a]) for a in sealed)
    notices = tuple(dock_plan.THE_NOTICES[n] for n in names)
    note = tuple(dock_plan.THE_NOTE[n] for n in names)
    second = max(v for k, v in scores.items() if k != notices)
    print("readings: %d" % len(scores))
    print("  %2d  by the notices" % scores[notices])
    print("  %2d  by the note" % scores[note])
    without = {}
    for i, n in enumerate(names):
        c = list(notices)
        c[i] = dock_plan.THE_NOTE[n]
        without[n] = scores[tuple(c)]
        print("  %2d  by the notices except %s" % (without[n], n))
    print("  %2d  the best reading that is not the notices'" % second)

    got, seen = dock_plan.plan(DOCK, dock_plan.THE_NOTICES)
    naive, _ = dock_plan.plan(DOCK, dict(dock_plan.THE_NOTICES,
                                         quantity="single_units"))
    master = dock_plan.item_master(DOCK)
    in_packs, least_whole, most_part = 0, 1.0, 0.0
    middles = {}
    for supplier, s in sorted(seen.items()):
        truly = mapping[supplier]["sends_inners"]
        in_packs += truly
        if truly:
            most_part = max(most_part, s["share"])
        else:
            least_whole = min(least_whole, s["share"])
        rows, _ = dock_plan.read_notices(DOCK / "asn" / (supplier + ".csv"),
                                         dock_plan.THE_NOTICES)
        middles[supplier] = statistics.median(q for _, _, q in rows)
        print("  %s  whole inner packs on %.2f of lines; middle quantity on a "
              "line %4d   [%s]%s"
              % (supplier, s["share"], middles[supplier],
                 ", ".join(s["habits"]) or "plain",
                 "  SENDS INNER PACKS" if truly else ""))
        if s["in_packs"] != truly:
            trouble.append("the packs misread %s" % supplier)
    if least_whole < 0.999 or most_part > 0.6:
        trouble.append("whole packs do not settle a supplier")
    honest = [m for s, m in middles.items() if not mapping[s]["sends_inners"]]
    for s, m in middles.items():
        if mapping[s]["sends_inners"] and not min(honest) <= m <= max(honest):
            trouble.append("%s's quantities are of a size no unit sender's are"
                           % s)
    # the plan read as single units must still look like a plan
    sizes = sorted(v[2] for a, v in naive.items())
    true_sizes = sorted(v[2] for v in got.values())
    print("  pallets on a notice: %d to %d truly, %d to %d with every notice "
          "read as single units" % (true_sizes[0], true_sizes[-1], sizes[0],
                                    sizes[-1]))

    if scores[notices] != total:
        trouble.append("the notices' reading does not get every line")
    if second > total - LINES_THAT_MAY_BE_WRONG - 1:
        trouble.append("a wrong reading is within the allowance")
    for line in sorted(set(trouble)):
        print("TROUBLE: %s" % line)
    if not trouble:
        (DOCK / "check.json").write_bytes(json.dumps(dict(
            total=total, may_be_wrong=LINES_THAT_MAY_BE_WRONG, second=second,
            by_note=scores[note], without=without, readings=len(scores),
            suppliers=len(seen), in_packs=in_packs,
            least_whole="%.2f" % least_whole, most_part="%.2f" % most_part,
            items=len(master)), indent=1).encode())
    return 1 if trouble else 0


if __name__ == "__main__":
    raise SystemExit(main())
