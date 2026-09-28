"""The gradiometer survey, as the contractor's specification sets it out.

Everything is whole numbers. Positions are decimetres on the site grid,
readings are whole nanotesla (a cell's reading is carried as an exact fraction
where the instrument logged finer than the cell), and a peak is found by exact
comparison, so two correct implementations must agree to the cell.

This one model is used three times over: gen.py walks the site with it,
gates.py scores every reading of the records with it, and the shipped reference
locates the peaks with it. They cannot drift apart.
"""

from __future__ import annotations

from fractions import Fraction

# --------------------------------------------------------------- published ---
# All of this is stated in SPEC.md and none of it is in doubt.

GRID_DM = 200               # a survey grid is 20 m square
CELL_DM = 5                 # a survey cell is half a metre square
CELLS = GRID_DM // CELL_DM  # forty traverses of forty cells

# ----------------------------------------------------------- not published ---
# The instrument's heading error: it reads this much high carried northwards
# and as much low carried southwards. SPEC.md does not give it. It is in the
# dumps, as the stripes a zig-zag survey always carries, and only gen.py - which
# walks the site - uses the figure.
HEADING = 1


def cell_ref(east_dm: int, north_dm: int) -> str:
    """A cell is referenced by its south-west corner, in decimetres."""
    return "E%04dN%04d" % (east_dm, north_dm)


def traverses(readings, per_cell=1):
    """A logger dump cut into its forty traverses, in the order logged."""
    run = CELLS * per_cell
    lines = []
    for t in range(CELLS):
        line = list(readings[t * run:(t + 1) * run])
        lines.append(line + [None] * (run - len(line)))
    return lines


def assemble(readings, per_cell=1, zigzag=True, begun="S"):
    """Lay a logger dump out as a grid: raster[traverse][cell], from the SW.

    Traverses lie along the grid's north-south lines beginning with the
    westernmost, and the instrument logs readings as they are taken. With
    `zigzag`, every second traverse was walked back the other way and so runs
    the other way in the dump. `begun` is the end the grid was begun from: from
    the south the first traverse runs south to north in the dump, from the
    north it runs north to south.

    Where the instrument logged finer than the cell, a cell takes the mean of
    the readings that fall in it, carried exactly.
    """
    raster = []
    for t, line in enumerate(traverses(readings, per_cell)):
        northwards = (begun == "S") == (t % 2 == 0 or not zigzag)
        if not northwards:
            line = line[::-1]
        cells = []
        for c in range(CELLS):
            group = [v for v in line[c * per_cell:(c + 1) * per_cell]
                     if v is not None]
            cells.append(Fraction(sum(group), len(group)) if group else None)
        raster.append(cells)
    return raster


def peak(mosaic, east_from, east_to, north_from, north_to):
    """The cell holding the greatest reading in a window of the site.

    `mosaic` maps (east_dm, north_dm) of a cell's south-west corner to its
    reading. A cell is in the window if its south-west corner is. Equal
    readings are broken to the west and then to the south.
    """
    best, where = None, None
    for (east, north), value in mosaic.items():
        if value is None or not east_from <= east < east_to \
                or not north_from <= north < north_to:
            continue
        key = (value, -east, -north)
        if best is None or key > best:
            best, where = key, (east, north)
    return where
