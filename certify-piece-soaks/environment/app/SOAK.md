# Soak certificates: from the logger's records to a piece's soak

## The logger

Each load is logged on an eight-channel logger, one probe to a channel. Every
ten seconds it writes a line for each channel: the time, the channel and the
probe's reading in degrees Celsius. `load_A.csv` and `load_B.csv` are the two
loads' records, and `channel_schedule.csv` gives the piece on each channel for
each load.

The logger's channels were configured one at a time over the years, by
different technicians. A channel that does not record as this section says is
put into that form first; every piece is certified.

## Calibration

`pieces.csv` gives each piece's probe, its serial number and the figures from
its calibration certificate. A type K thermocouple is corrected by adding its
`offset_c` to the reading. A Pt100 resistance probe is corrected by multiplying
the reading by its `scale`.

## Soak

A piece is soaking on every reading whose corrected temperature is 840.0
degrees Celsius or more, and each such reading counts for ten seconds.
`soak_min` is that time in minutes, and `mean_soak_c` is the mean of the
corrected temperatures over those readings.
