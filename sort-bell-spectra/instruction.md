A founder's analyser tapes came back with their labels lost. Work out what each
run was of, and write up where the ring now stands.

`/app/logs` holds the tapes. A run starts with a `* RUN` line giving its id and
its peaks follow, one `PEAK` line each, in Hz. The tapes are in no order and do
not say when a run was taken or what it was of. A bell went back on the lathe
several times, and many of the runs are of other work that was on the bench at
the time. `/app/daybook.csv` is the workshop book: a date and a run id for
every run, and a bell for some of them, entered by hand.

The ring is eight bells, tuned true-harmonic: the five tuned partials stand at
fixed fractions of the bell's own nominal - the hum at a quarter, the prime at
a half, the tierce at three fifths, the quint at three quarters. Measure
against those exact ratios. Campanology also reads the same intervals in equal
temperament, which puts the tierce about sixteen cents lower; that is not the
convention graded here.

Write `/app/attribution.json`, naming every run on the tapes - the bell it was
of, or `other` if it was not this ring's work:

    {"S001": "bell-03", "S002": "other", "S003": "bell-01"}

Write `/app/tuning.json`, where each bell now stands:

    [{"bell": "bell-01", "in_true": true,
      "partials": [{"partial": "hum", "cents": 1.2, "in_true": true},
                   {"partial": "prime", ...}, ...]}]

Eight bells, `bell-01` the lightest through `bell-08` the heaviest, five
partials each, named hum, prime, tierce, quint and nominal. `cents` is how far
that partial stands from where it should, positive if sharp, measured against
the bell as it is now. The nominal is what the other four are measured from,
not a pitch the ring is held to, so its own figure is zero. A partial within
four cents of true is finished, and a bell is in true when all five are.

Every run named and every partial written up counts as one answer: one hundred
and forty two runs on the tapes and forty partials, one hundred and eighty two
in all. One hundred and seventy one have to be right. Partials are checked to two
cents, in both the figure and the verdict.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
