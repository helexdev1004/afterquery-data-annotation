# Ring numbers for the lining defects

Forty defects from last year's walk-through inspection of the five bored
tunnels are going into the asset register, and the register files a defect
under the lining ring it is on, by the number painted on that ring at
construction, and the segment of that ring.

1. Read `/app/LINING.md`. It is the asset team's note on how the tunnels were
   driven and lined, how the rings were numbered and their segments lettered,
   how the joint survey and the walk-through inspection were taped and booked,
   and which ring takes a defect that sits on a joint.
2. The records are in `/app` beside it: `tunnels.csv` (each tunnel, its
   inspector, and how many rings each of its two drives built), `joints.csv`
   (the joint survey: where every ring joint falls along the survey tape) and
   `defects.csv` (the walk-through inspection: every defect, with where the
   inspector booked it).
3. `/app/wanted.txt` lists the forty defects the register needs.
4. Leave `/app/rings.tsv` behind: one line for each wanted defect, the defect
   number, a tab, and its ring and segment as the register writes them, like
   this:

       D0000	T9-A-0001-A

Thirty-six correct lines out of the forty are enough for the batch to be loaded.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
