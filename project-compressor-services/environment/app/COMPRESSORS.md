# Compressor house: reading use from the power monitor

## The log

The power monitor has eight channels, each a current transformer on one
compressor's motor supply. `monitor_channels.csv` is the monitor's wiring
schedule: the channel, the compressor it is on, and the transformer's ratio.
Every ten seconds the monitor writes a line to `current_log.csv`: the time, and
for each channel the motor's line current in amps.

The monitor was fitted and set up channel by channel. A channel that is not
logged as this section says is first put into that form; every compressor is
planned.

## Running and starting

`asset_register.csv` gives each compressor's kind, rating and full-load amps.
A compressor is running on a line when its current is at least 20 per cent of
its full-load amps. Its running hours are its running lines, at ten seconds a
line. A start is a running line that follows a line on which it was not
running.

## When the next service is due

Screw compressors are serviced every 4000 running hours and piston compressors
every 6000 starts. The register gives the date of the last service and the
running hours or starts already used since then, up to the start of the log.
What is left of the interval after the logged fortnight is divided by the
fortnight's daily rate of use, rounded to whole days and counted on from the
day after the last line of the log; that day is the due date.
