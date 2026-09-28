An irrigation trial has ten plots, each with one buried soil moisture probe logging the soil's apparent permittivity every hour; half the probes are TDR probes and half are capacitance probes, and the two kinds need different calibrations to turn permittivity into volumetric water content. For the trial report the soil physicist needs each plot's mean volumetric water content over the six-week trial and its driest daily mean.

`/app/PROBES.md` is the trial's note on how a plot's logger file is laid out, the calibration for each kind of probe and how the means are taken. The plots and the probe installed in each are in `/app/plots.csv`, the probes with their kinds and calibration constants are in `/app/probes.csv`, and the loggers' files are in `/app/loggers/`.

Write `/app/plot_moisture.json`: an object keyed by plot, each value an object with `mean_vwc` and `driest_daily_vwc` in cubic metres of water per cubic metre of soil, for example `"P99": {"mean_vwc": 0.2314, "driest_daily_vwc": 0.1422}`. A plot is right when both figures are within 0.002, and all ten plots have to be right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
