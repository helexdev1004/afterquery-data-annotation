# Loading gantry: batches, meters and corrected litres

## Headers and batches

Each of the five loading arms stands on its own header, fed straight from the
pipeline manifold. Batches follow one another down a header without mixing.
`batch_tickets.txt` has the pipeline company's tickets: for each header, every
batch and the header's litres at which it began, counted from 00:00 on
1 December 2026, when the log below begins. A load's batch is the batch its
header was on when the load started.

## Meters and the log

Each arm has a turbine meter. The terminal automation system divides the
meter's pulses by the arm's K-factor, which `arms.csv` gives in pulses per
litre, and keeps a running totaliser for the arm in litres. Every ten seconds
it writes a line to `tas_log.csv` with, for each arm, the totaliser and the
product temperature in degrees Celsius. Arms load at between 2,000 and 2,600
litres a minute. A load's paperwork carries the arm's totaliser at the start
and at the finish of the load, and `loads.csv` has those readings for the
loads in question.

The system was configured arm by arm as the gantry grew. Where an arm's
columns are not as this section describes them they are corrected first; no
arm is left out.

## Litres at 15 degrees C

A load's litres at 15 degrees C are its litres multiplied by
1 - 0.00084 x (T - 15), where T is the mean of the temperatures logged for the
arm while the load was flowing: the lines from the first on which its
totaliser stood above the load's start reading to the first on which it stood
at the load's finish reading, both included.

A US gallon is 3.785411784 litres.
