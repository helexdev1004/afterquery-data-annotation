# Earthworks note

This is how the office books cross-sections and takes earthworks areas off
them.

The five surveyors did not all book alike. Where a field book cannot be right
against this note it is put right before it is used.

## Cross-sections

A scheme is sectioned every ten metres of chainage. At each cross-section the
surveyor books the ground as a line of points across the road: the chainage in
metres, each point's offset from the centreline in metres, positive to the
right looking up chainage, and its level in metres above datum. `sections/` has
one field book per scheme, named for it. Between two booked points the ground
is taken as the straight line between them.

## The template

`schemes.csv` gives each scheme's template and `formation.csv` the formation
level at every cross-section. The formation is level, from `left_width_m` to
the left of the centreline to `right_width_m` to the right of it. From each
edge of the formation a side slope runs outward until it meets the ground.
Where the ground at the edge stands above formation level the slope is a cut
slope, rising outward at 1 vertical in `cut_slope_1_in` horizontal; where it
stands below, a fill slope, falling outward at 1 in `fill_slope_1_in`.

## Areas

At a cross-section, cut is the area of ground standing above the template and
fill the area of template standing above the ground, both taken between the
two points where the side slopes meet the ground, in square metres.

## Topsoil

Topsoil is stripped over the whole width between those same two points before
any earth is moved. `land.csv` schedules the land across each scheme, by
chainage and by offset from the centreline: `pasture` is stripped to 0.15 m,
`woodland` to 0.25 m and `arable` to 0.30 m. The strip area at a cross-section
is the width on each kind of land times its depth, summed. A schedule line runs
from its first chainage up to but not including its last, and from its first
offset up to but not including its last. Cut and fill are taken to the ground
as booked, before stripping.

## Measures

The office works in metres. A foot is 0.3048 m.
