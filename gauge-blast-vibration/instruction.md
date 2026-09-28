A university group had ten seismic stations out around a limestone quarry when a production blast was fired, five with broadband seismometers and five with short-period geophones. For the vibration report to the district the seismologist needs each station's peak vertical ground velocity from the blast, in micrometres per second, and how long after the shot the peak came.

How a data logger writes its file, how counts become ground velocity and how the peak and its time are taken are set out in `/app/BLAST.md`. `/app/stations.csv` lists the stations with their sensors, sensitivities, preamp gains and distances from the shot, and the loggers' files from the blast are in `/app/waveforms/`.

Write `/app/blast_pgv.csv` with the columns `station`, `pgv_um_s` and `peak_time_s`, one line per station, like `ST99,184.30,2.47`. A station is right when its velocity is within 1 per cent and its time within 0.02 s; the report is only accepted with all ten stations right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
