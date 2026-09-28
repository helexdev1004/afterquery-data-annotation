# Blast monitoring: from a logger's file to peak ground velocity

## Stations and loggers

`stations.csv` lists the ten stations: the sensor, its kind (a broadband
seismometer or a 4.5 Hz geophone), its sensitivity in volts per metre per
second, the preamp gain in front of the logger and the distance from the shot
in metres. The sensors, gains and distances were checked on site by the survey
crew the day before the blast.

Every station has a 24-bit data logger on the vertical component, 100 samples
per second, and one count is 40 V / 2^24. A logger writes one file, named by
the logger's serial number. The first line gives the network and station code
the logger is configured with, the channel code (HHZ for a broadband sensor,
EHZ for a short-period one), the number of samples, the sample rate and the
start time; the samples follow in counts, six to a line. The loggers keep UTC.
Every file starts at 08:29:00 UTC and runs for 180 s, and the shot was fired at
08:30:00.000 UTC.

The loggers were configured by different people over several field seasons. A
file that does not follow this section is brought into line with it first;
every station is reported.

## Ground velocity

Ground velocity in metres per second is counts times volts per count, divided
by the sensitivity times the preamp gain. Both kinds of sensor are flat across
the band of the blast and no response correction is made.

## The peak

A file's rest level is the mean of its samples before the shot. The peak is
the largest departure from the rest level, either way, among the samples from
the shot onwards; the earliest if two are equal. `pgv_um_s` is that departure
as ground velocity in micrometres per second, to two decimals, and
`peak_time_s` is the time of that sample after the shot, to two decimals.
