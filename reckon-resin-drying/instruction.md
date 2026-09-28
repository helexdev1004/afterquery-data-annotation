How long had the resin been drying when each housing was shot?

A customer has sent back brittle housings, and the moulding shop suspects
under-dried resin. Nylon has to sit in a machine's hopper dryer for some hours
before it moulds properly, and the clock starts again every time the dryer is
refilled. The shop has forty suspect housings, each marked with the machine it
came off and its shot number. The dryer refills are booked in the planning
system by the material handlers; the shots are logged by each machine's own
controller. What the lab wants for each housing is the drying time its resin
had had, in hours, when it was shot.

- `/app/DRYING.md` - the shop's drying procedure: how refills are booked, how a
  controller logs its shots, and how drying time is reckoned for a shot.
- `/app/machines.csv` - the five machines, their dryers, and who looks after
  each controller.
- `/app/refills.csv` - every dryer refill the planning system has: dryer, time,
  and the kind of resin that went in.
- `/app/shots/` - each machine controller's shot log.
- `/app/housings.txt` - the forty suspect housings, as machine and shot number.

Write `/app/drying_times.json`, one JSON object whose keys are the forty
housings exactly as they are written in `/app/housings.txt` and whose values
are objects like `{"hours": 3.25, "resin": "virgin"}`. An entry is right when
the hours are within 0.1 and the resin is right. The lab will take the table if
at most four of the forty entries are wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
