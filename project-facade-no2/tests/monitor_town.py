"""Eight weeks of nitrogen dioxide at ten sites, and the analysers' downloads.

    python monitor_town.py [outdir]

The air comes first. Every site breathes the town's weather - dirty still
spells and clean windy ones, lasting hours to days - over its own daily shape
with a morning and an evening rise. On top of that a roadside inlet, a few
metres from the kerb, catches exhaust plumes: every so often a quarter-hour
mean is lifted well above its neighbours. An urban background inlet, set back
in a park or a schoolyard, never sees that; its record moves only as the
weather moves.

Then the downloads. A download is named by its analyser's serial number and the
site list says which analyser stands where. After the autumn service two
analysers went back to each other's cabinets - one at a roadside site, one at a
background site - and the site list was not brought up to date.

The road is a quiet one and the background site is in a busy district, so
their levels are of a kind, and the weather's share of every
background record is sized so that it has the same relative spread as the
roads' have. Only how a quarter-hour stands to its neighbours tells which
inlet made a record, and neither a period mean nor the fall-off adjustment
ever looks at that.
"""

import csv
import datetime
import json
import math
import pathlib
import random
import sys

SEED = 6150283
WEEKS, EVERY_MIN = 8, 15
FIRST = datetime.datetime(2026, 1, 12, 0, 0)
PPB_TO_UG = 1.9125

SITES = (
    # site, name, type, monitor-to-kerb m, facade-to-kerb m, local background, mean at the inlet, analyser truly there, habit
    ("HST", "High Street", "roadside", 2.5, 6.0, 17.4, 44.0, "NX-2081", None),
    ("STN", "Station Road", "roadside", 3.0, 9.5, 16.8, 38.5, "NX-2107", "ppb"),
    ("MLN", "Mill Lane", "roadside", 1.5, 4.0, 14.9, 27.0, "NX-2064", None),
    ("QRD", "Quarry Road", "roadside", 2.0, 11.0, 15.6, 31.5, "NX-2119", "comma"),
    ("BYP", "Bypass East", "roadside", 4.5, 14.0, 13.7, 49.0, "NX-2092", None),
    ("PRK", "Victoria Park", "urban background", "", "", "", 18.5, "NX-2075", None),
    ("SCH", "St Anne's School", "urban background", "", "", "", 23.5, "NX-2130", "milligrams"),
    ("LIB", "Central Library", "urban background", "", "", "", 27.5, "NX-2058", None),
    ("ALT", "Allotments", "urban background", "", "", "", 15.0, "NX-2143", None),
    ("CEM", "Cemetery Lodge", "urban background", "", "", "", 21.0, "NX-2126", None),
)
# what the site list says: one road and one background site carry each other's analysers
LISTED = {"MLN": "NX-2130", "SCH": "NX-2064"}


def town_weather(rng, n):
    slow, out = 0.0, []
    for _ in range(n):
        slow = 0.992 * slow + rng.gauss(0, 0.126)
        out.append(slow)
    return out


def daily_shape(i):
    hour = (i * EVERY_MIN / 60.0) % 24
    return 1.0 + 0.30 * math.exp(-((hour - 8.0) / 1.8) ** 2) \
        + 0.36 * math.exp(-((hour - 17.5) / 2.2) ** 2) - 0.22 * math.exp(-((hour - 3.5) / 2.5) ** 2)


def inlet(rng, kind, mean, weather, spread=None):
    """Quarter-hour means at one inlet, micrograms per cubic metre."""
    n = len(weather)
    own, local = 0.0, []
    for _ in range(n):
        own = 0.97 * own + rng.gauss(0, 0.06)
        local.append(own)
    if kind == "roadside":
        series = []
        for i in range(n):
            base = 0.93 * mean * daily_shape(i) * math.exp(0.40 * weather[i] + local[i])
            plume = rng.expovariate(1.0 / (0.30 * mean)) if rng.random() < 0.22 else 0.0
            series.append(base + plume * daily_shape(i) + rng.gauss(0, 0.035 * mean))
    else:
        gain = 0.42 if spread is None else spread
        series = [mean * daily_shape(i) * math.exp(gain * weather[i] + local[i] - 0.05)
                  + rng.gauss(0, 0.035 * mean) for i in range(n)]
    scale = mean * rng.uniform(0.975, 1.025) / (sum(series) / n)
    return [max(0.3, v * scale) for v in series]


