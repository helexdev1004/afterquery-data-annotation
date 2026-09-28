# Assign forty excavation finds to their contexts

Produce `/app/contexts.csv`: the header `find,context` and one line for each of
the forty finds listed in `/app/to_phase.csv`, giving the four figure number of
the stratigraphic context that find was dug from, as the recording manual
numbers contexts. Thirty six of the forty must be right.

`/app/MANUAL.md` is the site recording manual. It gives the site datum, how a
find's offset and depth are measured and booked, how the section drawings were
drawn and digitised, how a context boundary runs between two digitised points,
how cut features are treated, how the two teams that dug each trench numbered
their contexts, and which context takes a find that lies on a boundary.

`/app/sections.csv` is the digitised section drawings: for each trench and each
of its two long sections, the top and bottom boundary of every context as a run
of points, each an offset along the drawing and a depth, in metres.

`/app/finds.csv` is the finds register: every small find from the site, with
the trench it came from, the section it was booked against, its offset and its
depth. `/app/trenches.csv` gives each trench, its supervisor, its length, the
depth of its temporary bench mark below site datum, and the point where its two
teams met.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
