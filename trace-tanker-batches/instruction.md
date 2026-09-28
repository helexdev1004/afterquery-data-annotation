Which pipeline batch filled each road tanker

A fuel terminal takes diesel off a pipeline in batches and loads road tankers
from five gantry arms. A customer has complained about cold-flow performance,
and the terminal's quality engineer has to say, for each of forty tanker loads,
which pipeline batch the load was drawn from and how many litres at 15 degrees
C it held. A load is recorded only by its arm and the arm meter's totaliser
readings at start and finish.

`/app/GANTRY.md` is the terminal's note on how batches come down the arm
headers, how the arm meters and their totalisers work and how a load is
corrected to 15 degrees C. `/app/batch_tickets.txt` has the pipeline company's
batch tickets for each header, `/app/arms.csv` lists the arms and their meters,
`/app/tas_log.csv` is the terminal automation system's log, and
`/app/loads.csv` is the list of loads in question.

Write `/app/load_batches.csv` with the columns `load`, `batch` and `litres_15`,
a line such as `L999,B00,31250`. A line is right when the batch is right and
the litres are within 25; the engineer will answer the customer once no more
than four of the forty lines are wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
