# Counter commission: how the accounts office reckons it

## The books

`order_book.csv` is the quarter's order book from the counter system: the order
number, the date, the login of the terminal the order was written up on, what
the clerk wrote, and the net value. `clerks.csv` gives each clerk's login.
`credit_notes.csv` has the quarter's credit notes: the date, the clerk who
signed the note, the order it is against, what the clerk wrote, and the net
value credited.

The books are exported just as the counter keeps them. Anything in them that
does not match this note is put right before commission is reckoned.

## The kind of order

A clerk begins what he or she writes with the kind of order - a trade account
order, a cash sale, a special order or plant hire - each in their own way of
putting it. `rates.csv` gives the commission each kind earns, as a percentage
of the net value.

## A clerk's month

An order earns its commission for the clerk who wrote it up, in the month of
the order's date. A credit note takes commission away from the clerk who signed
it, in the month of the credit note's date: the net value credited, at the rate
of the kind of order it is against. A clerk's commission for a month is the one
less the other, in pounds and pence.
