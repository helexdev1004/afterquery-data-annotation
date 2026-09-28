"""What each way of working up the sealed days scores, written to accounts.json.

    python accounts.py

Every figure quoted in task.toml is read from that file, none is typed.  The
accounts are the ones a solver could plausibly ship:

  reference         the note's arithmetic, each plate judged by how its wells'
                    departures follow one another
  lay-out believed  the note's arithmetic and nothing else
  every plate turned
  judged by spread  plate turned if the crude wells' spread about their lines
                    sits better the other way round (it cannot: the spread is
                    the same for both preparations)
  judged by rate    the same with the fitted rate
  judged by level   the same with the level at the first read
"""
import json
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tests_src"))     # where marking.py sits while being built

import activities                                               # noqa: E402
import bench                                                    # noqa: E402
import marking                                                  # noqa: E402


def per_well(plate, what):
    per_min = 1.0 if plate["time_unit"] == "min" else 1.0 / 60.0
    minutes = [t * per_min for t in plate["read_times"]]
    fitted = activities.fits(plate)
    out = {}
    for name, series in plate["reads"].items():
        slope, level = fitted[name]
        if what == "rate":
            out[name] = slope
        elif what == "level":
            out[name] = level
        else:
            off = [activities.absorbance(v, plate["mode"]) - level - slope * t
                   for v, t in zip(series, minutes)]
            out[name] = statistics.pstdev(off)
    return out


def turned_by(plate, what):
    value = per_well(plate, what)

    def apart(at):
        crude, spun = [], []
        for w, d in plate["layout"].items():
            if d["role"] == "sample":
                (crude if d["prep"] == "crude" else spun).append(value[at(w)])
        return abs(statistics.mean(crude) - statistics.mean(spun))

    return apart(activities.turned) > apart(lambda w: w)


def figures(day, flips):
    got = {}
    for plate in day["plates"]:
        alone = dict(plate)
        if flips[plate["plate"]]:
            alone["reads"] = {activities.turned(w): s for w, s in plate["reads"].items()}
        got.update(activities.work_up({"plates": [alone]}, judge="as_laid"))
    return got


def main():
    judges = {
        "reference": lambda p: activities.went_in_end_for_end(p, activities.fits(p)),
        "lay-out believed": lambda p: False,
        "every plate turned": lambda p: True,
        "judged by spread": lambda p: turned_by(p, "spread"),
        "judged by rate": lambda p: turned_by(p, "rate"),
        "judged by level": lambda p: turned_by(p, "level"),
    }
    right = dict.fromkeys(judges, 0)
    total = plates = turned = misjudged = 0
    for seed in marking.UNSEEN_SEEDS:
        day, was_turned = bench.one_day(seed)
        want = marking.true_figures(day, was_turned)
        total += len(want)
        plates += len(was_turned)
        turned += sum(was_turned.values())
        for name, judge in judges.items():
            flips = {p["plate"]: judge(p) for p in day["plates"]}
            if name == "reference":
                misjudged += sum(flips[k] != was_turned[k] for k in flips)
            got = figures(day, flips)
            right[name] += sum(marking.line_is_right(got[k], want[k]) for k in want)
    out = {"days": len(marking.UNSEEN_SEEDS), "plates": plates, "plates_turned": turned,
           "lines": total, "bar": marking.BAR, "needed": int(-(-marking.BAR * total // 1)),
           "reference_misjudged_plates": misjudged,
           "accounts": {k: {"right": v, "share": round(v / total, 4)} for k, v in right.items()}}
    (HERE / "accounts.json").write_text(json.dumps(out, indent=1) + "\n", encoding="ascii",
                                        newline="\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
