# Cable blowing procedure

This is the contractor's procedure for blowing fibre cable into duct. It is all
the crews have.

The five crews did not all log alike. Where a log cannot be right against this
procedure it is put right before it is used.

## Routes and ducts

A route runs from its A chamber to its B chamber, and distances along it are
reckoned from the A chamber. `ducts.csv` schedules each route's duct, length by
length, by distance from the A chamber in metres: smoothwall, ribbed, or the
old earthenware that some routes still run through. A place exactly where the
duct changes takes the duct of the length beyond it.

`routes.csv` gives each route's chambers, the crew that blew it, and the time
of day the blow began, which is the time of the log's first line.

## The blow

The blowing machine is set up at the A chamber with its counter at nought and
the cable is blown through to the B chamber in one go. The machine writes a
line every second, the time of day and the length of cable paid out so far in
metres; `blows/` has one log for each route, named for it. The cable head is
as far along the route as the cable that has been paid out.

## Alarms

When the pressure alarm sounds the machine stops paying out and stamps the
alarm with the time of day, from the same clock as the log; the crew clears it
and the blow goes on. `alarms.csv` has every alarm: its number, its route and
the time it sounded. An alarm's place is where the cable head stood when it
sounded.

## Measures

The contractor works in metres. A foot is 0.3048 m.
