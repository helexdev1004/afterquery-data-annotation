# Power budget: from the bench logger to bus power

## The board and the logger

`rails.csv` lists the eight rails: the nominal voltage, the regulator that
makes the rail from the 5.00 V bus (a buck converter or an LDO), the value of
the rail's current-sense resistor in milliohms and, for a buck converter, its
efficiency in per cent. The regulator types, sense resistors and efficiencies
are taken from the released schematic and bill of materials.

The logger has eight probe pairs, P1 to P8. `probe_map.csv` says which rail
each pair was clipped to. Each pair records two things every 10 ms: the rail's
voltage in volts (`Pn_v`) and the voltage across the rail's sense resistor in
millivolts (`Pn_sense_mv`), positive for current flowing into the load. There
is one recording per phase.

The logger's channels were set up by different people over the life of the
bench. A channel that does not follow this section is brought into line with
it first; every rail is budgeted in every phase.

## Current and bus power

A rail's current in amps at a sample is its sense voltage in millivolts divided
by its sense resistor in milliohms.

What the rail draws from the bus at that sample depends on its regulator. An
LDO passes the rail's current straight through from the bus, so the draw in
milliwatts is the current times 5.00 times 1000. A buck converter draws the
rail's own power over its efficiency: the rail's voltage times the current
times 1000, divided by the efficiency as a fraction.

## A phase

`mean_mw` for a rail in a phase is the mean of the draw over every sample of
that phase's recording, to two decimals.
