"""Account reads and writes.

Two ways to read an account, and the difference matters:

  `get`             a plain read. The row can change underneath you before the
                    transaction commits.
  `get_for_update`  takes the row lock, so nothing else may change that account
                    until the surrounding transaction ends.

Anything that decides something about an account and then acts on it wants the
second one. A plain read is only safe when the answer is being handed straight
back to the caller.
"""

from __future__ import annotations

COLUMNS = "id, pool_id, balance, status"


async def get(conn, account_id: int):
    return await conn.fetchrow(
        f"SELECT {COLUMNS} FROM accounts WHERE id = $1", account_id
    )


async def get_for_update(conn, account_id: int):
    return await conn.fetchrow(
        f"SELECT {COLUMNS} FROM accounts WHERE id = $1 FOR UPDATE", account_id
    )


async def lock_pair(conn, first_id: int, second_id: int) -> dict:
    """Lock two accounts, lowest id first.

    The ordering is the whole point. Two transfers moving money in opposite
    directions between the same pair take the same two locks; if each grabbed
    its own source first they would hold one lock apiece and wait forever for
    the other, and PostgreSQL would break the cycle by killing one of them.
    Sorting the ids means both queue on the same row and neither deadlocks.

    Returns the rows keyed by account id, so the caller does not have to
    remember which of the two came back first.
    """
    low, high = sorted((first_id, second_id))
    rows = {}
    for account_id in (low, high):
        row = await get_for_update(conn, account_id)
        if row is not None:
            rows[row["id"]] = row
    return rows


async def adjust_balance(conn, account_id: int, delta: int) -> None:
    await conn.execute(
        "UPDATE accounts SET balance = balance + $1 WHERE id = $2", delta, account_id
    )


async def mark_closed(conn, account_id: int) -> None:
    await conn.execute(
        "UPDATE accounts SET status = 'closed' WHERE id = $1", account_id
    )
