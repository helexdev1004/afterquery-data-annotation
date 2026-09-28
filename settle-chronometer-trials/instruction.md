# What does each chronometer rate at on trial?

`/app/sheets/` holds the comparison book for forty chronometers on an eight week
trial, a file to an instrument and a line to each daily comparison against the
observatory's standard clock. `/app/chronometers.csv` gives the maker, the
chamber and the observer for each. `/app/standard.csv` gives the standard
clock's own rate for every day of the trial. `/app/TRIAL.md` is the
observatory's method: the rate, the mean, the variation, the temperature
coefficient and how the trial number is made up of them.
`/app/certificates.csv` gives the trial numbers the observatory already
published for eight of the instruments, computed by its own hands off these
same sheets.

Write `/app/trials.csv` with a header and one row per instrument, the trial
number as a whole number of hundredths of a second:

```
chronometer,trial_number
CH01,329
CH02,138
```

A row counts only where the number is exactly right, and 37 of the 40 have to
be right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
