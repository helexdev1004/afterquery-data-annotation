# Ways to pass without inspecting the plates, and what stops each

Written by asking what the laziest passing attempt would be. Never executed by
the pipeline.

## 1. Find the answers in the container

Look for a master report, a reference implementation, or anything the grader
compares against.

**Blocked.** There is none. The expected report is generated from the measured
points and baked into the verifier image, which is built separately and never
mounted into the agent's container. `/app` holds the plate files and nothing
else. This is also why the instruction says outright that there is nothing to
check against - it is true, and pretending otherwise would just waste the
solver's time.

## 2. Claim everything passes

Fill the report with `"pass": true` and a plausible number.

**Blocked.** Both halves of every callout are checked. Of the fifty four, a
substantial minority genuinely fail - domed seating faces and holes outside
their position zone - so a blanket pass loses those outright, and every
`actual` still has to land within four microns of the measurement, which
guessing will not do.

## 3. Report the measurement without interpreting it

Give the distance from nominal, the fitted diameter, the spread of the face -
all correctly measured, none of them converted into what the drawing asks for.

**Not blocked, and it is the intended near miss.** Everything is honestly
measured and most of it is right. The position callouts come out at half their
value, which is the diametral convention, and the ones near the limit flip from
fail to pass. Measured on this batch, a report like this gets forty five of
fifty four.

## 4. Use the stated position tolerance

Take the number in the feature control frame and compare against it.

**Not blocked, and it is the other half of the near miss.** At maximum material
condition the tolerance grows with the bore. Six holes across the batch are
inside once the bonus is allowed and outside without it, so this alone costs
six callouts.

## 5. Work in machine coordinates

The points are already three dimensional and the nominal positions are on the
drawing, so subtract and be done.

**Blocked by the plates themselves.** The faces sit about a tenth of a degree
out of square with the machine axes, which across the plate moves a hole by
more than the whole position tolerance. Fifteen verdicts change. Establishing
the frame from the datum faces, in precedence, is not optional here.

## 6. Fit the seating face and take the spread of the residuals

The obvious reading of "how flat is it".

**Not blocked and rarely decisive, but it is still wrong.** The minimum zone is
smaller than the spread about a best fit plane on every face in the batch, by
between one and nine microns. It does not usually change a verdict, which is
why it is worth only a few callouts, but the value is checked to four microns
and the two definitions differ by more than that on several plates.

## 7. Guess the tolerances rather than reading the drawing

Assume the usual shop values.

**Blocked.** The drawing travels in each plate file and the tolerances are
stated there. There is nothing to guess and no credit for guessing it right.
