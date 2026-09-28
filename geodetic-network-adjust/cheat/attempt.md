# Ways to pass without adjusting the networks, and what stops each

Written by asking what the laziest passing attempt would be. Never executed by
the pipeline.

## 1. Return the published answers

`/app/published` holds correct results for three jobs, in exactly the shape the
function must return. So key off the network name and return them.

**Blocked.** The published jobs are not graded. Grading runs on ten jobs that
are not in the agent's container at all, and their names are not in it either.
A lookup table returns nothing for every graded job.

## 2. Read the answers at run time

Have `adjust()` open the truth files, or the reference answers, from disk.

**Blocked.** Those live under `/tests` inside the verifier image, which is
built separately and is never mounted into the agent's container. The runner
executes as an unprivileged account with no access to anything but the network
file it is handed and the module itself. A submission that goes looking finds
nothing and fails on the answer it does not have.

## 3. Declare everything rank deficient

`rank_deficient: true` skips the coordinate, variance and blunder checks, so
claim it for every job and nothing else gets looked at.

**Blocked.** The claim is checked first and against the truth of the matter.
Two of the ten jobs are genuinely rank deficient; on the other eight the claim
is simply wrong and the job is failed on that alone. This caps the attempt at
two of ten against a pass mark of nine.

## 4. Never reject anything

Return an empty blunder list and hope the rest carries.

**Not blocked, and it is most of the way there.** Eight of the ten jobs contain
no gross error, so an empty list is right for them. It fails the two that do,
which with the two rank-deficient jobs is four failures against a pass mark of
nine. That is the intended shape: the blunder work is worth exactly as much as
it should be.

## 5. Reject anything that looks large

Compare each residual with its own standard deviation and throw out whatever
exceeds three sigma.

**Not blocked, and it is the intended near miss.** It is the test most people
write and it is right about which observations are sound on every job the
office has published. On the graded jobs the error sits on a tie whose
redundancy number is about one sixth, so five sixths of it is absorbed into the
coordinates of the station it serves and the residual reads two sigma. The test
passes a blunder and the variance factor and coordinates are wrong with it.

## 6. Tune against the published jobs until they match

Run all three, compare with `/app/published`, adjust until they agree, stop.

**Not blocked, and this is the point of the task.** Measured on this bundle: a
straightforward implementation reproduces all three published jobs exactly and
gets six of the ten graded jobs right. Everything the agent can check says the
work is done. The published jobs are distance only, well conditioned and firmly
held, so they exercise neither the weighting, nor the conditioning, nor the
datum, nor a blunder the network can barely see.

## 7. Overfit the rejection threshold

Pick a critical value that happens to give the right answer on the published
jobs and hope it transfers.

**Neither blocked nor rewarded.** The graded answer is the same for every
critical value between 3.0 and 4.5 - this was checked by running the whole
reject-and-adjust loop at five values across that range on every job. Tuning
the threshold changes nothing. What changes the answer is whether the residual
is standardised by the redundancy number first.

## 8. Reimplement from a library

Install a geodetic adjustment package and call it.

**Allowed.** The network is open and the instruction says so. Finding a library
that does weighting across mixed units, rank detection and data snooping
correctly, and driving it with these files, is a legitimate route and is real
work. Grading looks only at the answers.
