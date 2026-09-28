# Our network adjustment only works on our own networks

We run a small survey office. For years every job we adjusted looked the same:
a handful of stations, distances only, measured round three times, held on two
known points. The program we inherited handles those fine and we have never had
reason to doubt it.

The work coming in now does not look like that. Long thin traverses. Jobs where
the distances arrive with azimuths from a gyro, quoted to a fraction of a
second. Jobs held on a single station because that is all the client has. We
are getting numbers out of the old program for these and I do not trust any of
them, so I would rather have the adjustment written properly than keep patching
what we have.

Put it in `/app/solution/adjust.py`, as a function `adjust(network)` taking one
of these network files already parsed and returning:

    {"rank_deficient": bool,
     "points": {"<id>": {"x": float, "y": float}},
     "variance_factor": float or null,
     "blunders": ["<observation id>", ...]}

`/app/networks` has the jobs. Each gives approximate coordinates, which points
are held fixed, and the observations - distances in metres, azimuths in degrees
clockwise from the y axis, each with the standard deviation it was measured to.
Azimuth precisions are quoted in arc seconds.

`/app/published` has our accepted results for three of them, in exactly the
shape above. Those are the ones I am confident in. Use them to check yourself.

What I will do with it: run it over the jobs on my desk, which are not in here.
Nine of the ten have to come out right. For each one I check the coordinates of
every point against the survey we generated them from, to fifty millimetres;
the variance factor; and which observations you threw out.

On throwing observations out: an observation is in error if the rest of the
network cannot account for its residual at the one in a thousand level. Reject
it, adjust again without it, and keep going until nothing is left that fails.
Be careful here. How well a network checks a given observation varies enormously
from one to the next, and a residual that looks unremarkable is not the same
thing as an observation that is sound.

The fixed points in each file carry the coordinate system, so there is one
answer and not a family of them. If the observations do not determine the free
points at all, say so with `rank_deficient` and I will not look at the rest -
that is a real answer and I would rather have it than a plausible-looking set
of coordinates.

`numpy` is installed. The network is open if you want anything else.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
