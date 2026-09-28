"""Place the samples in their beds from the shipped records alone.

This reads only what the agent's container carries and never looks at the
answer. `TRUE_READING` is how the records have to be read; gates.py scores
every other way of reading them.
"""

from __future__ import annotations

import csv
import pathlib
from fractions import Fraction

import coring

TRUE_READING = {
    # One curator books a sample's place in millimetres: his samples lie ten
    # sections' length along a section.
    "millimetres": "to_centimetres",
    # One curator books it in inches: his samples stop two fifths of the way
    # along every section.
    "inches": "to_centimetres",
    # One curator books the sample's depth down the hole in metres, not its
    # place along the section; the section's top depth is on record.
    "hole_depth": "to_place",
    # One curator writes the volume before the place: his places are 2, 5, 8
    # and 10 and his volumes run the length of a section.
    "columns": "unswap",
    # A section is labelled top and bottom at the rig, and about a third of
    # them were labelled the wrong way up. Nothing says which. The beds say it:
    # they are flood layers, each coarsest at its base and fining upward, and
    # the core scanner ran a grain track down every section. In a section
    # labelled upside down every graded bed reads coarsest at its labelled
    # top - and its beds, logged from the labelled top, run up the hole.
    "way_up": "by_the_grading",
}

OTHERS = {
    "millimetres": "as_booked",
    "inches": "as_booked",
    "hole_depth": "as_booked",
    "columns": "as_booked",
    # the natural reading: every section lies the way it is labelled
    "way_up": "as_labelled",
}

EXTRAS = {}


def places():
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    if (yard / "truth.json").is_file():
        return yard, yard
    return pathlib.Path("/app"), here


def load(app):
    app = pathlib.Path(app)

    def rows(name):
        with open(app / (name + ".csv"), newline="") as fh:
            return list(csv.DictReader(fh))

    book = {name: rows(name) for name in ("sections", "beds", "samples",
                                          "scan")}
    book["paper"] = (app / "paper.txt").read_text().split()
    return book


def build(app, reading):
    book = load(app)
    sections = {}
    order = {}
    for row in book["sections"]:
        sections[row["section"]] = {
            "hole": row["hole"], "curator": row["curator"],
            "top_depth": Fraction(row["top_depth_m"]) * 1000,
            "length": coring.mm_from_cm(row["length_cm"]), "beds": [],
            "lean": Fraction(0)}
        order.setdefault(row["hole"], []).append(row["section"])
    for row in book["beds"]:
        s = sections[row["section"]]
        s["beds"].append((coring.mm_from_cm(row["top_cm"]),
                          coring.mm_from_cm(row["base_cm"])))

    # ---- each bed's grading, from the scanner's track ----------------------
    track = {}
    for row in book["scan"]:
        track.setdefault(row["section"], []).append(
            (int(row["at_cm"]) * 10 + 5, int(row["grain_index"])))
    for name, s in sections.items():
        for top, base in s["beds"]:
            third = (base - top) // 3
            upper = [v for at, v in track[name] if top <= at < top + third]
            lower = [v for at, v in track[name] if base - third <= at < base]
            if len(upper) < 2 or len(lower) < 2:
                continue                # too thin a bed to say
            # how much coarser the bed reads in its lower third than in its
            # upper: positive for a flood layer lying the right way up
            s["lean"] += Fraction(sum(lower), len(lower)) - Fraction(
                sum(upper), len(upper))

    # ---- which sections were labelled upside down ---------------------------
    for s in sections.values():
        s["right_way_up"] = True
        if reading["way_up"] == "by_the_grading":
            s["right_way_up"] = s["lean"] >= 0

    # ---- the beds above each section, down the hole -------------------------
    for hole, names in order.items():
        names.sort(key=lambda n: sections[n]["top_depth"])
        above = 0
        for name in names:
            sections[name]["beds_above"] = above
            above += len(sections[name]["beds"])

    # ---- each curator's habit, found and not assumed ------------------------
    by_curator = {}
    for row in book["samples"]:
        by_curator.setdefault(sections[row["section"]]["curator"],
                              []).append(row)

    samples = []
    for curator, rows in by_curator.items():
        places = [Fraction(r["place_cm"]) for r in rows]
        volumes = [Fraction(r["volume_cc"]) for r in rows]
        lengths = [Fraction(sections[r["section"]]["length"], 10) for r in rows]
        exchanged = reading["columns"] == "unswap" \
            and max(places) <= 10 and max(volumes) > 10
        if exchanged:
            places = volumes
        habit = None
        if any(p > n for p, n in zip(places, lengths)):
            if reading["millimetres"] == "to_centimetres":
                habit = "millimetres"
        elif all(p * 2 < n + 5 for p, n in zip(places, lengths)) \
                and max(places) > 25:
            if reading["inches"] == "to_centimetres":
                habit = "inches"
        elif max(places) <= 25:
            if reading["hole_depth"] == "to_place":
                habit = "hole_depth"
        for r, place in zip(rows, places):
            s = sections[r["section"]]
            if habit == "millimetres":
                offset = place
            elif habit == "inches":
                offset = place * coring.INCH_MM
            elif habit == "hole_depth":
                offset = place * 1000 - s["top_depth"]
            else:
                offset = place * 10
            samples.append({"sample": r["sample"], "section": r["section"],
                            "offset": coring.nearest_mm(Fraction(offset))})
    return book, sections, samples


def run(app, reading=None):
    reading = reading or TRUE_READING
    book, sections, samples = build(app, reading)
    wanted = set(book["paper"])
    out = {}
    for sample in samples:
        if sample["sample"] not in wanted:
            continue
        s = sections[sample["section"]]
        along = coring.bed_at(s["beds"], sample["offset"])
        if along is None:
            out[sample["sample"]] = "NONE"
            continue
        out[sample["sample"]] = coring.numbered(
            s["hole"], s["beds_above"], len(s["beds"]), along,
            s["right_way_up"])
    return out
