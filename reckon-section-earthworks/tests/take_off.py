"""Take off cut, fill and topsoil strip at the wanted cross-sections from the
shipped records alone.

Nothing here looks at the sealed figures. `PROPERLY` is how the field books
have to be read; audit_task.py scores every other way of reading them.

Four of the five surveyors booked something the office note does not: offsets
in feet, levels in feet, levels in millimetres, chainages in kilometres. Each
shows at once and each is only a unit.

The fifth thing is not like those. The note books an offset positive to the
right of the centreline looking up chainage. Two surveyors booked theirs
positive to the left. Nothing says which, and nothing breaks: a cross-section
runs as far one way as the other, the template sits on it either way, and
every area comes out - of the wrong ground. No mean says it: these schemes
cross no ditch, bank or hedge, and the fall of the ground across a road is
whatever it is. What says it is the land. Ploughed land is rougher from one
staff position to the next than pasture is, and the land either side of each
centreline is scheduled, because the topsoil allowance needs it. Booked the
wrong way round, a surveyor's rough ground lies on the pasture.
"""

import csv
import json
import pathlib

import template

PROPERLY = {"offsets_feet": "convert", "levels_feet": "convert",
            "levels_mm": "convert", "chainage_km": "convert",
            "hand": "ask_the_ground"}
AS_BOOKED = {"offsets_feet": "leave", "levels_feet": "leave",
             "levels_mm": "leave", "chainage_km": "leave",
             "hand": "right_positive"}
OTHER_HANDS = ("left_positive",)


def sheet(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def where():
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    return yard if (yard / "sealed.json").is_file() else pathlib.Path("/app")


def median(values):
    values = sorted(values)
    return values[len(values) // 2] if values else 0.0


class FieldBook:
    """One scheme's cross-sections, put into metres under a given reading."""

    def __init__(self, rows, formation, reach_m, reading):
        self.units = []
        chain = [float(r["chainage_m"]) for r in rows]
        offs = [float(r["offset_m"]) for r in rows]
        levs = [float(r["level_m"]) for r in rows]

        c_unit = o_unit = l_unit = 1.0
        if max(chain) < 0.01 * max(formation):
            self.units.append("chainage_km")
            if reading["chainage_km"] == "convert":
                c_unit = 1000.0
        if max(abs(o) for o in offs) > 2.0 * reach_m:
            self.units.append("offsets_feet")
            if reading["offsets_feet"] == "convert":
                o_unit = template.FOOT_M
        ratio = median(levs) / median(formation.values())
        if ratio > 100:
            self.units.append("levels_mm")
            if reading["levels_mm"] == "convert":
                l_unit = 0.001
        elif ratio > 2:
            self.units.append("levels_feet")
            if reading["levels_feet"] == "convert":
                l_unit = template.FOOT_M

        self.sections = {}
        for c, o, z in zip(chain, offs, levs):
            self.sections.setdefault(int(round(c * c_unit)), []).append(
                (o * o_unit, z * l_unit))
        for points in self.sections.values():
            points.sort()

    def roughness(self, land_at, flipped):
        """Middle value, on each kind of land, of how far a booked level stands
        from the straight line between the levels either side of it."""
        found = {}
        for chainage, points in self.sections.items():
            for (x0, z0), (x1, z1), (x2, z2) in zip(points, points[1:],
                                                    points[2:]):
                x = -x1 if flipped else x1
                kind = land_at(chainage, x, clear=1.0)
                if kind and x2 > x0:
                    line =z0 + (z2 - z0) * (x1 - x0) / (x2 - x0)
                    found.setdefault(kind, []).append(abs(z1 - line))
        return {kind: median(values) for kind, values in found.items()}


def read_job(app, reading):
    app = pathlib.Path(app)
    job = {}
    for row in sheet(app / "schemes.csv"):
        job[row["scheme"]] = {
            "left": float(row["left_width_m"]),
            "right": float(row["right_width_m"]),
            "cut_slope": float(row["cut_slope_1_in"]),
            "fill_slope": float(row["fill_slope_1_in"]),
            "formation": {}, "land": []}
    for row in sheet(app / "formation.csv"):
        job[row["scheme"]]["formation"][int(round(float(row["chainage_m"])))] \
            = float(row["formation_level_m"])
    for row in sheet(app / "land.csv"):
        job[row["scheme"]]["land"].append(
            (float(row["from_chainage_m"]), float(row["to_chainage_m"]),
             float(row["from_offset_m"]), float(row["to_offset_m"]),
             row["land"]))

    for name, s in job.items():
        reach = max(abs(v) for _, _, a, b, _ in s["land"] for v in (a, b))

        def land_at(chainage, x, clear=0.0, strips=s["land"]):
            for c0, c1, a, b, kind in strips:
                if c0 <= chainage < c1 and a + clear <= x < b - clear:
                    return kind
            return None

        s["land_at"] = land_at
        book = FieldBook(sheet(app / "sections" / (name + ".csv")),
                         s["formation"], reach, reading)
        s["book"] = book
        s["contrast"] = {}
        for hand, flipped in (("right_positive", False),
                              ("left_positive", True)):
            rough = book.roughness(land_at, flipped)
            s["contrast"][hand] = rough.get(template.ROUGHEST_LAST[-1], 0.0) \
                / max(rough.get(template.ROUGHEST_LAST[0], 0.0), 1e-9)
        if reading["hand"] == "ask_the_ground":
            s["hand"] = max(s["contrast"], key=s["contrast"].get)
        else:
            s["hand"] = reading["hand"]
    return job


def figures(app, reading=None):
    app = pathlib.Path(app)
    job = read_job(app, reading or PROPERLY)
    out = {}
    for wanted in (app / "wanted.txt").read_text().split():
        name, chainage = wanted.split("/")
        s = job[name]
        points = s["book"].sections.get(int(chainage))
        if not points or int(chainage) not in s["formation"]:
            continue
        if s["hand"] == "left_positive":
            points = sorted((-x, z) for x, z in points)
        land = [(a, b, kind) for c0, c1, a, b, kind in s["land"]
                if c0 <= int(chainage) < c1]
        try:
            cut, fill, strip = template.take_off(
                points, s["formation"][int(chainage)], s["left"], s["right"],
                s["cut_slope"], s["fill_slope"], land)
        except ValueError:
            continue
        out[wanted] = [round(cut, 1), round(fill, 1), round(strip, 1)]
    return out


if __name__ == "__main__":
    import sys

    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else where()
    rows = ["section,cut_m2,fill_m2,strip_m2"]
    for section, (cut, fill, strip) in sorted(figures(target).items()):
        rows.append("%s,%.1f,%.1f,%.1f" % (section, cut, fill, strip))
    (target / "areas.csv").write_text("\n".join(rows) + "\n")
