# What the three defects are, and why each fix is the fix

Three separate races, one per use case. None of them is a lost update on an
account balance: the shipped code already locks both account rows in ascending
id order in `repositories/accounts.py::lock_pair`, which is correct, is used by
the transfer path, and the fix leaves it alone. That matters, because it is the
first thing anyone looks for and finding it already done is what makes the real
defects worth the search.

## 1. The daily pool limit - `services/transfers.py`

The limit aggregates over every entry belonging to the pool, **including entries
that have not been written yet**, so it is a condition rather than a set of
rows. Two transfers leaving two different accounts of the same pool share no
row, so no account lock orders them: both read the same day's total, both find
room under the cap, and both commit. The pool goes over its limit with every
row lock behaving exactly as documented.

The fix gives that condition something lockable - the pool row itself, taken
before the day's total is read. Spending within one pool is then serialised
while different pools stay independent, because they queue on different rows.

Which pool to lock is a property of the source account, so it has to be read
first. That read deliberately takes no lock: locking the account first and the
pool second would invert the lock order the rest of the service depends on. An
account never moves between pools - nothing in the API changes `pool_id` - so
the answer cannot go stale under the lock taken immediately after.

## 2. Reversing twice - `services/reversals.py`

"Reversed at most once" is decided by whether a row exists in `reversals`, and
a row that does not exist yet cannot be locked. Two reversals of one transfer
both look, both see nothing, and both write.

The fix locks the accounts the reversal is about, which two reversals of the
same transfer necessarily share, in ascending id order. The second one waits,
and by the time it looks the first has committed its row.

## 3. Closing an account that is being paid into - `services/accounts.py`

The emptiness check read the account with `accounts.get`, which takes no lock,
so a transfer could land between the check and the update and leave money
stranded on a closed account. `accounts.get_for_update` was already in the
repository and already used by the transfer path; the close path was simply
calling the wrong one.

## Lock order

Pool first, then account rows ascending. A transaction takes at most one pool
lock and always takes it before any account lock, so no cycle can form between
any two paths in this service and the server's deadlock counter never moves.

## What a wrong fix looks like

- **One global lock** - correct, and caught. Unrelated pools then wait on each
  other, which both the lock-wait sampler and the disjoint-progress probe see.
- **Unordered `SELECT ... FOR UPDATE` plus retry on deadlock** - answers every
  request correctly and still fails: the deadlock is read from the server's own
  log and from `pg_stat_database`, so retrying hides it from the caller only.
- **Refusing traffic** - caught by the utilisation floor; each pool still has to
  get at least 60% of its allowance through.
- **`SERIALIZABLE` with a bounded retry** - legitimate and passes. A 40001
  serialization failure is not a deadlock.
