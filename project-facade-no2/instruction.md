A council's air quality officer is preparing the nitrogen dioxide section of the annual status report from ten continuous monitoring sites, five at the roadside and five at urban background locations. For each site the officer needs the mean concentration over the monitoring period at the monitor and the mean at the nearest building facade, which for a roadside site means applying the fall-off-with-distance adjustment.

`/app/MONITORING.md` is the team's note on how an analyser's download is laid out, which readings count, and how a roadside mean is carried from the monitor to the facade. The sites with their types, distances, local background concentrations and the analyser installed at each are in `/app/sites.csv`, and the analysers' downloads are in `/app/downloads/`.

The figures go in `/app/no2_report.csv` with the columns `site`, `monitor_mean` and `facade_mean` in micrograms per cubic metre, a line such as `ZZ9,31.840,27.060`. A line is right when both figures are within 0.5 per cent, and the report needs all ten lines right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
