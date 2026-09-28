"""Weekly good share and error budget used, for every service.

    python budgets.py [folder]        writes folder/error_budget.csv

`budgets(folder, reading)` is the job; `reading` says, for each way the
collector's records can differ from the team's note, which to believe.
"""

import csv
import math
import pathlib
import statistics
import sys
from datetime import datetime

THE_RECORDS = {"microseconds": "to_ms", "seconds": "to_ms",
               "status_text": "leading_number", "relabel": "ask_the_runtime"}
THE_NOTE = {"microseconds": "as_ms", "seconds": "as_ms",
            "status_text": "not_a_number", "relabel": "as_ruled"}


def base():
    here = pathlib.Path(__file__).resolve().parent
    return pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        here.parent / "fortnight"


def table(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def read_streams(folder, reading):
    """{stream: [(week, status or None, latency ms)]} and each stream's habits."""
    raw = {}
    for r in table(folder / "requests.csv"):
        raw.setdefault(r["stream"], []).append(r)
    first = min(datetime.fromisoformat(r["time"]) for rs in raw.values()
                for r in rs[:1])
    monday = datetime(first.year, first.month, first.day)
    streams, habits = {}, {}
    for stream, rows in raw.items():
        found, scale = [], 1.0
        middle = statistics.median(float(r["latency_ms"]) for r in rows)
        if middle > 5000:
            found.append("microseconds")
            scale = 0.001 if reading["microseconds"] == "to_ms" else 1.0
        elif middle < 5:
            found.append("seconds")
            scale = 1000.0 if reading["seconds"] == "to_ms" else 1.0
        texty = not rows[0]["status"].isdigit()
        if texty:
            found.append("status_text")
        out = []
        for r in rows:
            when = datetime.fromisoformat(r["time"])
            week = (when - monday).days // 7 + 1
            if texty and reading["status_text"] != "leading_number":
                status = None
            else:
                status = int(r["status"].split()[0])
            out.append((week, status, round(float(r["latency_ms"]) * scale, 1)))
        streams[stream], habits[stream] = out, found
    return streams, habits


def memory(requests, objective):
    """How far one ordinary request's latency foretells the next one's: the
    correlation of neighbouring log latencies, slow requests left out."""
    logs = [math.log(l) for _, _, l in requests if 0 < l <= objective]
    if len(logs) < 50:                 # nothing ordinary to go by
        return 0.0
    a, b = logs[:-1], logs[1:]
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return cov / math.sqrt(sum((x - ma) ** 2 for x in a)
                           * sum((y - mb) ** 2 for y in b))


def budgets(folder, reading):
    """{'svc/1': (good_pct, budget_used_pct)} and what each stream showed."""
    folder = pathlib.Path(folder)
    catalog = {r["service"]: r for r in table(folder / "service_catalog.csv")}
    ruled = {r["stream"]: r["service"] for r in table(folder / "collector_rules.csv")}
    streams, habits = read_streams(folder, reading)
    carries, seen = dict(ruled), {}
    for stream, requests in streams.items():
        listed = catalog[ruled[stream]]
        m = memory(requests, float(listed["latency_objective_ms"]))
        seen[stream] = dict(habits=habits[stream], ruled=ruled[stream],
                            memory=m, looks="jvm" if m > 0.08 else "native")
    if reading["relabel"] == "ask_the_runtime":
        odd = [s for s, v in seen.items()
               if v["looks"] != catalog[v["ruled"]]["runtime"]]
        for s in odd:        # its partner: the odd stream with the same objectives
            mine = catalog[ruled[s]]
            for other in odd:
                theirs = catalog[ruled[other]]
                if other != s and (mine["latency_objective_ms"],
                                   mine["target_good_pct"]) == (
                        theirs["latency_objective_ms"],
                        theirs["target_good_pct"]):
                    carries[s] = ruled[other]
    out = {}
    for stream, requests in streams.items():
        service = catalog[carries[stream]]
        seen[stream]["carries"] = carries[stream]
        objective = float(service["latency_objective_ms"])
        target = float(service["target_good_pct"])
        for week in (1, 2):
            mine = [r for r in requests if r[0] == week]
            ok = sum(1 for _, status, latency in mine
                     if status is not None and status < 500
                     and latency <= objective)
            pct = 100.0 * ok / len(mine)
            out["%s/%d" % (carries[stream], week)] = (
                round(pct, 3), round((100 - pct) / (100 - target) * 100, 1))
    return out, seen


if __name__ == "__main__":
    where = base()
    answer, _ = budgets(where, THE_RECORDS)
    with open(where / "error_budget.csv", "w", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["service", "week", "good_pct", "budget_used_pct"])
        for key in sorted(answer):
            service, week = key.split("/")
            sheet.writerow([service, week, "%.3f" % answer[key][0],
                            "%.1f" % answer[key][1]])
    print("%d lines written" % len(answer))
