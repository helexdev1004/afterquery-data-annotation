"""The journal.

Every movement of money is two rows here - a negative one on the account the
money left and a positive one on the account it arrived at - so the journal is
the record and the cached balance on `accounts` is a convenience. The two must
always agree.

`daily_debits` is the one read in this module that is not about a single
transfer: it aggregates everything a pool has sent out since midnight, which is
what the daily limit is measured against.
"""

from __future__ import annotations

DAILY_DEBITS_SQL = """
    SELECT COALESCE(-SUM(e.amount), 0)::bigint
    FROM entries e
    JOIN accounts a ON a.id = e.account_id
    WHERE a.pool_id = $1
      AND e.amount < 0
      AND e.created_at >= date_trunc('day', now())
"""


async def daily_debits(conn, pool_id: int) -> int:
    """Total sent out of this pool since midnight, as a positive number.

    Aggregated over the journal rather than kept as a running total on the pool
    row, so it is always consistent with the entries that actually exist.
    """
    return await conn.fetchval(DAILY_DEBITS_SQL, pool_id)


async def legs_of(conn, transfer_id: str):
    return await conn.fetch(
        "SELECT account_id, amount FROM entries WHERE transfer_id = $1", transfer_id
    )


async def write_pair(conn, transfer_id: str, source_id: int,
                     destination_id: int, amount: int) -> None:
    """Write the two halves of one movement."""
    await conn.execute(
        "INSERT INTO entries (transfer_id, account_id, amount) VALUES ($1, $2, $3)",
        transfer_id, source_id, -amount,
    )
    await conn.execute(
        "INSERT INTO entries (transfer_id, account_id, amount) VALUES ($1, $2, $3)",
        transfer_id, destination_id, amount,
    )


async def write_leg(conn, transfer_id: str, account_id: int, amount: int) -> None:
    await conn.execute(
        "INSERT INTO entries (transfer_id, account_id, amount) VALUES ($1, $2, $3)",
        transfer_id, account_id, amount,
    )
