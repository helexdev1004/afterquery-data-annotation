"""Fire the quarry blast and write each data logger's file.

    python fire_shot.py [outdir]

The ground comes first. Every station sees quiet ground for a minute, then the
blast: a P wave and a slower, stronger surface wave, each a burst of 4-12 Hz
shaking that dies away. Each station's sensor turns ground velocity into volts
by its sensitivity and preamp gain, the logger turns volts into counts, and the
sealed peak velocity and peak time are the note's own arithmetic on those
counts. Then the files are written. A logger stamps its file with the station
code it was configured with; two loggers went back to each other's stations
and were never reconfigured.

The two stations are one broadband seismometer and one geophone at about the
same distance, with gains that put their recordings at the same size in
counts, so a file's arrival time and amplitude say nothing about which sensor
made it.
What differs is what the two kinds of sensor see when nothing is happening. A
broadband seismometer records the ocean microseism, a slow swell of several
seconds' period; a 4.5 Hz geophone is deaf to it and records only its own
hiss. The hiss is sized so both kinds of quiet ground have the same spread in
counts: only how one sample stands to the next tells them apart.
"""

import csv
import json
import math
import pathlib
import random
import sys

SEED = 3306174
SPS, SECONDS, SHOT_AT_S = 100, 180, 60
LSB_V = 40.0 / 2 ** 24                  # a 24-bit logger over 40 V
START = "2026-05-12T08:29:00.000000"    # UTC; the shot is at 08:30:00
LOCAL = "2026-05-12T10:29:00.000000"    # the same instant on a local-time logger
QUIET_COUNTS = 230.0                    # spread of quiet ground, either sensor

STATIONS = (
    # station, sensor, kind, V s/m, gain, distance m, peak counts, logger that recorded it, habit
    ("ST01", "Trillium Compact", "broadband", 750.0, 1, 820, 61000, "DL-3107", None),
    ("ST02", "SM-6 4.5 Hz", "geophone", 28.8, 32, 905, 57000, "DL-3112", "local time"),
    ("ST03", "Trillium Compact", "broadband", 750.0, 1, 1540, 38000, "DL-3120", "unsigned"),
    ("ST04", "SM-6 4.5 Hz", "geophone", 28.8, 32, 1525, 38000, "DL-3115", None),
    ("ST05", "SM-6 4.5 Hz", "geophone", 28.8, 32, 2310, 24000, "DL-3126", None),
    ("ST06", "Trillium Compact", "broadband", 750.0, 1, 2120, 27000, "DL-3131", "volts"),
    ("ST07", "SM-6 4.5 Hz", "geophone", 28.8, 32, 3420, 15000, "DL-3144", None),
    ("ST08", "Trillium Compact", "broadband", 750.0, 1, 3180, 17000, "DL-3139", None),
    ("ST09", "Trillium Compact", "broadband", 750.0, 1, 4260, 11000, "DL-3152", None),
    ("ST10", "SM-6 4.5 Hz", "geophone", 28.8, 32, 4610, 9500, "DL-3158", None),
)
# the station code each logger stamps: one pair carry each other's
STAMPS = {s[7]: s[0] for s in STATIONS}
STAMPS.update({"DL-3120": "ST04", "DL-3115": "ST03"})
CHANNEL = {"broadband": "HHZ", "geophone": "EHZ"}


def shaking(rng, n, hz, damping=0.08):
    """White noise through a two-pole resonator at `hz`, scaled to unit peak."""
    w = 2 * math.pi * hz / SPS
    r = 1 - damping
    a1, a2 = 2 * r * math.cos(w), -r * r
    y1 = y2 = 0.0
    out = []
    for _ in range(n):
        y = rng.gauss(0, 1) + a1 * y1 + a2 * y2
        out.append(y)
        y1, y2 = y, y1
    top = max(abs(v) for v in out)
    return [v / top for v in out]


