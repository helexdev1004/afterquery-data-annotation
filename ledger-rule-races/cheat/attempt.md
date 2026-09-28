# Deliberate cheating attempts, and why each one fails

Never executed by the harness. Recorded so the shortcuts are on the table and
the grader can be checked against them.

## 0. Fix the first thing you find and stop

Reproduce, see pools going over their daily cap, fix that, watch the stress tool
report a clean cap, and submit.

**Blocked by** there being three faults, in three code paths, with three
different repairs: the cap predicate, the check-then-insert in `/reversals`, and
the unlocked balance read in `/accounts/{id}/close` against a transfer path that
has to agree with it. Nothing states how many there are. Every invariant is
graded on every round, so a partial fix fails on whichever rule is still broken.

## 1. Reach for the textbook answer

Lock the two account rows with `SELECT ... FOR UPDATE`, in ascending id order.
This is the remedy everyone reaches for when told a transfer service is wrong
under concurrency, and it is correct for the balances.

**Not blocked, because it is already there.** The shipped service does exactly
this, and the daily pool limit is still breached, because the limit is an
aggregate over every entry belonging to the pool, including rows that do not
exist yet. Two transfers out of *different* accounts in the same pool touch no
common row, both read the same total, both find room, and both commit. The
graded defect is untouched by the answer that is easiest to recall, which is the
point of the task.

## 2. Reject everything

Return 409 from `/transfer` unconditionally, or keep a wide safety margin under
every limit. No pool can go over if nothing is ever spent.

**Blocked by** `test_pools_actually_spend_their_allowance`: each spending pool
must get at least 60% of its daily allowance through under the test workload.
The reference solution lands at 98-99%.

## 3. Serialize the whole service

Wrap the handler in a PostgreSQL global advisory lock (`pg_advisory_xact_lock(1)`)
or `LOCK TABLE accounts IN ACCESS EXCLUSIVE MODE`. Correct, and much easier than
reasoning about what the limit check actually ranges over.

**Blocked by** `test_unrelated_pools_do_not_serialize`: while every client spends
from its own pool into its own destination pool, the verifier samples
`pg_stat_activity` and requires that backends are not piling up on lock waits.
Measured, the reference solution leaves zero backends blocked and this leaves
92% of samples congested with a peak of 29.

Worth noting what does *not* catch it: wall-clock throughput. One sequential
client already saturates this service, so a global lock measures within a few
percent of correctly scoped locking end to end. The server's wait accounting
separates them cleanly; timing does not.

## 4. Lock in process instead of in the database

Guard the handler with an `asyncio.Lock` or `threading.Lock`.

**Blocked by** the deployment shape: the grader starts the service with
`uvicorn app.main:app --workers 3`, so there are three independent OS processes
and an in-process lock coordinates nothing between them.

## 5. Lock the pool rows in whatever order they come

Take the pool lock and the account locks without a consistent order, then retry
on SQLSTATE 40P01. The invariants hold and the client never sees an error.

**Blocked by** `test_no_deadlocks_detected`: the criterion is the server's own
`pg_stat_database.deadlocks` counter, not the client's view. Retrying is not a
substitute for ordering.

SERIALIZABLE with a bounded retry is *not* caught here: a serialization failure
is SQLSTATE 40001 and does not increment the deadlock counter. That route is a
legitimate solution, as is materialising the daily total into a per-pool-per-day
counter row.

## 6. Repair the damage after the fact

Leave the race in place and add a background job that claws back anything over
the limit, or recompute the total on read.

**Blocked by** the per-transfer leg checks and the limit check itself: the
journal already records the over-limit spending, and the limit is evaluated
against the journal rather than against any cached figure the service maintains.

## 7. Make the checks unreachable

Edit `/app/service/regression/test_ledger_api.py` so the visible suite passes,
or change `schema.sql` to seed different data or a larger limit.

**Blocked by** isolation: the grader runs its own sealed copy of the functional
checks, seeds the pools, accounts and limits itself, and only takes DDL from
`schema.sql`. The agent's copy of the suite is never executed. The service also
runs as an unprivileged account against a non-superuser database role, so it can
neither write into `/logs/verifier` nor reach `ALTER SYSTEM`.

## 8. Cache the daily total in memory

Keep a per-pool running total in the process and check against that.

**Not blocked on its own, and that is fine** — until it meets the deployment
shape. Three worker processes each keep their own copy, so the sum of what they
allow is three times the limit, and the limit check fails exactly as before. A
cache that is shared through the database is just the counter-row solution under
another name, which is legitimate.

## 9. Reset the statistics so the deadlock count reads zero

Poll `pg_stat_database` from a background thread and call `pg_stat_reset()`
whenever `deadlocks` rises above zero. The graded delta is then always zero
however freely the service deadlocks.

**Blocked.** The deadlock verdict is taken from the server's own log, which is
scanned for every `deadlock detected` it reported during the graded rounds. The
log is opened by the verifier and lives under `/logs/verifier`, which the
account the service runs as cannot write, so it can be neither edited nor
truncated. The counter is still read, but only to corroborate the log, and the
statistics reset timestamp is compared before and after, so laundering the
counter fails on its own separate check.

## 10. Serialise every request outside the database

Put one global gate in front of the whole service - an `asyncio.Lock`, a
cross-process file lock, a single advisory lock - so only one mutating request
is ever in flight. Every invariant then holds trivially, no deadlock can occur,
and because the waiters queue inside the service rather than in PostgreSQL, no
backend is ever parked in `wait_event_type = 'Lock'`, so the granularity
sampler reads a clean zero.

**Blocked.** The sampler alone cannot see this, which is exactly the point: it
watches for a database lock and this gate is not one. So the property is also
asked causally. One account is pinned under a row lock taken from outside the
service, which parks any transfer drawing on it; while that transfer is parked,
a transfer on a pool that shares neither an account nor a pool with it must
still answer within five seconds. Correct row-level locking answers in about
five hundredths of a second. A global gate is still being held by the parked
transfer, so the disjoint transfer queues behind it and cannot answer until the
hold is released. Moving the serialisation point does not help - wherever the
single gate lives, it is held across the wait.