"""Locate the peaks from the shipped records alone.

This reads only what the agent's container carries and never looks at the
answer. `TRUE_READING` is how the records have to be read; gates.py scores
every other way of reading them.
"""

from __future__ import annotations

import csv
import itertools
import pathlib
import statistics
from fractions import Fraction

import survey

TRUE_READING = {
    # One surveyor left the instrument on its tenth-of-a-nanotesla range: his
    # grids read ten times everybody else's.
    "units": "rescale",
    # One surveyor books a grid's position by its centre, where the
    # specification asks for its south-west corner: his grids lie across their
    # neighbours.
    "position": "to_corner",
    # One surveyor books northing before easting: his grids fall off the site.
    "columns": "unswap",
    # One surveyor logged at a quarter-metre sample interval, so his dumps run
    # to twice the length; a cell takes the mean of the readings in it.
    "sampling": "mean_of_cell",
    # A grid is walked zig-zag, as the specification says, so every second
    # traverse runs the other way in the dump. It is easy to leave out.
    "walk": "zigzag",
    # The specification has every grid begun at its south-west corner. Sixteen
    # of the forty were begun from the north, and no field sheet says which.
    # What says it is the instrument's heading error: a fluxgate reads a
    # little high carried one way and a little low carried the other, so in
    # every dump the first, third and fifth traverses stand a little apart
    # from the second, fourth and sixth. Which way round they stand in a grid
    # begun from the south is shown by the one surveyor who kept to the
    # specification; a grid where they stand the other way round was begun
    # from the north.
    "begun": "by_heading",
}

OTHERS = {
    "units": "as_logged",
    "position": "as_booked",
    "columns": "as_booked",
    "sampling": "as_cells",
    "walk": "parallel",
    # the natural reading: every grid begun where the specification says
    "begun": "south_west",
}

EXTRAS = {}


def places():
    here = pathlib.Path(__file__).resolve().parent
    yard = here.parent / "yard"
    if (yard / "truth.json").is_file():
        return yard, yard
    return pathlib.Path("/app"), here


def dm(text):
    """Metres to one place, as whole decimetres, without touching a float."""
    whole, _, part = text.strip().partition(".")
    return int(whole) * 10 + int((part + "0")[:1])


def load(app):
    app = pathlib.Path(app)

    def rows(name):
        with open(app / name, newline="") as fh:
            return list(csv.DictReader(fh))

    grids = rows("grids.csv")
    dumps = {}
    for row in grids:
        text = (app / "dumps" / (row["grid"] + ".txt")).read_text()
        dumps[row["grid"]] = [int(v) for v in text.split()]
    return grids, dumps, rows("anomalies.csv")


