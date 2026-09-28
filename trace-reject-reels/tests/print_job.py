"""Print the job, stack it, die-cut it, and write down what each machine kept.

    python print_job.py [outdir]

The press comes first: it sheets one reel of board after another onto six
pallets and books the sheet count at every reel change. Every sheet therefore
has a reel. Then each pallet goes to the die-cutter, which feeds from the top
of whatever stack it is given. A pallet that went through the turner feeds its
first-printed sheet first, as the pressroom's note says; two pallets did not go
through it, and fed last-printed first. The rejects' reels are read off the
press's side of that.

All the board is one grade to one caliper, so nothing about a reel shows in the
level of the die-cutter's caliper reading: the level wanders with the room for
the whole job and hiccups when the feeder does. What differs from reel to reel
is how even the board is, sheet to sheet, and that is the only trace a reel
leaves in the die-cutter's record.
"""

import csv
import json
import pathlib
import random
import sys

SEED = 2236067
CALIPER_UM = 412.0
EVENNESS_UM = (1.2, 2.8, 6.0)             # sheet to sheet, by reel
REJECTS_EACH = 7

PALLETS = (
    # pallet, went through the turner, how the die-cutter's gauge was set
    ("P1", True, "um"), ("P2", True, "thou"), ("P3", False, "um"),
    ("P4", True, "tenths"), ("P5", False, "mm"), ("P6", True, "um"),
)


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "job"
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    # the press: reels run on from pallet to pallet, so a pallet's first and
    # last reels are part-reels of any length and its two ends look alike
    reel_no, left, kind = 300, 0, None
    ticket, record, sealed, turned = [], [], {}, {}
    drift, hiccup = 0.0, 0
    for pallet, was_turned, gauge in PALLETS:
        sheets = rng.randrange(8000, 11000)
        reel_of, booked = [], []
        for count in range(1, sheets + 1):
            if left == 0:
                reel_no += rng.randrange(1, 4)
                left = rng.randrange(1700, 3600)
                kind = rng.choice([k for k in range(3) if k != kind])
                if count > 1:
                    booked.append((count, "R%03d" % reel_no))
            if count == 1:
                booked.append((1, "R%03d" % reel_no))
            reel_of.append(("R%03d" % reel_no, kind))
            left -= 1
        ticket.append((pallet, sheets, booked))

        order = range(sheets) if was_turned else range(sheets - 1, -1, -1)
        lines = []
        for fed, press_index in enumerate(order, 1):
            reel, evenness = reel_of[press_index]
            drift = 0.9995 * drift + rng.gauss(0, 0.11)
            if hiccup:
                hiccup -= 1
            elif rng.random() < 1 / 1400.0:
                hiccup = rng.randrange(8, 40)
            um = CALIPER_UM + drift + rng.gauss(0, EVENNESS_UM[evenness]) \
                + (rng.gauss(0, 5.0) if hiccup else 0.0)
            um = round(um)
            shown = {"um": "%d" % um, "thou": "%.2f" % (um / 25.4),
                     "mm": "%.3f" % (um / 1000.0),
                     "tenths": "%d" % (um * 10)}[gauge]
            lines.append((pallet, fed, shown, fed, reel, um))
        record += lines
        # rejects whose reel the unturned reading would really get wrong
        def other_end(fed):
            return reel_of[fed - 1][0] if not was_turned else None
        pool = [l for l in lines if 300 < l[3] < sheets - 300
                and (was_turned or other_end(l[3]) != l[4])]
        for l in sorted(rng.sample(pool, REJECTS_EACH), key=lambda l: l[3]):
            sealed["%s-%05d" % (pallet, l[1])] = [l[4], l[5]]
        turned[pallet] = dict(turned=was_turned, gauge=gauge)

    with open(outdir / "diecutter.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["pallet", "sheet", "caliper"])
        out.writerows(l[:3] for l in record)
    with open(outdir / "press_ticket.txt", "w", newline="\n") as handle:
        handle.write("JOB 58114  folding carton, 400 gsm board, one grade\n\n")
        for pallet, sheets, booked in ticket:
            handle.write("pallet %s  %d sheets\n" % (pallet, sheets))
            for count, reel in booked:
                handle.write("    reel %s from sheet %d\n" % (reel, count))
            handle.write("\n")
    (outdir / "rejects.txt").write_bytes(
        "".join(t + "\n" for t in sorted(sealed)).encode())
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "turner.json").write_bytes(json.dumps(turned, indent=1).encode())
    print("pallets %d  sheets %d  rejects %d"
          % (len(PALLETS), len(record), len(sealed)))


if __name__ == "__main__":
    main()
