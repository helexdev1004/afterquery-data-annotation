"""Run the shop first, then write the logs the way five controllers would.

    python make_shop.py [outdir]

Truth first. Every refill and every shot happens in site time; each housing's
drying time is taken from those, and only then is each controller's log
written out in its own way and by its own clock.

Nothing in a log is tied to a refill through a mean. A dryer is refilled on the
run, so there is no stoppage at a refill; a machine's cycle is set and is the
same on any resin; stoppages fall at random; and no two logs begin or end at
the same moment or on any round one. A machine's cycle also drifts a little
over hours with the mould's temperature, and now and then the robot fusses for
a few minutes, so the plain spread of the cycle is mostly that. What a refill
does leave is second order: the more regrind in the blend, the more the cycle
wavers from one shot to the next.
"""

import csv
import datetime as dt
import json
import pathlib
import random
import sys

import dryrules

SEED = 27182
SITE_BEGAN = dt.datetime(2026, 9, 14)
DAYS = 8
HOUSINGS_PER_MACHINE = 8

MACHINES = (
    # machine, dryer, who keeps the controller, its way with a time, behind?
    ("M1", "D1", "Naylor", "sheet", False),
    ("M2", "D2", "Oddy", None, True),
    ("M3", "D3", "Priestley", "cycles", False),
    ("M4", "D4", "Quarmby", "continental", True),
    ("M5", "D5", "Rushworth", "unix", False),
)
WAVER_S = {"virgin": 0.05, "blend 20": 0.08, "blend 40": 0.13}


def book_refills(rng, began, ended):
    refills, now, last = [], began - rng.uniform(1, 6) * 3600, None
    while now < ended:
        minute = int(now // 60) * 60
        kinds = [k for k in dryrules.RESINS if k != last]
        resin = rng.choice(kinds) if last is None or rng.random() < 0.78 \
            else last
        refills.append((float(minute), resin))
        last = resin
        now += rng.uniform(3.0, 8.0) * 3600
    return refills


def run_machine(rng, dryer, began, ended):
    """Shot times in site time."""
    cycle = rng.uniform(34.0, 44.0)
    start = began + rng.uniform(1.2, 9.5) * 3600 + rng.uniform(0, 60)
    stop = ended - rng.uniform(1.2, 9.5) * 3600 - rng.uniform(0, 60)
    drift, fuss, now, shots = 0.0, 0, start, []
    while now < stop:
        _, resin = dryer.drying(now)
        drift = 0.998 * drift + rng.gauss(0, 0.014)
        if fuss:
            fuss -= 1
        elif rng.random() < 1 / 400.0:
            fuss = rng.randrange(8, 26)
        took = cycle + drift + rng.gauss(0, WAVER_S[resin]) \
            + (rng.gauss(0, 0.45) if fuss else 0.0)
        if rng.random() < 1 / 1200.0:
            took += rng.uniform(180, 1500)            # a stoppage
        now += max(took, 0.6 * cycle)
        shots.append(round(now, 2))
    return start, shots


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "yard"
    (outdir / "shots").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    began = dryrules.seconds(SITE_BEGAN)
    ended = began + DAYS * 86400

    shop, housings = {}, []
    for machine, dryer_name, keeper, way, behind in MACHINES:
        dryer = dryrules.Dryer(book_refills(rng, began, ended))
        start, shots = run_machine(rng, dryer, began, ended)
        first_number = rng.randrange(40000, 900000)
        lag = 3600.0 if behind else 0.0
        shop[machine] = dict(dryer_name=dryer_name, keeper=keeper, way=way,
                             behind=behind, dryer=dryer, start=start,
                             shots=shots, first_number=first_number, lag=lag)
        for k, site_time in enumerate(shots):
            hours, resin = dryer.drying(site_time)
            # clear of any refill by a quarter of an hour, on the true clock
            # and on the controller's, so no answer turns on a minute
            clear = min(abs(t - c) for t, _ in dryer.refills
                        for c in (site_time, site_time - lag))
            if clear >= 900 and 0.3 <= hours:
                housings.append(dict(
                    machine=machine, name="%s/%d" % (machine, first_number + k),
                    entry={"hours": round(hours, 2), "resin": resin}))

    def stamp(seconds_since_1970, places=2):
        moment = dryrules.DAY0_UNIX + dt.timedelta(
            seconds=round(seconds_since_1970, places))
        text = moment.strftime("%Y-%m-%d %H:%M:%S.%f")
        return text[:-4]                              # hundredths

    def write(chosen):
        with open(outdir / "machines.csv", "w", newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            out.writerow(["machine", "dryer", "controller_kept_by",
                          "log_began"])
            for machine, m in shop.items():
                out.writerow([machine, m["dryer_name"], m["keeper"],
                              stamp(m["start"] - m["lag"])])
        with open(outdir / "refills.csv", "w", newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            out.writerow(["dryer", "time", "resin"])
            booked = [(t, m["dryer_name"], resin) for m in shop.values()
                      for t, resin in m["dryer"].refills]
            for t, name, resin in sorted(booked):
                out.writerow([name, stamp(t)[:16], resin])
        for machine, m in shop.items():
            with open(outdir / "shots" / (machine + ".csv"), "w",
                      newline="") as handle:
                out = csv.writer(handle, lineterminator="\n")
                out.writerow(["shot", "time"])
                before = m["start"]
                for k, site_time in enumerate(m["shots"]):
                    shown_at = site_time - m["lag"]   # the controller's clock
                    if m["way"] == "unix":
                        text = "%.2f" % shown_at
                    elif m["way"] == "sheet":
                        text = "%.8f" % ((shown_at - dryrules.seconds(
                            dryrules.DAY0_SHEET)) / 86400.0)
                    elif m["way"] == "continental":
                        moment = dryrules.DAY0_UNIX + dt.timedelta(
                            seconds=shown_at)
                        text = moment.strftime("%d.%m.%Y %H:%M:%S,%f")[:-4]
                    elif m["way"] == "cycles":
                        text = "%.2f" % (site_time - before)
                        before = site_time
                    else:
                        text = stamp(shown_at)
                    out.writerow([m["first_number"] + k, text])
        (outdir / "housings.txt").write_text(
            "".join(h + "\n" for h in sorted(chosen)), newline="\n")
        (outdir / "sealed.json").write_text(json.dumps(
            {h["name"]: h["entry"] for h in housings if h["name"] in chosen},
            indent=1, sort_keys=True), newline="\n")

    chosen = set()
    for machine in shop:
        mine = [h["name"] for h in housings if h["machine"] == machine]
        chosen.update(rng.sample(mine, HOUSINGS_PER_MACHINE))
    write(chosen)
    (outdir / "clocks.json").write_text(json.dumps(
        {machine: ("hour_behind" if m["behind"] else "site_time")
         for machine, m in shop.items()}, indent=1), newline="\n")

    import reckon

    sealed = json.loads((outdir / "sealed.json").read_text())
    table = reckon.reckon(outdir)
    adrift = [h for h in sealed if not dryrules.same(table.get(h), sealed[h])]
    print("machines %d  shots %d  refills %d  housings %d"
          % (len(shop), sum(len(m["shots"]) for m in shop.values()),
             sum(len(m["dryer"].refills) for m in shop.values()), len(sealed)))
    if adrift:
        print("FAILED: the reference and the shop disagree on %d" % len(adrift))
        for h in adrift[:5]:
            print("   %s: %s against %s" % (h, table.get(h), sealed[h]))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
