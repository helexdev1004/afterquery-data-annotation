# The batch-size sweep: from a training log to cost-to-target

## Runs and logs

`run_sheet.csv` lists the eight runs: the global batch size in sequences, the
number of GPUs the batch was spread over, the learning rate, and the name of
the run's log under `logs/`. The batch size, GPU count and learning rate are
taken from the cluster scheduler's accounting records. Every sequence is 2048
tokens.

A log has a line every ten optimiser steps, written by the first device: the
step, and the training loss in nats on that device's share of the batch.

The launcher scripts were written by different people at different times. A
log that does not follow this section is brought into line with it first; every
run is costed.

## Reaching the target

The target loss is 3.200. A run has reached it at the first logged step where
the mean of the last twenty logged losses, that step's included, is 3.200 or
less. That step is `steps_to_target`.

## Tokens and GPU-hours

`tokens_to_target` is the steps to target times the global batch size times
2048. `step_times.csv` gives the measured seconds per optimiser step for each
global batch size and number of GPUs; `gpu_hours` is the steps to target times
the seconds per step times the number of GPUs, divided by 3600.
