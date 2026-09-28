# Gradiometer survey specification

This is the whole of how the survey was to be made and recorded. Every figure
and every rule the survey was let to is here.

Five surveyors walked the site, and they did not all keep to this
specification. Where a record cannot be right against it, the record is put
right before it is used.

## The site grid

Positions are eastings and northings on the site grid, in metres. The surveyed
area is a block of forty survey grids with no gaps and no overlaps.

## Survey grids

A survey grid is **20 m square**, laid out square to the site grid. Its
position is recorded on the field sheet as the easting and northing of its
**south-west corner**.

## The instrument

The instrument is a fluxgate gradiometer with a logger. Readings are in **whole
nanotesla**, on the instrument's 1 nT range, and nothing in the log is
corrected. The logger writes each reading down as it is taken, and a dump is
the log as it came off the instrument, one reading to a line, and carries
nothing else.

## Walking a grid

Traverses lie north and south, **0.5 m apart**, and the instrument takes a
reading every **0.5 m** along a traverse: forty traverses of forty readings to
a grid. A grid is begun at its south-west corner and its first traverse is the
one along its west edge. It is walked **zig-zag**: out along one traverse and
back along the next.

## Survey cells

A reading stands for a **survey cell 0.5 m square**. A cell is referenced by
the site grid position of its south-west corner in whole decimetres, easting
then northing, each to four figures: the cell whose south-west corner stands at
43.5 m east and 21.0 m north is `E0435N0210`.

Where a traverse was logged at a finer sample interval than 0.5 m, a cell takes
the **mean** of the readings that fall in it.

## An anomaly's peak

An anomaly is given a window of the site: eastings from `east_from_m` up to but
not including `east_to_m`, and northings likewise. A cell is in the window if
its south-west corner is. The anomaly's **peak** is the cell in the window with
the greatest reading. Equal readings are broken to the west, and then to the
south.
