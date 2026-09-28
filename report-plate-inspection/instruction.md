# Six plates measured, and nobody left to write up the inspection

Our inspector walked out mid-contract and left me with the CMM output for a
batch of six plates and a customer waiting on the report. I can read the point
files well enough but I am not going to sign off tolerances I do not understand,
so I need the report written properly.

The measurements are in `/app/plates`, one JSON file per plate. Each holds the
drawing requirements and the measured points, in millimetres, in machine
coordinates. Every plate is the same design: a seating face, two side faces
that square it up, and four bored holes.

The drawing in each file gives you the datum reference frame, the flatness
tolerance on the seating face, the size limits on the bores, and the position
tolerance on the holes with its material condition modifier.

Write the report to `/app/inspection.json`, a list with one entry per plate:

    [{"plate": "plate-01",
      "callouts": [{"callout": "flatness", "feature": "A",
                    "actual": 0.0, "pass": true},
                   {"callout": "size",     "feature": "H1", ...},
                   {"callout": "position", "feature": "H1", ...}]}]

One `flatness` entry per plate, then a `size` and a `position` entry for each of
the four holes. Nine callouts a plate, fifty-four altogether. `actual` is the
value you measured for that callout and `pass` is whether it meets the drawing.

Everything is to be evaluated as ASME Y14.5 defines it. That is the whole of
the specification and I am not going to paraphrase it at you - if the standard
and your intuition disagree about what a number means, the standard is what the
customer is buying and what I am checking against.

I check every callout, both the number and the verdict. The number has to be
within four microns of what the measurement actually gives, which is loose
enough that how you fit a feature will not fail you on its own, and tight
enough that the wrong definition will. Fifty of the fifty-four have to be right.

There is no master report to check yourself against. If there were I would not
need this doing. Work from the points and the standard.

`numpy` and `scipy` are installed and the network is open.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