def tile(grids, reading):
    """Where every grid's south-west corner really stands.

    Found, not assumed: forty grids tile the surveyed block exactly, corner to
    corner, with none lying across another. Each surveyor's booking is tried as
    it stands, by the centre, with the columns exchanged, and both; only one
    way of taking all five surveyors' books tiles the block.
    """
    booked = {g["grid"]: (dm(g["east_m"]), dm(g["north_m"])) for g in grids}
    people = sorted({g["surveyor"] for g in grids})
    half = survey.GRID_DM // 2

    def apply(how, pos):
        east, north = pos
        if "swap" in how:
            east, north = north, east
        if "centre" in how:
            east, north = east - half, north - half
        return east, north

    options = ["plain"]
    if reading["position"] == "to_corner":
        options.append("centre")
    if reading["columns"] == "unswap":
        options += ["swap"] + (["swap centre"]
                               if reading["position"] == "to_corner" else [])

    best, chosen = None, None
    for combo in itertools.product(options, repeat=len(people)):
        how = dict(zip(people, combo))
        placed = [apply(how[g["surveyor"]], booked[g["grid"]]) for g in grids]
        clashes = len(placed) - len(set(placed))
        easts = [p[0] for p in placed]
        norths = [p[1] for p in placed]
        off = sum(1 for e, n in placed
                  if (e - min(easts)) % survey.GRID_DM
                  or (n - min(norths)) % survey.GRID_DM)
        slots = ((max(easts) - min(easts)) // survey.GRID_DM + 1) * \
                ((max(norths) - min(norths)) // survey.GRID_DM + 1)
        cost = (clashes + off, slots, sum(c != "plain" for c in combo))
        if best is None or cost < best:
            best, chosen = cost, how
    return ({g["grid"]: apply(chosen[g["surveyor"]], booked[g["grid"]])
             for g in grids}, chosen)


def heading_step(readings, per_cell):
    """How far the odd-numbered traverses of a dump stand above the even.

    Counting the first traverse as the first. Carried northwards the instrument
    reads high and southwards low, so this is positive for a grid whose first
    traverse was walked northwards and negative for one whose first traverse
    was walked southwards. An anomaly lies under odd and even traverses alike,
    so over eight hundred readings a side it does not decide the matter.
    """
    lines = survey.traverses(readings, per_cell)

    def mean(chosen):
        values = [v for line in chosen for v in line if v is not None]
        return Fraction(sum(values), len(values))

    return mean(lines[0::2]) - mean(lines[1::2])


def run(app, reading=None):
    reading = reading or TRUE_READING
    grids, dumps, anomalies = load(app)
    corners, booking = tile(grids, reading)

    # ---- the instrument left on the wrong range ------------------------------
    scale = {g["grid"]: 1 for g in grids}
    if reading["units"] == "rescale":
        quiet = {}
        for g in grids:
            values = sorted(abs(v) for v in dumps[g["grid"]])
            quiet[g["grid"]] = values[len(values) // 2]
        usual = statistics.median(quiet.values())
        for name, level in quiet.items():
            if level >= 5 * max(1, usual):
                scale[name] = 10

    prepared = {}
    for g in grids:
        name = g["grid"]
        readings = dumps[name]
        per_cell = 1
        if reading["sampling"] == "mean_of_cell" \
                and len(readings) == 2 * survey.CELLS * survey.CELLS:
            per_cell = 2
        if scale[name] != 1:
            readings = [v // scale[name] for v in readings]
        prepared[name] = (readings, per_cell)

    # ---- which way the instrument's heading error runs -----------------------
    # Found, not assumed. One surveyor kept to the specification in everything
    # that can be checked - his range, his sample interval, his bookings - and
    # the specification has every grid begun at its south-west corner, so his
    # first traverses were walked northwards. Whichever way his first, third
    # and fifth traverses stand against his second, fourth and sixth is the
    # way the instrument reads when it is carried northwards.
    kept = [who for who, how in booking.items() if how == "plain" and all(
        scale[g["grid"]] == 1
        and len(dumps[g["grid"]]) == survey.CELLS * survey.CELLS
        for g in grids if g["surveyor"] == who)]
    northwards_high = sum(heading_step(*prepared[g["grid"]]) for g in grids
                          if g["surveyor"] in kept) >= 0

    mosaic = {}
    for g in grids:
        name = g["grid"]
        readings, per_cell = prepared[name]

        # ---- which end the grid was begun from -------------------------------
        begun = "S"
        if reading["begun"] == "by_heading" and (
                heading_step(readings, per_cell) < 0) == northwards_high:
            begun = "N"

        zigzag = reading["walk"] == "zigzag"
        raster = survey.assemble(readings, per_cell, zigzag, begun)
        east0, north0 = corners[name]
        for t, line in enumerate(raster):
            for c, value in enumerate(line):
                mosaic[(east0 + t * survey.CELL_DM,
                        north0 + c * survey.CELL_DM)] = value

    out = {}
    for row in anomalies:
        where = survey.peak(mosaic, dm(row["east_from_m"]), dm(row["east_to_m"]),
                            dm(row["north_from_m"]), dm(row["north_to_m"]))
        out[row["anomaly"]] = survey.cell_ref(*where) if where else "NONE"
    return out
