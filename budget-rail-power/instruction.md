Rail power for the board's energy budget

A hardware team is closing the power budget of a battery-powered sensor board
with eight supply rails, all fed from one 5 V bus. A bench logger recorded
every rail's voltage and the voltage across its current-sense resistor through
three test phases - sleep, idle and active - and the power engineer needs the
mean power each rail drew from the bus in each phase, in milliwatts.

`/app/BUDGET.md` is the team's note on how the logger records, how a rail's
current and its draw from the bus follow from the readings and how a phase is
averaged. The rails, their regulators and sense resistors are in
`/app/rails.csv`, the logger's probe map is `/app/probe_map.csv`, and the three
recordings are `/app/phase_sleep.csv`, `/app/phase_idle.csv` and
`/app/phase_active.csv`.

The budget figures go in `/app/rail_power.csv` with the columns `rail`, `phase`
and `mean_mw`, a line such as `VX_9V9,idle,41.37`. A line is right when it is
within 0.5 per cent, and the budget is closed if no more than two of the
twenty-four lines are wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
