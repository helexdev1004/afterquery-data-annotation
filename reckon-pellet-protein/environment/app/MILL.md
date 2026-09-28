# How the mill runs, for the quality lab

This note is what the lab works from when it ties a pellet sample back to the
ration it was pressed from.

The five press loggers were not all set up alike. Where a log cannot be right
against this note it is put right before it is used.

## Bins and presses

Finished meal is held in five bins, and each press draws from one of them;
`routing.csv` is the routing table. A bin holds one formula at a time. When the
batching system starts sending a new formula to a bin it books the change, and
`bin_changes.csv` has every such booking: the bin, the time, and the formula
the bin holds from then on. Bins are changed over on the run, without stopping
the press.

## Press logs

Every press has a tonnage counter that is never reset. Its logger writes a line
every ten seconds, the time of day as `YYYY-MM-DD HH:MM:SS` and the counter's
reading in tonnes; `press_logs/` has one log for each press, named for it.
`routing.csv` also gives, for each press, the time its log began and the
counter's reading at that moment.

## Samples

A pellet sample is caught at the press's die and tagged with the press and the
counter's reading as it was caught, written `P1@1234.56`. Between two lines of
a log the counter is taken to have run evenly.

## Expected protein

`formulas.csv` gives each formula's ingredients and the inclusion of each, in
per cent of the formula as fed. `assays.csv` gives each ingredient's crude
protein and moisture, in per cent, and the basis the protein is quoted on. A
protein quoted on a dry-matter basis is brought to the ingredient as fed by
multiplying it by one less the moisture as a fraction. A formula's expected
protein is the sum over its ingredients of inclusion times as-fed protein.

## Measures

The mill works in tonnes. A tonne is 1000 kg, or 2204.62262 lb.
