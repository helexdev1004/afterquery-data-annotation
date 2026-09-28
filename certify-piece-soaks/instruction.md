Soak times for the heat-treatment certificates

A metallurgy lab austenitised two furnace loads of eight test pieces each, every
piece with its own temperature probe, and must certify each piece's soak: the
minutes it spent at or above 840 degrees Celsius and its mean temperature over
that time, after each probe's calibration correction. Some pieces carry type K
thermocouples and some platinum resistance probes, and the two kinds are
corrected differently.

`/app/SOAK.md` is the lab's note on how the logger records, how each kind of
probe is corrected and how a soak is reckoned. The pieces, their probes and the
probes' calibration figures are in `/app/pieces.csv`, the logger's channel
schedule for each load is `/app/channel_schedule.csv`, and the logger's records
are in `/app/load_A.csv` and `/app/load_B.csv`.

The certificate figures go in `/app/soaks.csv` with the columns `piece`,
`soak_min` and `mean_soak_c`, a line such as `X99,47.5,851.3`. A line is right
when the minutes are within 0.5 and the temperature within 0.3, and the
certificates are issued if no more than one of the sixteen lines is wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
