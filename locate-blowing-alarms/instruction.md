Where along the duct did each blowing alarm happen?

Five fibre cables were blown into new duct routes last month, and the blowing
machines' pressure alarms went off many times along the way. Forty of those
alarms are to be followed up with a duct rod and a camera, and the crews need
to know where on each route to look and what duct they will find there. A
machine does not record places. It logs the length of cable it has paid out
every second, and it stamps each alarm with the time.

- `/app/BLOWING.md` - the contractor's blowing procedure: how a route is
  scheduled from its A chamber, how a blow is set up and logged, and how an
  alarm is booked.
- `/app/routes.csv` - the five routes, the crew that blew each, and the time
  the blow began.
- `/app/ducts.csv` - each route's duct schedule: every length of duct by its
  distance from the A chamber, with the kind of duct it is.
- `/app/blows/` - the machine's log for each route.
- `/app/alarms.csv` - every alarm the machines booked, with its time.
- `/app/follow_up.txt` - the forty alarms to be followed up.

Write `/app/dig_sheet.csv` with the header `alarm,from_a_m,duct` and one row
for each alarm in `/app/follow_up.txt`: the alarm's number, how far along the
route from the A chamber the cable head was when it sounded, in metres, and the
kind of duct there, for example `A000,1234.5,ribbed`. A row is right when the
distance is within two metres and the duct is the scheduled one. The crews can
go out if at most four of the forty rows are wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
