# The plot probes: from a logger file to volumetric water content

## Plots and probes

`plots.csv` lists the ten plots with their irrigation treatment and the serial
number of the probe buried in each at 40 cm. `probes.csv` lists the probes:
the kind (TDR or capacitance) and the constants that go with it - a TDR probe's
cable offset, a capacitance probe's laboratory slope and intercept. The kinds
and constants are from the calibration laboratory's certificates.

## A logger file

Each plot has its own logger, and its file is `loggers/<plot>.csv`: a
`timestamp` in local standard time and the `permittivity` the probe reported,
the apparent relative permittivity of the soil, once an hour from 4 May for six
weeks, 1008 rows.

The loggers were programmed by different students. A file that does not follow
this section is brought into line with it first; every plot is reported.

## Calibration

A TDR probe's reading has its cable offset taken off, and the Topp equation
gives the volumetric water content from the corrected permittivity e:

    vwc = -0.053 + 0.0292 e - 0.00055 e^2 + 0.0000043 e^3

A capacitance probe's reading e goes through the laboratory's own line for that
probe:

    vwc = slope * sqrt(e) + intercept

## Means

A day is the 24 rows from midnight. `driest_daily_vwc` is the lowest of the 42
daily means and `mean_vwc` is the mean over all 1008 rows.
