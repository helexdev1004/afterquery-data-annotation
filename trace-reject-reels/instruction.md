Which paper reel each rejected sheet came from

A carton printer runs sheets through a press, stacks them on pallets, and later
feeds the pallets through a die-cutter, where an inspection camera rejects bad
sheets. The buyer wants to claim against the board mill for the rejects, and
needs each rejected sheet tied to the reel of board it was cut from. The
camera knows only the pallet and the sheet's count as it was fed; the press
knows which reel it was sheeting as each pallet filled.

`/app/PRESSROOM.md` is the pressroom's note on how pallets are filled, turned
and fed. `/app/press_ticket.txt` is the press's job ticket, with the six
pallets and every reel change it booked by pallet and sheet count, and
`/app/diecutter.csv` is the die-cutter's sheet-by-sheet record. The rejected
sheets are listed in `/app/rejects.txt`.

Write `/app/reject_reels.csv` with the columns `reject`, `reel` and
`caliper_um`, a line such as `P9-04417,R000,412`: the reel the sheet came from
and the caliper the die-cutter measured on it. A line is right when the reel is
right and the caliper is within 2 micrometres; the claim goes in when 38 of
the 42 lines are right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
