# Coring targets from the gradiometer survey

The corer goes out next week to forty magnetic anomalies, and for each one it
needs a single survey cell to aim at: the cell with the highest reading inside
that anomaly's search window.

Write the targets to `/app/targets.txt`, one anomaly to a line: its number, a
space, and the cell's reference in the form the survey specification uses.

    A00 E0435N0210

The list is usable if at least 36 of its 40 cells are the right ones.

What there is to work from, all of it in `/app`:

| file | what it holds |
| --- | --- |
| `SPEC.md` | the specification the survey was let to: grid and cell sizes, how a grid is walked and logged, how a grid's position is booked, how a cell is referenced, how a peak is defined |
| `dumps/` | the instrument's logger dump for each of the forty survey grids, readings in nanotesla, one to a line |
| `grids.csv` | the field sheets: who surveyed each grid, and its position |
| `anomalies.csv` | the forty anomalies, each with its search window in site eastings and northings |

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
