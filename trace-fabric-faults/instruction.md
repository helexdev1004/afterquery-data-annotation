# Which panels did the flagged faults end up in?

A customer has returned upholstery covers with weaving faults in them, and the
cutting room has to say which cut panels were affected before the rest of the
order ships. The mill flagged every fault when it inspected the rolls; the
cutting room has the cut plan for every roll it laid up. Nobody has yet put the
two together.

Everything you need is under `/app`:

- `PROCEDURE.md` - the cutting room's written procedure: how the mill books a
  fault's place on a roll, how a roll is laid up on a table, how a cut plan is
  drawn and its panels numbered, and what happens to a fault that sits exactly
  on a cut line.
- `inspection.csv` - the mill's fault reports for fifteen rolls.
- `cutplans.csv` - every panel cut from those rolls, with its place in the lay.
- `rolls.csv` - each roll's inspector, length, width, the pieces it was joined
  from, and its cutting table.
- `recall.txt` - the fault numbers the customer's complaint comes down to.

Write `/app/recall.json`: a single JSON object whose keys are the fault numbers
in `recall.txt` and whose values are the panel each fault was cut into, written
the way `cutplans.csv` writes panels (`R07-P012`). The recall is only useful if
it is nearly all right: it is accepted when no more than four of the faults are
traced to the wrong panel.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
