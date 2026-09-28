Cut, fill and topsoil at forty cross-sections

Five short road schemes are going to tender and the quantity surveyor needs
earthworks figures at forty of their cross-sections before the bill can be
closed. The ground at every cross-section was levelled by one of five
surveyors, as offsets from the centreline with a level at each. The designer's
template - formation level, the widths either side and the side slopes - is
fixed for each scheme, and the land either side of each centreline is
scheduled by what grows on it, because the depth of topsoil to be stripped
first depends on that.

- `/app/EARTHWORKS.md` - the office's note: how a cross-section is booked, how
  the template sits on it, how topsoil strip is allowed for, and how the areas
  of cut and fill at a section are reckoned.
- `/app/schemes.csv` - the five schemes, who levelled each, and its template.
- `/app/sections/` - one file per scheme: every cross-section's offsets and
  levels as booked.
- `/app/formation.csv` - the formation level at every cross-section.
- `/app/land.csv` - what the land is, strip by strip, across each scheme.
- `/app/wanted.txt` - the forty cross-sections the quantity surveyor wants.

Write `/app/areas.csv` with the header `section,cut_m2,fill_m2,strip_m2` and one
row for each cross-section in `/app/wanted.txt`, for example
`S9/0120,14.2,3.6,5.1`. A row is right when all three areas are within 0.2 of
the true ones. The bill can be closed if at most four of the forty rows are
wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
