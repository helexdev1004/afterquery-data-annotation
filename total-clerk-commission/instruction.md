Quarterly commission for the sales desk

A builders' merchant pays its six counter clerks a quarterly commission on the
orders each of them wrote up, at a rate that depends on the kind of order. The
accounts assistant has the quarter's order book exported from the counter
system and needs each clerk's commission for each month of the quarter.

`/app/COMMISSION.md` is the accounts note on how an order is classed from what
the clerk wrote, which rate each class earns and how a clerk's month is
totalled. The order book is `/app/order_book.csv`, the credit notes are in
`/app/credit_notes.csv`, the commission rates in `/app/rates.csv`, and the
clerks and their counter logins in `/app/clerks.csv`.

The figures go in `/app/commission.csv` with the columns `clerk`, `month` and
`commission_gbp`, a line such as `Z. Example,2026-07,412.35`. A line is right
when the amount is within 0.50, and the payroll run will take the file if no
more than two of the eighteen lines are wrong.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
