Comfort hours for the tenants' service-charge rebate

A landlord's lease gives each tenant of a mixed-use building a rebate on the
service charge for every occupied hour in which the tenant's zone was outside
the agreed temperature band. The managing agent is settling the last five weeks,
and needs, for each of the ten zones and each of the five weeks, the number of
occupied hours the zone spent out of band. The building management system
trended every zone's temperature throughout.

The agent's own note, `/app/COMFORT.md`, explains how zones are trended, what
counts as an occupied hour and when an hour is out of band. The lease schedule
of each zone's occupied hours is `/app/occupancy.csv`. The building management
system's point list, which says which trend belongs to which zone, is
`/app/points.csv`, and the trends themselves are in `/app/outstations/`, one
file for each outstation.

The result goes in `/app/out_of_band.csv`, with the columns `zone`, `week` and
`hours`, a line looking like `Z99,3,12.5`. A line is accepted when its hours
are within a quarter of an hour of the true figure, and the agent will settle
once no more than four of the fifty lines fall outside that.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
