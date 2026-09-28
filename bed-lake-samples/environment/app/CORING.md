# Coring and curation note

This note is the whole of how the project's five holes were cored, logged and
sampled.

The five curators did not all book a sample alike. Where an entry cannot be
right against this note it is put right before it is used.

## Holes and sections

The lake's fill is flood layers, a bed to a flood. Each hole was cored from the
lake floor down in sections about a metre and a half long. A section is pushed out of the barrel, capped, and labelled top and
bottom at the rig. `sections.csv` gives every section's hole and curator, the
depth of its top below the lake floor in metres, and its length in centimetres.
A little core is lost at the shoe between one section and the next.

## The bed log

Before a section was split it was run through the core scanner, which reads a
grain-size index every centimetre along it from the labelled top, a higher
index being coarser sediment; `scan.csv` is its track.

Each section was then split and logged from its labelled top. `beds.csv` gives
every bed the logger saw in a section, in the order he came to them: where the
bed's top and base stand in centimetres along the section.

## Bed numbers

Beds are numbered down each hole from the lake floor, and the numbers run on
from section to section: `H2-B001` is the first bed under the floor of hole 2.
Those are the numbers the project's papers use. Nothing is counted for the core
lost at the shoe.

## Samples

A sample is cut from the archive half of a section and booked by its section,
its place along the section in centimetres from the labelled top, and its volume
in cubic centimetres.

A sample cut exactly on a bed boundary goes with the bed beyond the boundary,
the one further along the section.

The project's papers quote, beside a sample's bed, the scanner's grain index
at the sample: the reading of the centimetre its place falls in, so a sample
at 36.4 cm takes the reading at 36.

## Measures

The project works in centimetres along a section. An inch is 25.4 mm.
