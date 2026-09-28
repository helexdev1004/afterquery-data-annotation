# Name the manhole each drain runs into

The borough is taking over the private drains on the Enville estate and it
cannot charge for a connection it cannot show. Forty of them were never
recorded, and the man who would have known them retired before the survey was
written up.

`/app/manholes.csv` is the chamber book, every manhole on the estate with the
chamber it falls into and its cover and invert levels. `/app/drains.csv` is the
fifty two drains on the estate and the level and the discharge of each.
`/app/known.csv` is the twelve whose connection the borough already has on
record. `/app/flows.csv` is the flow survey, a gauged rate at every manhole. `/app/tracer.csv` is last autumn's dye survey - where each trace was
put in, and where and when it was seen after. `/app/rain.csv` is the borough's
own rain gauge through the survey weeks. `/app/DRAINAGE.md` is the borough
surveyor's standing instructions: how levels are booked, the fall a drain is
laid to, how a trace is dosed and how fast it runs, and how the flow survey was
taken.

Leave `/app/connections.csv` behind you, a header `drain,manhole` and forty
lines under it, naming the manhole each of the unrecorded drains discharges
into. Thirty seven of the forty have to be right.

Taking each drain on its own will not do it. What is gauged at a manhole is
everything that stands above it, so the drains answer for one another, and the
records of a survey run over several weeks are not all of them of a piece.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
