"""Phase the finds from the shipped archive alone.

This reads only what the agent's container carries and never looks at the
answer. `TRUE_READING` is how the archive has to be read; gates.py scores
every other way of reading it.
"""

from __future__ import annotations

import csv
import pathlib
from fractions import Fraction

import site_model as site

FAR_TEAM = 100      # the far team's context numbers stand a hundred higher

TRUE_READING = {
    # One supervisor books a find's depth below his trench's own bench mark
    # and never reduced it to site datum. As booked his finds stand above the
    # turf; the bench mark's depth below datum is on record for every trench.
    "benchmark": "reduce",
    # One supervisor's sections were digitised with the two columns exchanged:
    # his "offsets" stop at three metres and his "depths" run the trench.
    "columns": "unswap",
    # One supervisor's drawings were digitised at twice the scale: they run to
    # twice the length the trench is.
    "scale": "rescale",
    # One supervisor books a find's depth as a level above Ordnance datum.
    "levels": "to_depth",
    # A cut feature removed what stood where it was dug, so a find inside its
    # outline belongs to its fill. The manual says so; it is easy to leave out.
    "features": "cuts_take",
    # Two teams dug every trench and met at a point taped FROM THE ZERO PEG,
    # while a find's offset is read ALONG ITS DRAWING. A trench's two drawings
    # run opposite ways about - a section is drawn by someone facing it, left
    # to right - so one of them runs towards the zero peg, and along that one
    # the meeting point stands at (length - meeting). The manual says none of
    # this. What settles it is each drawing's own hand: each team drew its own
    # length of each section, one with its points about a metre apart and the
    # other about forty centimetres, so a drawing changes hands where the
    # teams met - which shows whether the meeting point stands at the taped
    # figure along it or at the trench's length less that.
    "meeting": "from_the_peg",
}

OTHERS = {
    "benchmark": "as_booked",
    "columns": "as_booked",
    "scale": "as_booked",
    "levels": "as_booked",
    "features": "layers_only",
    # the natural reading: every drawing taken to run from the zero peg
    "meeting": "along_the_drawing",
}

# Two more ways of taking the meeting point, scored alongside: seeing that a
# trench's two drawings run opposite ways and taking the north one for the one
# that runs from the peg, and leaving the second team out altogether.
EXTRAS = {"meeting": ("north_from_the_peg", "one_team")}


def places():
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    if (yard / "truth.json").is_file():
        return yard, yard
    return pathlib.Path("/app"), here


def cm(text):
    """Metres to two places, as whole centimetres, without touching a float."""
    text = text.strip()
    sign = -1 if text.startswith("-") else 1
    whole, _, part = text.lstrip("-").partition(".")
    return sign * (int(whole or 0) * 100 + int((part + "00")[:2]))


def load(app):
    app = pathlib.Path(app)

    def rows(name):
        with open(app / (name + ".csv"), newline="") as fh:
            return list(csv.DictReader(fh))

    return {name: rows(name) for name in
            ("trenches", "sections", "finds", "to_phase")}


def value_at(poly, x):
    for (x1, z1), (x2, z2) in zip(poly, poly[1:]):
        if x1 <= x <= x2:
            if x1 == x2:
                return Fraction(z1)
            return Fraction(z1) + Fraction((z2 - z1) * (x - x1), x2 - x1)
    return None


