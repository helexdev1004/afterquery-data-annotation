Traffic served by each signal plan run

The deliverable is `/app/plan_volumes.csv`, one line for every plan run the
signals team asked about, with the columns `run` and `vehicles`; a line looks
like `J9-042,1835`. A plan run is one unbroken spell of one signal plan at one
junction, and `vehicles` is the number of vehicles the junction's count site
recorded while it lasted.

A town's traffic signals team is reviewing the plans its control system chose
at five junctions over one week. The system logs every change of plan, and each
junction has a detector on its main exit that counts passing vehicles. The
review needs to know how much traffic each plan run actually served.

What there is to work from:

1. `/app/COUNTS.md`, the team's note on the control system's log, the count
   sites and how a plan run's vehicles are reckoned.
2. `/app/controller.log`, the control system's log of every change of plan.
3. `/app/detectors/`, one file for each count site, named for its street.
4. `/app/runs_wanted.txt`, the plan runs the team asked about.

A run is right when its vehicles are within 2 in 100 of the true count. The
team will take the sheet if at least 36 of the 40 runs are right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
