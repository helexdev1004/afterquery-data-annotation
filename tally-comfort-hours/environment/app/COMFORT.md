# Comfort hours: how the managing agent reckons them

## Trends

The building management system has five outstations, and each trends two wall
sensors side by side in one file under `outstations/`: a line every two
minutes, the time as `YYYY-MM-DD HH:MM` and each sensor's reading in degrees
Celsius. `points.csv` is the system's point list, which gives the zone each
trend belongs to.

The outstations were commissioned at different times by different contractors. A
trend that cannot be what this note describes is corrected before it is used,
never left out.

## Occupied hours

`occupancy.csv` is taken from the leases: for each zone, the days its tenant
keeps and the hours kept on those days. A reading counts as occupied when its
time falls on a kept day at or after the opening time and before the closing
time.

## Out of band

The agreed band is 20.0 to 24.0 degrees Celsius, both ends inside the band. An
occupied reading outside the band counts as two minutes out of band. A zone's
figure for a week is the total of those, in hours. Weeks run Monday to Sunday,
and week 1 begins on Monday 2 November 2026.
