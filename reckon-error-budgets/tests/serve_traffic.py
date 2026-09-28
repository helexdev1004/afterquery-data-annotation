"""Serve a fortnight of traffic on eight services, then collect the records.

    python serve_traffic.py [outdir]

The services come first: every request is answered by one real service, fast or
slow, well or with a server error, and a week's good share and budget are
counted from that. Then the collector writes the records, stream by stream. Its
relabelling rules say which service a stream is; for two pairs of services the
rules were pasted the wrong way round when the collector was last rebuilt.

Each crossed pair is two services with the same objectives and much the same
traffic, so nothing about a stream's level gives it away: not its volume, not
its latency percentiles, not its error rate. What differs is the runtime. A
service on a garbage-collected runtime slows as its heap fills and snaps back
when it is collected, so one request's latency says something about the next
one's; on a native runtime it says nothing. The catalogue
says which runtime each service is on.
"""

import csv
import json
import math
import pathlib
import random
import sys
from datetime import datetime, timedelta

SEED = 4795831
BEGINS = datetime(2027, 2, 1)                  # a Monday
DAYS = 14

SERVICES = (
    # service, runtime, latency objective ms, target %, stream really carrying it, habit
    ("svc-accounts", "jvm", 350, 99.5, "s01", None),
    ("svc-billing", "native", 400, 99.0, "s06", None),
    ("svc-catalog", "jvm", 300, 99.5, "s03", "microseconds"),
    ("svc-checkout", "native", 250, 99.5, "s08", None),
    ("svc-ledger", "native", 300, 99.5, "s05", "seconds"),
    ("svc-notify", "jvm", 400, 99.0, "s02", None),
    ("svc-search", "native", 200, 99.0, "s07", "status text"),
    ("svc-session", "jvm", 250, 99.5, "s04", None),
)
REASONS = {200: "OK", 201: "Created", 204: "No Content", 404: "Not Found",
           500: "Internal Server Error", 503: "Service Unavailable"}


def main():
    outdir = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        pathlib.Path(__file__).resolve().parent.parent / "fortnight"
    outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    span = DAYS * 86400.0
    records, sealed, truth = [], {}, {}

    for name, runtime, objective, target, stream, habit in SERVICES:
        per_second = rng.uniform(0.019, 0.024)           # requests a second
        slow_share = rng.uniform(0.0016, 0.0042)
        error_share = rng.uniform(0.0006, 0.0016)
        good = {1: [0, 0], 2: [0, 0]}
        # a collected runtime slows as its heap fills and snaps back when it
        # is collected; a native one has the same spread with no memory in it
        k, t, heap_from, heap_for = 0, 0.0, 0.0, rng.uniform(7200, 21600)
        while True:
            t += rng.expovariate(per_second)
            if t >= span:
                break
            while t > heap_from + heap_for:
                heap_from += heap_for
                heap_for = rng.uniform(7200, 21600)
            if runtime == "jvm":
                drag = -0.5 + 1.0 * (t - heap_from) / heap_for
            else:
                drag = rng.uniform(-0.5, 0.5)
            if rng.random() < slow_share:
                latency = objective * rng.uniform(1.15, 3.0)
            else:
                latency = objective * min(0.9, rng.lognormvariate(-1.9, 0.45)
                                          * math.exp(drag))
            latency = round(latency, 1)
            status = rng.choice((500, 503)) if rng.random() < error_share \
                else rng.choices((200, 201, 204, 404), (80, 8, 6, 6))[0]
            week = 1 if t < 7 * 86400 else 2
            good[week][1] += 1
            good[week][0] += status < 500 and latency <= objective
            if habit == "microseconds":
                shown = "%d" % round(latency * 1000)
            elif habit == "seconds":
                shown = "%.4f" % (latency / 1000.0)
            else:
                shown = "%.1f" % latency
            code = "%d %s" % (status, REASONS[status]) \
                if habit == "status text" else str(status)
            records.append((t, stream, code, shown))
        for week, (ok, total) in good.items():
            pct = 100.0 * ok / total
            sealed["%s/%d" % (name, week)] = [
                round(pct, 3), round((100 - pct) / (100 - target) * 100, 1)]
        truth[name] = dict(stream=stream, runtime=runtime, habit=habit)

    records.sort()
    with open(outdir / "requests.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["time", "stream", "status", "latency_ms"])
        for t, stream, code, shown in records:
            stamp = BEGINS + timedelta(seconds=t)
            out.writerow([stamp.strftime("%Y-%m-%dT%H:%M:%S.")
                          + "%03d" % (stamp.microsecond // 1000),
                          stream, code, shown])
    with open(outdir / "service_catalog.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["service", "runtime", "latency_objective_ms",
                      "target_good_pct"])
        out.writerows(s[:4] for s in SERVICES)
    with open(outdir / "collector_rules.csv", "w", newline="") as handle:
        out = csv.writer(handle, lineterminator="\n")
        out.writerow(["stream", "service"])
        for n, s in enumerate(SERVICES, 1):
            out.writerow(["s%02d" % n, s[0]])
    (outdir / "sealed.json").write_bytes(json.dumps(
        sealed, indent=1, sort_keys=True).encode())
    (outdir / "relabel_truth.json").write_bytes(json.dumps(
        truth, indent=1).encode())
    print("services %d  requests %d" % (len(SERVICES), len(records)))


if __name__ == "__main__":
    main()
