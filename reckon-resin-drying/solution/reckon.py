"""Reckon the forty drying times from the shipped records alone.

Nothing here looks at the sealed table. `AS_IT_IS` is how the records have to
be read; proof.py scores every other way of reading them.

Four of the five controllers do not log a shot's time the way the procedure
says: one writes seconds since 1970, one a spreadsheet's day numbers, one the
continental way with a decimal comma, and one writes no time at all, only how
long each shot took, to be counted on from the time its log began. Each shows
at once and each is only a way of writing a time.

The fifth thing is not like those. The procedure says controllers keep site
time, as the planning system does. Two controllers are an hour behind it.
Nothing says which and nothing breaks: every shot still falls after some
refill and gets a drying time, an hour short. No mean says it either - a
machine's cycle is set, and is the same on any resin. What says it is how
steadily the machine cycles. Regrind plasticises unevenly, so from one shot to
the next the cycle wavers more the more regrind is in the blend, and the waver
steps up or down where a refill changes the blend. Read on the right clock the
steps fall at the refills.
"""

import bisect
import csv
import json
import pathlib

import dryrules

AS_IT_IS = {"unix": "decode", "sheet": "decode", "continental": "decode",
            "cycles": "count_on", "clock": "ask_the_cycle"}
AS_WRITTEN = {"unix": "leave", "sheet": "leave", "continental": "leave",
              "cycles": "leave", "clock": "site_time"}
OTHER_CLOCKS = ("hour_behind", "hour_ahead")
HOUR = 3600.0
WINDOW_S = 40 * 60


def read_csv(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def records_dir():
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    return yard if (yard / "sealed.json").is_file() else pathlib.Path("/app")


def shot_times(rows, log_began, reading):
    """(how the controller writes a time, the times in seconds since 1970 by
    the controller's own clock - or None if they are left as written and mean
    nothing)."""
    first = rows[0]["time"]
    if "-" in first and ":" in first:
        return None, [dryrules.iso(r["time"]) for r in rows]
    if "," in first or first.count(".") == 3:
        way, decode = "continental", dryrules.continental
    elif float(first) < 1e3:
        way, decode = "cycles", None
    elif float(first) < 1e6:
        way, decode = "sheet", dryrules.sheet_day
    else:
        way, decode = "unix", float
    if reading[way] == "leave":
        return way, None
    if way == "cycles":
        # the first shot ends one cycle after the log began
        now, times = dryrules.iso(log_began), []
        for r in rows:
            now += float(r["time"])
            times.append(now)
        return way, times
    return way, [decode(r["time"]) for r in rows]


def waver(times):
    """(when, how far a cycle stands from the mean of the cycles either side of
    it) for every shot in a run of three clean cycles."""
    cycles = [b - a for a, b in zip(times, times[1:])]
    usual = sorted(cycles)[len(cycles) // 2]
    out = []
    for k in range(1, len(cycles) - 1):
        trio = cycles[k - 1:k + 2]
        if max(trio) < 1.5 * usual:                 # no stoppage among them
            out.append((times[k + 1], abs(trio[1] - (trio[0] + trio[2]) / 2)))
    return out


def steps_at_refills(wavering, dryer, behind_s):
    """How much the waver steps the way the blend says it should at the
    refills that change the blend, if the controller is `behind_s` seconds
    behind site time; in units of the log's usual waver."""
    when = [w for w, _ in wavering]
    usual = sorted(v for _, v in wavering)[len(wavering) // 2] or 1e-9
    total, counted = 0.0, 0
    for (t0, old), (t1, new), nxt in zip(dryer.refills, dryer.refills[1:],
                                         dryer.refills[2:] + [(None, None)]):
        if old == new:
            continue
        at = t1 - behind_s                          # by the controller's clock
        lo = max(at - WINDOW_S, t0 - behind_s)
        hi = at + WINDOW_S if nxt[0] is None \
            else min(at + WINDOW_S, nxt[0] - behind_s)
        before = sorted(v for _, v in wavering[bisect.bisect_left(when, lo):
                                                bisect.bisect_left(when, at)])
        after = sorted(v for _, v in wavering[bisect.bisect_left(when, at):
                                               bisect.bisect_left(when, hi)])
        if len(before) < 15 or len(after) < 15:
            continue
        rise = after[len(after) // 2] - before[len(before) // 2]
        if dryrules.RESINS.index(new) < dryrules.RESINS.index(old):
            rise = -rise
        total += rise / usual
        counted += 1
    return total / counted if counted else 0.0


def read_shop(app, reading):
    app = pathlib.Path(app)
    refills = {}
    for r in read_csv(app / "refills.csv"):
        refills.setdefault(r["dryer"], []).append(
            (dryrules.iso(r["time"]), r["resin"]))
    shop = {}
    for m in read_csv(app / "machines.csv"):
        rows = read_csv(app / "shots" / (m["machine"] + ".csv"))
        way, times = shot_times(rows, m["log_began"], reading)
        dryer = dryrules.Dryer(refills[m["dryer"]])
        entry = {"way": way, "dryer": dryer, "steps": {}, "behind_s": 0.0,
                 "times": None}
        if times is not None:
            entry["times"] = dict(zip((r["shot"] for r in rows), times))
            wavering = waver(times)
            for name, behind in (("site_time", 0.0), ("hour_behind", HOUR),
                                 ("hour_ahead", -HOUR)):
                entry["steps"][name] = steps_at_refills(wavering, dryer,
                                                        behind)
            best = max(entry["steps"], key=entry["steps"].get) \
                if reading["clock"] == "ask_the_cycle" else reading["clock"]
            entry["clock"] = best
            entry["behind_s"] = {"site_time": 0.0, "hour_behind": HOUR,
                                 "hour_ahead": -HOUR}[best]
        shop[m["machine"]] = entry
    return shop


def reckon(app, reading=None):
    app = pathlib.Path(app)
    shop = read_shop(app, reading or AS_IT_IS)
    table = {}
    for housing in (app / "housings.txt").read_text().split():
        machine, shot = housing.split("/")
        entry = shop[machine]
        if entry["times"] is None:
            continue
        found = entry["dryer"].drying(entry["times"][shot] + entry["behind_s"])
        if found:
            table[housing] = {"hours": round(found[0], 2), "resin": found[1]}
    return table


if __name__ == "__main__":
    import sys

    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else records_dir()
    (target / "drying_times.json").write_text(
        json.dumps(reckon(target), indent=1, sort_keys=True) + "\n")
