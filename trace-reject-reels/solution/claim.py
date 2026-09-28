"""Tie each rejected sheet to its reel of board.

    python claim.py [folder]        writes folder/reject_reels.csv

`claim(folder, reading)` does it. `reading` holds, for every point on which
the die-cutter's record can part company with the pressroom's note, the side
to be believed.
"""

import csv
import math
import pathlib
import re
import statistics
import sys

EITHER_SIDE = 400          # sheets compared across a booked reel change

BY_THE_RECORD = {"thou": "to_um", "mm": "to_um", "tenths": "to_um",
                 "turner": "ask_the_board"}
BY_THE_NOTE = {"thou": "as_um", "mm": "as_um", "tenths": "as_um",
               "turner": "every_pallet_turned"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "job"


def press_ticket(folder):
    """{pallet: (sheets, [(first sheet, reel)])} from the press's job ticket."""
    out, pallet = {}, None
    for line in (folder / "press_ticket.txt").read_text().splitlines():
        head = re.match(r"pallet (\S+)\s+(\d+) sheets", line)
        change = re.match(r"\s+reel (\S+) from sheet (\d+)", line)
        if head:
            pallet = head.group(1)
            out[pallet] = (int(head.group(2)), [])
        elif change:
            out[pallet][1].append((int(change.group(2)), change.group(1)))
    return out


def diecutter_record(folder, reading):
    """{pallet: [caliper in um, in the order fed]} and each pallet's gauge."""
    raw = {}
    with open(folder / "diecutter.csv", newline="") as handle:
        for row in csv.DictReader(handle):
            raw.setdefault(row["pallet"], []).append(float(row["caliper"]))
    calipers, gauges = {}, {}
    for pallet, values in raw.items():
        middle = statistics.median(values)
        gauge, factor = "um", 1.0
        if middle < 5:
            gauge, factor = "mm", 1000.0
        elif middle < 100:
            gauge, factor = "thou", 25.4
        elif middle > 2000:
            gauge, factor = "tenths", 0.1
        if gauge != "um" and reading[gauge] != "to_um":
            factor = 1.0
        calipers[pallet], gauges[pallet] = [v * factor for v in values], gauge
    return calipers, gauges


def unevenness(calipers):
    c = calipers
    return [0.0] + [abs(c[i] - (c[i - 1] + c[i + 1]) / 2.0)
                    for i in range(1, len(c) - 1)] + [0.0]


def steps_at_changes(uneven, changes, sheets, turned):
    """How sharply the board's evenness changes at the booked reel changes,
    if the pallet was fed the way `turned` says."""
    total = 0.0
    for first_sheet, _ in changes[1:]:
        at = first_sheet - 1 if turned else sheets - first_sheet + 1
        before = uneven[max(0, at - EITHER_SIDE):at]
        after = uneven[at:at + EITHER_SIDE]
        if len(before) > 50 and len(after) > 50:
            total += abs(math.log(max(statistics.median(after), 0.1)
                                  / max(statistics.median(before), 0.1)))
    return total / max(1, len(changes) - 1)


def claim(folder, reading):
    """{reject: (reel, caliper_um)} and what was found about each pallet."""
    folder = pathlib.Path(folder)
    ticket = press_ticket(folder)
    calipers, gauges = diecutter_record(folder, reading)
    found = {}
    for pallet, (sheets, changes) in ticket.items():
        uneven = unevenness(calipers[pallet])
        fit = {way: steps_at_changes(uneven, changes, sheets, way)
               for way in (True, False)}
        turned = fit[True] >= fit[False] \
            if reading["turner"] == "ask_the_board" else True
        found[pallet] = dict(gauge=gauges[pallet], turned=turned, fit=fit)
    out = {}
    for tag in (folder / "rejects.txt").read_text().split():
        pallet, fed = tag.split("-")[0], int(tag.split("-")[1])
        sheets, changes = ticket[pallet]
        printed = fed if found[pallet]["turned"] else sheets - fed + 1
        reel = [r for first, r in changes if first <= printed][-1]
        out[tag] = (reel, round(calipers[pallet][fed - 1]))
    return out, found


if __name__ == "__main__":
    where = base()
    answer, _ = claim(where, BY_THE_RECORD)
    with open(where / "reject_reels.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["reject", "reel", "caliper_um"])
        for tag in sorted(answer):
            sheet.writerow([tag, answer[tag][0], answer[tag][1]])
    print("%d rejects placed" % len(answer))
