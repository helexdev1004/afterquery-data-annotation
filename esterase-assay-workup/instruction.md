An insectary screens field-caught mosquitoes for raised esterase activity on 96-well plates, one mosquito to a well, and works up each assay day from the plate readers' exports. It wants that work-up as a program.

Write the program at `/app/activities.py`. It is run as `python3 /app/activities.py` with one assay day as JSON on standard input, and it prints one line for every mosquito on that day, the mosquito and its esterase activity in nmol a minute at 25 C, as in `M-000000 12.34`. Python 3 with numpy is what it will be run under, and nothing else.

`/app/ASSAY.md` is the insectary's note on how the plates are made up, what a day file holds and how a day is worked up. `/app/days/` holds three past assay days as they came off the readers.

The program is marked by running it on assay days it has not seen and setting its lines against the insectary's own figures for those days, which come from the arithmetic in the note applied to each plate the way it actually sat in the reader. A line is right when it is within 2 per cent of the insectary's figure for that mosquito, and nine lines in ten over all those days have to be right.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
