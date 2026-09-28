# Gauging stations: from logged stage to monthly runoff

## Stage

Each station has a pressure logger that writes the stage every fifteen minutes:
the time, and the water level in metres above the station's gauge datum.
`stage_logs/` has the quarter's files, and `field_sheet.csv` is the download
sheet that says which file came from which station.

The loggers are of several ages and were set up by different field staff. A
file that is not as this section describes it is first put right; every
station's runoff is wanted.

## Discharge

`stations.csv` gives each station's control, its rating constants and its gauge
zero. The head is the stage less the gauge zero. At a station whose control is a
v-notch weir, the discharge in cubic metres a second is the coefficient times the head
raised to the power 2.5. At a station whose control is a natural riffle, it is
the coefficient times the head raised to the station's own exponent.

## Runoff

A reading's discharge is taken to hold for the fifteen minutes that follow it. A
month's runoff is the sum of those volumes over the readings in the calendar
month, in thousands of cubic metres.
