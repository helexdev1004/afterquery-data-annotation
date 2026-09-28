Tracer breakthrough for the packed-column runs

A hydrology lab sent a radiotracer pulse through eight packed soil columns at
once and counted the outflow with a radiation detector at the foot of each
column, all eight cabled to one scaler that registers counts second by second.
For the transport paper the analyst needs, for every column, the net tracer
counts that passed its detector and the mean residence time of the pulse.

`/app/COUNTING.md` is the lab's note on how the scaler's dump is laid out, how
counts are corrected for dead time and background and how the net counts and
the mean residence time follow. The columns and the detector under each are in
`/app/columns.csv`, the detectors with their types, dead times and scaler
channels are in `/app/detectors.csv`, and the scaler's dump of the run is
`/app/scaler.dmp`.

The figures go in `/app/breakthrough.csv` with the columns `column`,
`net_counts` and `mean_residence_s`, a line such as `C9,1284500.0,412.60`. A
line is right when the net counts are within 0.5 per cent and the residence
time is within 0.5 s, and the paper needs all eight lines right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
