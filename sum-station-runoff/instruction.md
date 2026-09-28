Monthly runoff for the catchment water balance

A hydrologist is closing the quarter's water balance for an upland research
catchment with eight gauging stations. Each station has a stage logger, and the
balance needs each station's runoff volume for each of the three months, in
thousands of cubic metres: stage turned into discharge through the station's
own rating, and discharge summed over the month.

`/app/GAUGING.md` is the hydrologist's note on how stage is logged, how each
kind of control is rated and how a month's volume is summed. The stations, their
controls and rating constants are in `/app/stations.csv`, the field sheet that
says which logger file came from which station is `/app/field_sheet.csv`, and
the logger files are in `/app/stage_logs/`.

The volumes are written to `/app/monthly_runoff.csv` with the columns `station`,
`month` and `runoff_dam3`, a line such as `G99,2027-03,412.6`. A line is right
when the volume is within 0.5 per cent, and the balance is closed with no more
than two of the twenty-four lines wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
