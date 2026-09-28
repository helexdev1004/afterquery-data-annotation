# Signals review: plans and counts

## The control system's log

The control system runs each junction on one of three plans, P1, P2 or P3, and
chooses the plan from conditions across the whole network. Whenever it changes
a junction's plan it writes a line to `controller.log`: the time, the junction,
the number of the plan run that begins there, and the plan selected. A plan run
lasts from its line until the junction's next line. Plans are changed on the
run; the signals never stop.

## Count sites

Each junction has a count site on its main exit, and its detector file is under
`detectors/`:

| junction | detector file | street |
|---|---|---|
| J1 | commercial-street | Commercial Street |
| J2 | wharf-road | Wharf Road |
| J3 | northgate | Northgate |
| J4 | station-approach | Station Approach |
| J5 | mill-lane | Mill Lane |

A detector file has a line for every twenty seconds: `interval_start`, the time
the twenty seconds began, written `YYYY-MM-DD HH:MM:SS`, and `count`, the
number of vehicles that passed in them.

The detectors were bought from three suppliers over the years, and a file does
not always keep to the paragraph above. One that does not is brought into line
with it first; none is set aside.

## Reckoning

A plan run's vehicles are the sum of the twenty-second counts that began within
the run.