def spread_of(series):
    m = sum(series) / len(series)
    return math.sqrt(sum((v - m) ** 2 for v in series) / len(series))


def facade(monitor_mean, background, monitor_m, facade_m):
    """The fall-off adjustment: a roadside mean carried to the facade."""
    fall = lambda d: -0.5476 * math.log(d) + 2.7171
    return (monitor_mean - background) / fall(monitor_m) * fall(facade_m) + background


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "town"
    (outdir / "downloads").mkdir(parents=True, exist_ok=True)
    for old in (outdir / "downloads").glob("*.csv"):
        old.unlink()
    rng = random.Random(SEED)
    n = WEEKS * 7 * 24 * 60 // EVERY_MIN
    weather = town_weather(rng, n)
    air = {}
    for site, _, kind, _, _, _, mean, _, _ in SITES:
        if kind == "roadside":
            air[site] = inlet(rng, kind, mean, weather)
    # every background record is given the relative spread of the roads', so that a
    # summary of a download says nothing of the inlet that made it
    road_cv = [spread_of(air[s]) / (sum(air[s]) / n) for s in air]
    for site, _, kind, _, _, _, mean, _, _ in SITES:
        if kind != "roadside":
            want = sum(road_cv) / len(road_cv) * rng.uniform(0.94, 1.06)
            low, high = 0.05, 3.0
            state = rng.getstate()
            for _ in range(30):
                mid = (low + high) / 2.0
                rng.setstate(state)
                trial = inlet(rng, kind, mean, weather, mid)
                cv = spread_of(trial) / (sum(trial) / n)
                low, high = (mid, high) if cv < want else (low, mid)
            air[site] = trial

    sealed, cabinets = {}, {}
    for site, name, kind, monitor_m, facade_m, background, _, analyser, habit in SITES:
        logged = [round(v, 1) for v in air[site]]
        keep = []
        with open(outdir / "downloads" / (analyser + ".csv"), "w", newline="") as handle:
            out = csv.writer(handle, delimiter=";" if habit == "comma" else ",",
                             lineterminator="\n")
            head = {"ppb": "no2_ppb", "milligrams": "no2_mg_m3"}.get(habit, "no2_ug_m3")
            out.writerow(["timestamp", head, "status"])
            for i, v in enumerate(logged):
                stamp = FIRST + datetime.timedelta(minutes=i * EVERY_MIN)
                status = "ok"
                if stamp.hour == 1 and stamp.minute in (0, 15) and stamp.weekday() == 2:
                    status, shown = "cal", round(rng.uniform(190, 205), 1)
                elif rng.random() < 0.004:
                    status, shown = "fault", -999.0
                else:
                    shown = v
                if habit == "ppb":
                    shown = round(shown / PPB_TO_UG, 2) if status == "ok" else shown
                    text = "%.2f" % shown
                elif habit == "milligrams":
                    text = "%.4f" % (shown / 1000.0) if status == "ok" else "%.1f" % shown
                else:
                    text = "%.1f" % shown
                if habit == "comma":
                    text = text.replace(".", ",")
                if status == "ok":
                    keep.append(shown * PPB_TO_UG if habit == "ppb" else v)
                out.writerow([stamp.strftime("%Y-%m-%d %H:%M"), text, status])
        mean = sum(keep) / len(keep)
        at_facade = mean if kind != "roadside" else facade(mean, background, monitor_m, facade_m)
        sealed[site] = dict(monitor_mean=round(mean, 3), facade_mean=round(at_facade, 3))
        cabinets[analyser] = dict(stands_at=site, type=kind, habit=habit,
                                  listed_at=[s for s, a in (
                                      (x[0], LISTED.get(x[0], x[7])) for x in SITES)
                                      if a == analyser][0])

    with open(outdir / "sites.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["site", "name", "type", "monitor_to_kerb_m", "facade_to_kerb_m",
                      "local_background_ug_m3", "analyser"])
        for s in SITES:
            out.writerow([s[0], s[1], s[2], s[3], s[4], s[5], LISTED.get(s[0], s[7])])
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "cabinets.json").write_bytes(json.dumps(cabinets, indent=1).encode())
    print("sites %d  rows each %d" % (len(SITES), n))


if __name__ == "__main__":
    main()
