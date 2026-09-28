"""Cartons, gross weight and pallet positions for the notices to be planned.

    python dock_plan.py [folder]        writes folder/inbound_plan.csv

`plan(folder, reading)` does the work; `reading` says, for each thing a
supplier's notices can do differently from the centre's note, which to trust.
"""

import csv
import math
import pathlib
import sys

THE_NOTICES = {"sku": "strip_to_the_master", "thousands": "drop_the_commas",
               "semicolon": "comma_is_decimal", "quantity": "ask_the_packs"}
THE_NOTE = {"sku": "as_written", "thousands": "up_to_the_comma",
            "semicolon": "drop_the_comma", "quantity": "single_units"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "dock"


def item_master(folder):
    with open(folder / "item_master.csv", newline="") as handle:
        return {r["sku"]: r for r in csv.DictReader(handle)}


def read_notices(path, reading):
    """[(asn, sku, quantity)] and the habits met in this supplier's file."""
    text = path.read_text()
    habits = set()
    delimiter = ";" if ";" in text.splitlines()[0] else ","
    rows = []
    for r in csv.DictReader(text.splitlines(), delimiter=delimiter):
        sku, shown = r["sku"], r["quantity"]
        if "-" in sku:
            habits.add("sku")
            if reading["sku"] == "strip_to_the_master":
                sku = sku.split("-")[0].lstrip("0").zfill(6)
        if delimiter == ";":
            habits.add("semicolon")
            whole, _, cents = shown.partition(",")
            quantity = int(whole) if reading["semicolon"] == "comma_is_decimal" \
                else int(whole + cents)
        elif "," in shown:
            habits.add("thousands")
            quantity = int(shown.replace(",", "")) \
                if reading["thousands"] == "drop_the_commas" \
                else int(shown.split(",")[0])
        else:
            quantity = int(shown)
        rows.append((r["asn"], sku, quantity))
    return rows, sorted(habits)


def whole_packs_share(rows, master):
    """Of a supplier's lines, the share whose quantity is a whole number of the
    item's inner packs."""
    known = [(q, int(master[s]["units_per_inner"])) for _, s, q in rows
             if s in master]
    return sum(q % upi == 0 for q, upi in known) / max(1, len(known))


def plan(folder, reading):
    """{asn: (cartons, gross_kg, pallets)} for the notices to plan, and what
    each supplier's file showed."""
    folder = pathlib.Path(folder)
    master = item_master(folder)
    wanted = set((folder / "to_plan.txt").read_text().split())
    out, seen = {}, {}
    for path in sorted((folder / "asn").glob("*.csv")):
        rows, habits = read_notices(path, reading)
        share = whole_packs_share(rows, master)
        in_packs = reading["quantity"] == "ask_the_packs" and share < 0.9
        seen[path.stem] = dict(habits=habits, share=share, in_packs=in_packs)
        totals = {}
        for asn, sku, quantity in rows:
            if asn not in wanted or sku not in master:
                continue
            item = master[sku]
            inners = quantity if in_packs \
                else quantity / int(item["units_per_inner"])
            cartons = math.ceil(inners / int(item["inners_per_carton"]) - 1e-9)
            t = totals.setdefault(asn, [0, 0.0, 0.0])
            t[0] += cartons
            t[1] += inners * float(item["inner_kg"]) \
                + cartons * float(item["carton_tare_kg"])
            t[2] += cartons / int(item["cartons_per_pallet"])
        for asn, (cartons, kilos, positions) in totals.items():
            out[asn] = (cartons, round(kilos, 1), math.ceil(positions - 1e-9))
    return out, seen


if __name__ == "__main__":
    where = base()
    answer, _ = plan(where, THE_NOTICES)
    with open(where / "inbound_plan.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["asn", "cartons", "gross_kg", "pallets"])
        for asn in sorted(answer):
            sheet.writerow([asn, answer[asn][0], "%.1f" % answer[asn][1],
                            answer[asn][2]])
    print("%d notices planned" % len(answer))
