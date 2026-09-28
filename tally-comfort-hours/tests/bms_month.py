"""Let a building run for five weeks, then write what the managing agent holds.

    python bms_month.py [outdir]

The month comes first. Each of ten zones has a sensor on its wall, a tenant who
keeps the hours in the lease, and plant that holds it near setpoint round the
clock and now and then fails to. The out-of-band hours are counted from the
sensor that is really in the zone. Then the trends are written, each in its
own outstation's way of writing a temperature or a time, and the point list is
written as the office believes it - which for two pairs of zones is crossed,
each of the pair trended under the other's name since a controls refit.

The plant runs day and night to one setpoint, so a zone is no warmer or cooler
for being occupied, and its slips out of band come when the plant slips, not
when the tenant does. What occupation does is second order: doors, people and
blinds make the reading restless from one two minutes to the next, in the hours
the tenant really keeps.
"""

import csv
import json
import pathlib
import random
import sys
from datetime import datetime, timedelta

SEED = 1732050
MONTH_BEGINS = datetime(2026, 11, 2)            # a Monday
WEEKS = 5
EVERY_MIN = 2
BAND = (20.0, 24.0)

TENANTS = (
    # zone, tenant, days kept (0 = Monday), from, to
    ("Z01", "solicitors", range(0, 5), "08:30", "18:00"),
    ("Z02", "gym", range(0, 7), "06:00", "22:00"),
    ("Z03", "dental practice", range(0, 6), "08:00", "17:00"),
    ("Z04", "cinema", range(0, 7), "13:00", "23:30"),
    ("Z05", "call centre", range(0, 7), "07:00", "21:00"),
    ("Z06", "nursery", range(0, 5), "07:00", "13:00"),
    ("Z07", "restaurant", range(1, 7), "11:30", "23:00"),
    ("Z08", "bookshop", range(1, 7), "10:00", "18:00"),
    ("Z09", "evening college", range(0, 4), "16:00", "22:00"),
    ("Z10", "bakery", range(0, 7), "04:30", "14:00"),
)
# trend -> the zone its sensor is really in; the office's list says T0n is Z0n
REALLY = {"T03": "Z07", "T07": "Z03", "T05": "Z10", "T10": "Z05"}
WRITES = {"T02": "fahrenheit", "T05": "hundredths", "T08": "kelvin"}


def minutes(clock):
    return int(clock[:2]) * 60 + int(clock[3:])


def kept(zone_row, when):
    _, _, days, start, stop = zone_row
    return when.weekday() in days and \
        minutes(start) <= when.hour * 60 + when.minute < minutes(stop)


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "month"
    (outdir / "outstations").mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    steps = WEEKS * 7 * 24 * 60 // EVERY_MIN
    sealed, zone_of, columns = {}, {}, {}

    for n, row in enumerate(TENANTS, 1):
        zone, trend = row[0], None
        for t in ("T%02d" % k for k in range(1, 11)):
            if REALLY.get(t, "Z" + t[1:]) == zone:
                trend = t
        zone_of[trend] = zone
        wander, slip, slip_size, fuss = 0.0, 0, 0.0, 0
        setpoint = 22.0 + rng.uniform(-0.4, 0.4)
        out_hours = [0.0] * WEEKS
        lines = []
        for i in range(steps):
            when = MONTH_BEGINS + timedelta(minutes=i * EVERY_MIN)
            wander = 0.998 * wander + rng.gauss(0, 0.035)
            if slip:
                slip -= 1
            elif rng.random() < 1 / 650.0:       # the plant slips
                slip = rng.randrange(40, 200)
                slip_size = rng.choice((-1, 1)) * rng.uniform(1.6, 3.2)
            if fuss:
                fuss -= 1
            elif rng.random() < 1 / 2500.0:       # cleaners, a delivery, a fault
                fuss = rng.randrange(10, 45)
            busy = kept(row, when)
            reading = setpoint + wander + (slip_size if slip else 0.0) \
                + rng.gauss(0, 0.16 if busy else 0.03) \
                + (rng.gauss(0, 0.22) if fuss else 0.0)
            reading = round(reading, 2)
            if busy and not BAND[0] <= reading <= BAND[1]:
                out_hours[i * EVERY_MIN // (7 * 24 * 60)] += EVERY_MIN / 60.0
            way = WRITES.get(trend)
            shown = "%.2f" % reading
            stamp = when.strftime("%Y-%m-%d %H:%M")
            if way == "fahrenheit":
                shown = "%.3f" % (reading * 9 / 5 + 32)
            elif way == "hundredths":
                shown = "%d" % round(reading * 100)
            elif way == "kelvin":
                shown = "%.2f" % (reading + 273.15)
            lines.append((stamp, shown))
        columns[trend] = lines
        for week, hours in enumerate(out_hours, 1):
            sealed["%s/%d" % (zone, week)] = round(hours, 2)

    # an outstation trends its two sensors side by side in one file
    for k in range(1, 6):
        pair = ["T%02d" % (2 * k - 1), "T%02d" % (2 * k)]
        with open(outdir / "outstations" / ("OS-%d.csv" % k), "w",
                  newline="") as handle:
            out = csv.writer(handle, lineterminator="\n")
            out.writerow(["logged_at"] + pair)
            for a, b in zip(columns[pair[0]], columns[pair[1]]):
                out.writerow([a[0], a[1], b[1]])
    with open(outdir / "points.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["trend", "zone", "outstation"])
        for k in range(1, 11):
            out.writerow(["T%02d" % k, "Z%02d" % k, "OS-%d" % ((k + 1) // 2)])
    with open(outdir / "occupancy.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["zone", "tenant", "day", "from", "to"])
        names = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
        for zone, tenant, days, start, stop in TENANTS:
            for d in days:
                out.writerow([zone, tenant, names[d], start, stop])
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "wiring.json").write_bytes(json.dumps(
        dict(zone_of=zone_of, writes=WRITES), indent=1, sort_keys=True).encode())
    print("zones %d  readings %d  out-of-band hours %.1f"
          % (len(TENANTS), steps * len(TENANTS), sum(sealed.values())))


if __name__ == "__main__":
    main()
