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
