How high, and on what, was each soil probe taken?

A study of footpath erosion on five old mineral railways, now walking paths, is
being written up. On each path a fieldworker pushed a measuring wheel from one
end to the other, stopping now and then to push a probe into the path bed and
speak the soil depth into a voice recorder. The wheel's logger wrote down how
far it had rolled every ten seconds and the recorder stamped every spoken
reading with the time, so between them they say where on the path each probe
was taken. The analysis needs the altitude of every probe and the surface it
was taken on, and nobody wrote either down.

What came back from the field:

- `/app/FIELDWORK.md` is the protocol the fieldworkers were given: how a path
  is levelled and its stations listed, how its surfaces are scheduled, how a
  walk is made and logged, and how altitude is worked out between stations.
- `/app/paths.csv` names the five paths, who walked each and when the walk
  began.
- `/app/stations.csv` is the levelling: every surveyed station on each path,
  with its distance along the path and its altitude.
- `/app/surfaces.csv` is the surface schedule.
- `/app/wheel/` has one wheel log per path.
- `/app/readings.csv` has every spoken reading with its time.
- `/app/paper.txt` names the forty readings that go into the paper's main
  figure.

Write `/app/probe_altitudes.jsonl` with one JSON object on a line for each
reading in `/app/paper.txt`, giving the reading's number under `reading`, its
altitude in metres under `altitude_m` and the surface under `surface`, like
`{"reading": "Q000", "altitude_m": 412.3, "surface": "tarmac"}`. A line is
right when the altitude is within half a metre and the surface is the scheduled
one. The figure can go to the journal if at most four of the forty are wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
