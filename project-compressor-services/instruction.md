Service due dates for the compressor house

A factory's compressed-air plant has eight compressors, and the maintenance
planner services each one by what it has done since its last service: running
hours for some kinds of machine, starts for others. The plant's power monitor
logs every compressor's motor current, and the planner needs, for each
compressor, its running hours and starts over the logged fortnight and the date
its next service falls due at that rate of use.

`/app/COMPRESSORS.md` is the planner's note on how a running hour and a start
are read from a motor current and how a due date is projected. The machines,
their ratings, kinds and last services are in `/app/asset_register.csv`, the
monitor's wiring schedule is `/app/monitor_channels.csv`, and the fortnight's
log is `/app/current_log.csv`.

The answer is written to `/app/service_due.csv` with the columns `compressor`,
`run_hours`, `starts` and `due_date`, for example `K9,212.4,37,2027-02-18`. A
line is right when the hours are within 0.2, the starts are exact and the date
is within a day; the planner will accept the file only when all eight lines
are right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
