# Counting the column runs

## The run and the scaler's dump

`columns.csv` lists the eight columns: the soil, the packed length, the flow
and the detector at the column's foot. Each soil was packed twice.
`detectors.csv` lists the detectors: the type (GM is a Geiger-Mueller tube, NaI
a sodium-iodide scintillator), the dead time in microseconds and the scaler
channel the detector's cable was plugged into. The detector types and dead
times are from the manufacturers' certificates, and each detector is bolted to
its own column's stand.

`scaler.dmp` has one block per channel, headed `[CHn]`. A block holds the
counts the channel registered in each one-second bin, ten bins to a line, 1500
bins from t = 0. The tracer went into all eight columns together at t = 120 s.

The scaler's channels were set up by different students over the years. A
block that does not follow this section is brought into line with it first;
every column is worked up.

## Dead time

A detector with dead time tau seconds that registered m counts in a one-second
bin saw m / (1 - m * tau) events in that bin. Every bin is corrected this way
before anything else is done with it.

## Background, net counts and residence time

The background is the mean of the corrected counts over the bins that end at or
before t = 120 s. A later bin's net count is its corrected count less the
background; it may come out negative and is kept as it is.

`net_counts` is the sum of the net counts over every bin from t = 120 s to the
end of the dump, to one decimal. A bin's time is its midpoint, measured from
t = 120 s. `mean_residence_s` is the sum of time times net count over the same
bins, divided by `net_counts`, to two decimals.
