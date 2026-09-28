# Drying procedure

This is the shop's procedure for drying nylon and for keeping the records that
show it was dried.

The five controllers do not all write a time the same way. Where a log cannot
be right against this procedure it is put right before it is used.

## Dryers and refills

Each machine draws from its own hopper dryer; `machines.csv` says which. A
dryer is run down and then refilled in one go, without stopping the machine,
and the drying clock starts again at the refill. The material handler books
every refill in the planning system, and `refills.csv` is that booking: the
dryer, the time to the minute, and the resin that went in - `virgin`,
`blend 20` or `blend 40`, the figure being the share of regrind in a hundred.

## Shot logs

A machine's controller numbers every shot and logs the time the shot ended, as
`YYYY-MM-DD HH:MM:SS.ss`. `shots/` has one log for each machine, named for it.
`machines.csv` gives the time each log began, which is one cycle before the
end of its first shot.

## Drying time

The drying time of a shot is the time from the last refill of its machine's
dryer before the shot to the end of the shot, in hours, and the shot's resin is
the resin that refill put in. A housing is known by its machine and its shot
number, written `M1/123456`.

## Measures

The shop works in site time throughout. Where a time is kept as a count,
second 0 is the start of 1 January 1970, and a spreadsheet's day 25569 is that
same day.
