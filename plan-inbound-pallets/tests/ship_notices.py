"""Six suppliers ship to the centre for a week; then their notices are written.

    python ship_notices.py [outdir]

The goods come first: every line of every delivery is so many sealed inner
packs of one item, and the cartons, weight and pallet positions of a delivery
follow from the centre's item master. The advance shipping notices are written
afterwards by each supplier's own system. The centre's note says a notice gives
single units. Two suppliers' systems were mapped to the wrong field when they
were connected, and send the count of inner packs instead.

Nothing about the size of a number says which: suppliers differ in scale by
more than a pack size does, and the two in question are the big ones, so their
inner-pack counts look like other suppliers' unit counts. What a true unit
count cannot avoid is being a whole number of inner packs, item by item.
"""

import csv
import json
import math
import pathlib
import random
import sys

SEED = 3605551
PLAN_EACH = 7

SUPPLIERS = (
    # code, inner packs on a typical line, notice habit, sends inner packs
    ("S1", 14, None, False), ("S2", 40, "sku", False),
    ("S3", 150, None, True), ("S4", 120, "semicolon", True),
    ("S5", 22, None, False), ("S6", 260, "thousands", False),
)


def check_digit(sku):
    return sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(sku)) % 10


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "dock"
    (outdir / "asn").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    master, sealed, mapping = [], {}, {}
    sku_no = 104000

    for code, scale, habit, sends_inners in SUPPLIERS:
        items = []
        for _ in range(rng.randrange(60, 90)):
            sku_no += rng.randrange(3, 40)
            upi = rng.choice((2, 3, 4, 5, 6, 8, 10, 12))
            ipc = rng.choice((4, 6, 8, 10, 12, 20))
            items.append(dict(
                sku="%06d" % sku_no, supplier=code, units_per_inner=upi,
                inners_per_carton=ipc,
                inner_kg=round(rng.uniform(0.25, 4.5), 3),
                carton_tare_kg=round(rng.uniform(0.2, 0.9), 2),
                cartons_per_pallet=rng.choice((24, 30, 36, 40, 48, 60, 72))))
        master += items

        notices, rows = [], []
        for n in range(rng.randrange(55, 75)):
            asn = "%s-%05d" % (code, 40000 + rng.randrange(1, 9) + 11 * n)
            cartons, kilos, positions = 0, 0.0, 0.0
            lines = rng.sample(items, rng.randrange(4, 22))
            for k, item in enumerate(lines, 1):
                if rng.random() < 0.55:            # whole cartons, as a rule
                    inners = item["inners_per_carton"] * max(1, round(
                        rng.lognormvariate(math.log(scale), 0.7)
                        / item["inners_per_carton"]))
                else:
                    inners = max(1, round(rng.lognormvariate(
                        math.log(scale), 0.7)))
                line_cartons = math.ceil(inners / item["inners_per_carton"])
                cartons += line_cartons
                kilos += inners * item["inner_kg"] \
                    + line_cartons * item["carton_tare_kg"]
                positions += line_cartons / item["cartons_per_pallet"]
                sent = inners if sends_inners \
                    else inners * item["units_per_inner"]
                rows.append((asn, k, item["sku"], sent))
            notices.append((asn, cartons, round(kilos, 1),
                            math.ceil(positions - 1e-9)))

        with open(outdir / "asn" / (code + ".csv"), "w", newline="") as handle:
            out = csv.writer(handle, lineterminator="\n",
                             delimiter=";" if habit == "semicolon" else ",")
            out.writerow(["asn", "line", "sku", "quantity"])
            for asn, k, sku, sent in rows:
                if habit == "sku":
                    sku = "0%s-%d" % (sku, check_digit(sku))
                shown = str(sent)
                if habit == "thousands":
                    shown = "{:,}".format(sent)
                elif habit == "semicolon":
                    shown = "%d,00" % sent
                out.writerow([asn, k, sku, shown])
        for asn, cartons, kilos, positions in rng.sample(notices, PLAN_EACH):
            sealed[asn] = [cartons, kilos, positions]
        mapping[code] = dict(sends_inners=sends_inners, habit=habit)

    with open(outdir / "item_master.csv", "w", newline="") as handle:
        out = csv.DictWriter(handle, lineterminator="\n",
                             fieldnames=list(master[0]))
        out.writeheader()
        out.writerows(master)
    (outdir / "to_plan.txt").write_bytes(
        "".join(a + "\n" for a in sorted(sealed)).encode())
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "mapping.json").write_bytes(json.dumps(mapping, indent=1).encode())
    print("suppliers %d  items %d  notices to plan %d"
          % (len(SUPPLIERS), len(master), len(sealed)))


if __name__ == "__main__":
    main()
