# The ledger stops holding its own rules under load

This service misbehaves under concurrent traffic and I can't chase it down.

It's in `/app/service` - routes in `app/api`, one module per use case in `app/services`, the rules in `app/policy`, every statement that touches the database in `app/repositories`. Double-entry ledger: every movement writes a debit and a matching credit into the journal, and each account carries a cached running balance. Accounts are grouped into pools, one pool per customer. Three rules the business cares about:

- a pool has a daily cap on how much can go out of it, counted across all of its accounts together
- an account can be closed once it's empty, and a closed account takes no more movement in either direction
- a transfer can be reversed, but only once

One request at a time, all of that behaves exactly as written. Under real traffic, ops keep finding pools over their cap, closed accounts still holding money, and transfers reversed twice. I don't know how many separate problems that is.

Sort it out so the ledger holds all its rules when requests overlap. Leave the fix in `/app/service`, that's what gets graded.

Keep the API as it is: `POST /transfer`, `POST /reversals`, `POST /accounts/{id}/close`, and the two GETs. 200 fine, 409 for a rule that says no, 400 same account both sides, 404 no such account, pool or transfer, 422 bad amount. Each is one operation: 200 means it's committed before you answer, a failure moves nothing. Don't push work onto a background queue and call that done.

When you're done, all of this should hold under load:

- no pool is ever over its daily cap, counting every debit from every account in that pool since midnight
- no closed account holds anything, and nothing moves in or out of one after it closes
- no transfer is reversed more than once, and a reversal writes exactly two journal rows
- the journal and the balances can't drift apart, and nothing goes negative
- the total money in the system doesn't change
- anything answered 200 wrote exactly its own rows, anything answered 409 wrote none
- nothing comes back 5xx
- no deadlocks at all. I read that off the server, not the client: `SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()` shouldn't move, and I read the server log too. Retrying one only hides it from the caller, it still counts, and clearing the statistics doesn't clear it. A serialization failure you retry yourself isn't a deadlock, that's fine.
- customers with nothing to do with each other still run at the same time. Two checks: while every client spends from its own pool into its own destination pool, fewer than 10% of my `pg_stat_activity` samples may show 3 or more backends in `wait_event_type = 'Lock'`; and with one account pinned under a row lock from outside the service, a transfer on an unrelated pool still has to answer within 5 seconds.
- don't get safe by being stingy. Each pool has to spend at least 60% of its daily allowance under the test workload, so refusing traffic isn't a fix.

Change the schema if you need to, just keep the pool, account, entry and reversal fields meaning what they mean today. Whatever you ship runs on the packages already in the image; nothing is installed at grading time.

It runs as `uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 3` and is graded that way, so don't move the module or rename the app. `DATABASE_URL` is set.

`ledger-up` brings it up, `ledger-up --restart` picks up your changes. `python /app/service/stress/stress.py --transfers 800 --concurrency 32` drives all three paths and reports what the API answered; it won't say whether the books balance, so check that yourself. `python -m app.jobs.reconcile` will. `psql "$DATABASE_URL"` is installed and the schema is in `/app/service/schema.sql`. Regression tests are in `/app/service/regression`.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
