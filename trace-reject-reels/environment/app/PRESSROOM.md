# Pressroom to die-cutter: how a sheet is followed

## On the press

The press sheets board from the reel and delivers printed sheets onto a pallet,
one on top of another, counting them from 1 as the pallet fills. When a reel
runs out the next is spliced in, and the press books the count of the first
sheet cut from the new reel. `press_ticket.txt` is the job ticket: each pallet,
the number of sheets on it, and the reels that went onto it with the sheet each
began at. A reel that is still running when a pallet is full carries on onto
the next pallet.

## Between the machines

A full pallet goes through the pallet turner, which turns the whole stack over,
so that the sheet printed first lies on top.

## On the die-cutter

The die-cutter feeds from the top of the stack. It counts the sheets it feeds
from 1, measures each sheet's caliper in micrometres as it passes the
double-sheet gauge, and writes a line for each to `diecutter.csv`: the pallet,
the sheet's count as fed, and the caliper. The inspection camera marks a reject
with the pallet and that count, written `P1-00001`.

Shifts set the die-cutter up as they see fit. If a pallet's lines are not as
this section says, they are first made so; no pallet is dropped.

## The claim

A rejected sheet is claimed against the reel it was cut from, with the caliper
the die-cutter measured on that sheet, in whole micrometres.
