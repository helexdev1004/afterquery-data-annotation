"""Pools.

A pool is a customer. Its accounts share one daily outbound limit, so the limit
is a property of the group and not of any single account in it.
"""

from __future__ import annotations

COLUMNS = "id, daily_limit_cents"


async def get(conn, pool_id: int):
    return await conn.fetchrow(
        f"SELECT {COLUMNS} FROM pools WHERE id = $1", pool_id
    )


async def daily_limit(conn, pool_id: int) -> int | None:
    return await conn.fetchval(
        "SELECT daily_limit_cents FROM pools WHERE id = $1", pool_id
    )


async def lock(conn, pool_id: int) -> int | None:
    """Take the pool row, so that spending against this pool's limit is
    serialised.

    The limit is a condition over rows that do not exist yet: two transfers out
    of two different accounts of the same pool touch no row in common, so no
    account lock orders them, and both can read the same day's total and both
    find room under the cap. Locking the pool row gives that condition
    something to queue on. Different pools still proceed in parallel, because
    they queue on different rows.
    """
    return await conn.fetchval(
        "SELECT id FROM pools WHERE id = $1 FOR UPDATE", pool_id
    )