def change_of_hand(boundary, pit_edges=()):
    """Where along a drawing the spacing of its points changes, and how sharply.

    Each team drew its own length of each section, one with a point every metre
    or so and the other with a point every thirty centimetres, so a drawing's
    points stand closer together on one side of the place the teams met than
    on the other. Returns (how many times closer, the offset of the change).
    """
    # a pit's two edges are digitised because the pit is there, not because
    # the draughtsman's hand put a point there, so they are left out
    points = sorted({x for x, _ in boundary} - set(pit_edges))
    gaps = [b - a for a, b in zip(points, points[1:])]
    best = (Fraction(1), points[len(points) // 2])
    for i in range(4, len(gaps) - 3):
        left = Fraction(sum(gaps[:i]), i)
        right = Fraction(sum(gaps[i:]), len(gaps) - i)
        ratio = max(left / right, right / left)
        if ratio > best[0]:
            best = (ratio, points[i])
    return best


def build(app, reading):
    book = load(app)

    trenches = {}
    for row in book["trenches"]:
        trenches[row["trench"]] = {"length": cm(row["length_m"]),
                                   "tbm": cm(row["tbm_m"]),
                                   "meet": cm(row["meeting_m"])}

    raw = {}
    for row in book["sections"]:
        key = (row["trench"], row["section"], row["context"], row["kind"],
               row["boundary"])
        raw.setdefault(key, []).append(
            (int(row["point"]), cm(row["offset_m"]), cm(row["depth_m"])))

    by_trench = {}
    for key, points in raw.items():
        by_trench.setdefault(key[0], []).extend(points)

    # ---- the exchanged columns, found and not assumed -----------------------
    swapped = set()
    if reading["columns"] == "unswap":
        for name, points in by_trench.items():
            # an offset runs the length of the trench and a depth does not
            if max(p[1] for p in points) < max(p[2] for p in points):
                swapped.add(name)

    # ---- the drawings at the wrong scale ------------------------------------
    factor = {}
    for name, points in by_trench.items():
        far = max((p[2] if name in swapped else p[1]) for p in points)
        factor[name] = 1
        if reading["scale"] == "rescale":
            ratio = Fraction(far, trenches[name]["length"])
            if ratio > Fraction(3, 2):
                factor[name] = round(ratio)

    sections = {}
    for (name, side, context, kind, label), points in raw.items():
        poly = []
        for _, x, z in sorted(points):
            if name in swapped:
                x, z = z, x
            poly.append((x // factor[name], z // factor[name]))
        poly.sort()
        entry = sections.setdefault((name, side), {})
        entry.setdefault((context, kind), {})[label] = poly

    built = {}
    for key, contexts in sections.items():
        layers, features = [], []
        for (context, kind), polys in contexts.items():
            item = (context, polys["top"], polys["bottom"])
            (features if kind == "cut" else layers).append(item)
        surface = min((item[1] for item in layers),
                      key=lambda poly: sum(z for _, z in poly))
        floor = max((item[2] for item in layers),
                    key=lambda poly: sum(z for _, z in poly))
        built[key] = {"layers": layers, "features": features,
                      "surface": surface, "floor": floor}

    finds = []
    for row in book["finds"]:
        finds.append({"find": row["find"], "trench": row["trench"],
                      "section": row["section"], "x": cm(row["offset_m"]),
                      "z": cm(row["depth_m"])})

    # ---- depths booked as levels --------------------------------------------
    if reading["levels"] == "to_depth":
        for name in trenches:
            mine = [f for f in finds if f["trench"] == name]
            if mine and min(f["z"] for f in mine) > site.DATUM_LEVEL_CM // 2:
                for f in mine:
                    f["z"] = site.DATUM_LEVEL_CM - f["z"]

    def adrift(name, extra=0):
        """Finds of this trench standing above the turf or under the floor."""
        count = 0
        for f in finds:
            if f["trench"] != name:
                continue
            key = (name, f["section"])
            ground = value_at(built[key]["surface"], f["x"])
            base = value_at(built[key]["floor"], f["x"])
            if ground is None or base is None \
                    or f["z"] + extra < ground or f["z"] + extra >= base:
                count += 1
        return count

    # ---- depths left unreduced from the trench's own bench mark -------------
    if reading["benchmark"] == "reduce":
        for name, t in trenches.items():
            mine = sum(1 for f in finds if f["trench"] == name)
            if adrift(name) * 5 > mine and adrift(name, t["tbm"]) < adrift(name):
                for f in finds:
                    if f["trench"] == name:
                        f["z"] += t["tbm"]

    # ---- which way each drawing runs ----------------------------------------
    # The manual says nothing of which way a drawing runs. Where a site's pits
    # run right across its trenches they stand in both drawings of a trench
    # and, matched up by their size, show that the two run opposite ways
    # about. On this site no pit reaches both sections, so this finds nothing
    # and each drawing is settled on its own, by where it changes hands.
    def paired(name, turned):
        """Pits of the two drawings that match in size and stand together."""
        length = trenches[name]["length"]
        count = 0
        for _, n_top, n_bottom in built[(name, "N")]["features"]:
            for _, s_top, s_bottom in built[(name, "S")]["features"]:
                n_a, n_b = n_top[0][0], n_top[-1][0]
                s_a, s_b = s_top[0][0], s_top[-1][0]
                if turned:
                    s_a, s_b = length - s_b, length - s_a
                n_deep = max(z for _, z in n_bottom) - min(z for _, z in n_top)
                s_deep = max(z for _, z in s_bottom) - min(z for _, z in s_top)
                if abs((n_b - n_a) - (s_b - s_a)) <= 8 \
                        and abs(n_deep - s_deep) <= 30 \
                        and abs(n_a - s_a) <= 60 and abs(n_b - s_b) <= 60:
                    count += 1
        return count

    from_peg = {}
    for name, t in trenches.items():
        from_peg[(name, "N")] = from_peg[(name, "S")] = True
        if reading["meeting"] == "from_the_peg":
            # Which of the two runs from the zero peg is shown by where each
            # drawing changes hands, which is where the teams met: at the taped
            # figure along a drawing that runs from the peg, and at the
            # trench's length less it along one that runs towards the peg.
            sharpness = {}
            for side in ("N", "S"):
                edges = {x for _, top, _ in built[(name, side)]["features"]
                         for x in (top[0][0], top[-1][0])}
                sharpness[side], where = change_of_hand(
                    built[(name, side)]["surface"], edges)
                from_peg[(name, side)] = abs(where - t["meet"]) <= abs(
                    where - (t["length"] - t["meet"]))
            if from_peg[(name, "N")] == from_peg[(name, "S")] \
                    and paired(name, True) > paired(name, False):
                # the pits say the two run opposite ways; trust the drawing
                # whose change of hand is the sharper
                sharper = max(sharpness, key=sharpness.get)
                other = "S" if sharper == "N" else "N"
                from_peg[(name, other)] = not from_peg[(name, sharper)]
        elif reading["meeting"] == "north_from_the_peg":
            from_peg[(name, "S")] = False

    return book, trenches, built, from_peg, finds


def run(app, reading=None):
    reading = reading or TRUE_READING
    book, trenches, built, from_peg, finds = build(app, reading)
    wanted = {row["find"] for row in book["to_phase"]}

    out = {}
    for f in finds:
        if f["find"] not in wanted:
            continue
        name = f["trench"]
        key = (name, f["section"])
        context = site.locate(built[key], f["x"], f["z"],
                              use_features=reading["features"] == "cuts_take")
        if context is None:
            out[f["find"]] = "NONE"
            continue
        taped = f["x"] if from_peg[key] else trenches[name]["length"] - f["x"]
        far = reading["meeting"] != "one_team" and taped > trenches[name]["meet"]
        out[f["find"]] = str(int(context) + (FAR_TEAM if far else 0))
    return out
