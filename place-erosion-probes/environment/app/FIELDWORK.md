# Fieldwork protocol, footpath erosion study

This is the whole of what the fieldworkers were given.

The five of them did not all log alike. Where a log cannot be right against
this protocol it is put right before it is used.

## Levelling

Every path was levelled before the study began. `stations.csv` lists a path's
stations in order from its foot, the foot being the end its distances are
reckoned from: each station's distance along the path in metres, wheeled along
the ground, and its altitude in metres. The first station of a path is its foot
and the last is its top.

Between one station and the next the path is taken to rise evenly, so the
altitude of a place between two stations is got from theirs in proportion to
its distance from each.

## Surfaces

`surfaces.csv` schedules each path's surface, stretch by stretch, by distance
from the foot in metres: tarmac, stone dust, or the old ballast. A place exactly
where the surface changes takes the surface of the stretch beyond it.

## The walk

The wheel is set to nought at the foot of the path and pushed to the top
without being lifted. Its logger writes a line every ten seconds, the time of
day and the distance the wheel has rolled so far in metres; `wheel/` has one
log for each path, named for it.

The fieldworker stops wherever a probe is to be taken, pushes the probe into
the path bed beside the wheel, and speaks the soil depth into the recorder. The
recorder stamps the reading with the time of day; it and the logger were set
from the same watch each morning. `readings.csv` has every reading: its number,
its path, the time it was spoken and what was said. A reading's place is where
the wheel stood when it was spoken.

`paths.csv` gives, for each path, who walked it and the time of day the walk
began, which is the time of the log's first line.

## Measures

The study works in metres. A foot is 0.3048 m and a mile is 1609.344 m.