def blast(rng, distance_m):
    """Unit-peak ground motion for the whole file."""
    n = SPS * SECONDS
    p_at = SHOT_AT_S + distance_m / 5200.0
    s_at = SHOT_AT_S + distance_m / 2400.0
    p_wave = shaking(rng, n, rng.uniform(9, 12))
    s_wave = shaking(rng, n, rng.uniform(4, 7))
    trace = []
    for i in range(n):
        t = i / SPS
        v = 0.0
        if t >= p_at:
            v += 0.35 * p_wave[i] * math.exp(-(t - p_at) / 0.9) * min(1.0, (t - p_at) / 0.08)
        if t >= s_at:
            v += 1.0 * s_wave[i] * math.exp(-(t - s_at) / 2.2) * min(1.0, (t - s_at) / 0.25)
        trace.append(v)
    top = max(abs(v) for v in trace)
    return [v / top for v in trace]


def quiet(rng, kind):
    """Quiet ground in counts for the whole file."""
    n = SPS * SECONDS
    if kind == "broadband":
        swell = [(rng.uniform(0.8, 1.2), rng.uniform(0.12, 0.28), rng.uniform(0, 2 * math.pi))
                 for _ in range(5)]
        size = math.sqrt(sum(a * a for a, _, _ in swell) / 2.0)
        hiss = 0.22 * QUIET_COUNTS
        swell_sd = math.sqrt(QUIET_COUNTS ** 2 - hiss ** 2)
        return [swell_sd / size * sum(a * math.sin(2 * math.pi * f * i / SPS + p)
                                      for a, f, p in swell) + rng.gauss(0, hiss)
                for i in range(n)]
    return [rng.gauss(0, QUIET_COUNTS) for _ in range(n)]


def reckon(counts, volts_per_m_s):
    """The note's arithmetic: (peak velocity um/s, seconds after the shot)."""
    shot = SHOT_AT_S * SPS
    rest = sum(counts[:shot]) / shot
    best, where = -1.0, shot
    for i in range(shot, len(counts)):
        size = abs(counts[i] - rest)
        if size > best:
            best, where = size, i
    return best * LSB_V / volts_per_m_s * 1e6, (where - shot) / SPS


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "shot"
    (outdir / "waveforms").mkdir(parents=True, exist_ok=True)
    for old in (outdir / "waveforms").glob("*.slist"):
        old.unlink()
    rng = random.Random(SEED)
    sealed, service = {}, {}

    for station, sensor, kind, sens, gain, dist, peak, logger, habit in STATIONS:
        offset = rng.uniform(-2500, 2500)
        peak *= rng.uniform(0.93, 1.07)
        motion, rest = blast(rng, dist), quiet(rng, kind)
        counts = [int(round(offset + peak * m + q)) for m, q in zip(motion, rest)]
        pgv, at = reckon(counts, sens * gain)
        sealed[station] = [round(pgv, 2), round(at, 2)]
        stamp = STAMPS[logger]
        stamped_kind = [s[2] for s in STATIONS if s[0] == stamp][0]
        service[logger] = dict(stood_at=station, stamps=stamp, kind=kind, habit=habit)

        start, encoding, unit = START, "INTEGER", "COUNTS"
        if habit == "local time":
            start = LOCAL
        if habit == "unsigned":
            shown = ["%d" % (c if c >= 0 else c + 2 ** 24) for c in counts]
        elif habit == "volts":
            encoding, unit = "FLOAT", "VOLTS"
            shown = ["%.7f" % (c * LSB_V) for c in counts]
        else:
            shown = ["%d" % c for c in counts]
        head = "TIMESERIES QB_%s__%s_D, %d samples, %d sps, %s, SLIST, %s, %s" % (
            stamp, CHANNEL[stamped_kind], len(counts), SPS, start, encoding, unit)
        lines = [head] + ["  ".join("%10s" % v for v in shown[i:i + 6])
                          for i in range(0, len(shown), 6)]
        (outdir / "waveforms" / (logger + ".slist")).write_bytes(
            ("\n".join(lines) + "\n").encode())

    with open(outdir / "stations.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["station", "sensor", "kind", "sensitivity_v_s_per_m",
                      "preamp_gain", "distance_m"])
        for s in STATIONS:
            out.writerow([s[0], s[1], s[2], "%.1f" % s[3], s[4], s[5]])
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "service.json").write_bytes(json.dumps(service, indent=1).encode())
    print("stations %d  samples %d" % (len(STATIONS), SPS * SECONDS))


if __name__ == "__main__":
    main()
