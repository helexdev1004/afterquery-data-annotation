# The chronometer trial — the observatory's method

## What a trial is

An instrument is kept in a rating chamber for eight weeks and compared against
the observatory's standard clock once a day. The comparison book for each
instrument is the file named for it in `sheets/`. Every figure in this method
and in every sheet is in **hundredths of a second**, and every figure the
method produces is a whole number of hundredths.

`against_standard` is the instrument against the standard clock: how far ahead
of the standard the instrument stood when the comparison was taken.

## The rate

The standard clock has a rate of its own, and `standard.csv` gives it for each
day of the trial. The instrument's rate over an interval between two
comparisons is how far the comparison moved, with the standard's own rate for
the days of that interval put back on:

    rate = (against_standard at the later comparison
            - against_standard at the earlier comparison)
           + the standard's rate for each day of the interval

A rate is a rate **a day**.

## The mean daily rate

The mean of the rates over the whole trial.

## The variation

The mean of the steps between consecutive rates, each step taken without
regard to sign.

## The temperature coefficient

The trial holds the chamber at the ordinary temperature of the room, then for
one week cold, then for one week warm, then at the ordinary temperature again.
`thermometer` on each line of a sheet is the chamber thermometer at the
comparison, in whole degrees.

The coefficient is the change in rate for one degree, taken between the two
held weeks:

    coefficient = (the mean rate of the warm week - the mean rate of the cold week)
                  / (the mean thermometer of the warm week
                     - the mean thermometer of the cold week)

## The trial number

    trial number = |mean daily rate| + 2 x variation + 10 x |coefficient|

The lower the number the better the instrument.

## Rounding

Every division is taken to the nearest whole hundredth, and a half goes away
from zero. Nothing is carried in fractions at any stage.

## The certificates

`certificates.csv` gives the trial numbers the observatory published for the
instruments it had already certificated. They are the observatory's own
figures, computed by the observatory's own hands from these same sheets.

## What is wanted

For each instrument, its trial number.
