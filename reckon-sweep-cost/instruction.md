Cost to target for the batch-size sweep

A research group swept batch size on a language model: eight training runs, the
same data and architecture, each to the same target loss. For the write-up the
engineer needs, for every run, the optimiser steps it took to reach the target,
the tokens it consumed to get there and the GPU-hours that cost on the cluster
it ran on.

`/app/SWEEP.md` is the group's note on how a run logs its loss, when a run
counts as having reached the target and how tokens and GPU-hours follow from
steps. The runs and their settings are in `/app/run_sheet.csv`, the measured
step times for each batch size are in `/app/step_times.csv`, and the training
logs are in `/app/logs/`.

The figures go in `/app/cost_to_target.csv` with the columns `run`,
`steps_to_target`, `tokens_to_target` and `gpu_hours`, a line such as
`R9,14200,5816320000,212.4`. A line is right when the steps and tokens are
exact and the GPU-hours are within 0.1, and the write-up needs all eight lines
right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
