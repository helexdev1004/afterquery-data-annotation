Expected protein for the lab's pellet samples

A feed mill's quality lab caught pellet samples off its five presses over three
days and measured the crude protein of each. Before anyone can say whether a
sample was on specification, the lab needs the protein it should have had: the
as-fed crude protein of the formula that was running through that press when
the sample was caught, worked out from the formula's ingredients and the
ingredient assays. A sample is tagged with its press and the reading on the
press's tonnage counter, not with a time. The samples in question are listed
in `/app/samples.txt`.

The mill's own note, `/app/MILL.md`, explains how bins feed presses, how the
batching system books a bin's change of formula, how a press logs its tonnage,
how a sample is tagged, and how a formula's protein is reckoned. Which
finished-meal bin feeds which press is in `/app/routing.csv`. Every change of
formula booked to a bin is in `/app/bin_changes.csv`, each press's tonnage log
is in `/app/press_logs/`, the formulas are in `/app/formulas.csv` and the
ingredient assays in `/app/assays.csv`.

The lab wants a file `/app/expected_protein.csv` whose columns are `sample`,
`formula` and `protein_pct`, a line looking like `P9@1234.5,F000,17.25`. A
line is good when the formula is right and the protein is within 0.05, and the
lab will report once nine samples in ten are good.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
