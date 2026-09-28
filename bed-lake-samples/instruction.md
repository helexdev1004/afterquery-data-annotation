# Which bed did each sediment sample come from?

The lake-core project has forty geochemistry samples whose results are in, and
the paper needs each one placed in the bed it was cut from, by the bed's number
down the hole, with the core scanner's grain reading at the sample. The beds were logged when the core sections were split; the
samples were cut later, from the archive halves, by people who only wrote down
the section and how far along it they cut.

You will find these under `/app`:

`CORING.md` - the project's coring and curation note: how a hole was cored in
sections, how a section is labelled and measured, how beds were logged and how
they are numbered down a hole, how a sample's place was booked, and which bed
takes a sample cut exactly on a bed boundary.

`sections.csv` - every core section, who curated it, its length and the depth
of its top. `scan.csv` - the core scanner's track of every section. `beds.csv`
- the bed log. `samples.csv` - every sample ever cut, with the section and the
place booked for it. `paper.txt` - the forty samples the paper uses.

Write `/app/beds_for_paper.md`: a three-column Markdown table, sample, bed and
the scanner's grain index at the sample, one row for each sample in
`paper.txt`, the bed written as the project numbers beds, like `H9-B001`. A
row is right when both the bed and the index are. It is good enough to send
to the co-authors if at most four rows are wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
