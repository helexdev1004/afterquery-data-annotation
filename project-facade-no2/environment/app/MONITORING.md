# Nitrogen dioxide monitoring: from a download to the status report

## Sites and analysers

`sites.csv` lists the ten sites: a code, a name, the type (roadside or urban
background) and the serial number of the analyser installed there. A roadside
site also has
the distance from the monitor's inlet to the kerb, the distance from the nearest
building facade to the kerb, and the local background concentration taken from
the national background maps. The site types, distances and background
concentrations are from the network review carried out by the council's
consultants last year.

## A download

An analyser's download is `downloads/<serial>.csv`. It has a row for every
quarter of an hour of the eight-week monitoring period, 5376 rows: the
`timestamp` in GMT, the quarter-hour mean `no2_ug_m3` in micrograms per cubic
metre referred to 20 C and 1013 hPa, and a `status` of `ok`, `cal` during the
weekly calibration or `fault`. Only `ok` rows count.

The analysers were commissioned by different contractors. A download that does
not follow this section is brought into line with it first; every site is
reported.

## The means

`monitor_mean` is the mean of all the rows that count.

For an urban background site `facade_mean` is the same as `monitor_mean`. For a
roadside site it is carried from the monitor to the facade with the fall-off
adjustment, distances in metres from the kerb:

    fall(d)     = -0.5476 * ln(d) + 2.7171
    facade_mean = (monitor_mean - background) / fall(monitor) * fall(facade) + background

Both means are given to three decimals.
