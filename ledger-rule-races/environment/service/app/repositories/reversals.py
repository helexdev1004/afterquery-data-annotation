"""Reversal bookkeeping.

One row per reversal. A transfer may be reversed at most once, and this table
is where that is recorded.
"""

from __future__ import annotations


async def exists_for(conn, transfer_id: str) -> bool:
    count = await conn.fetchval(
        "SELECT COUNT(*) FROM reversals WHERE transfer_id = $1", transfer_id
    )
    return bool(count)


async def record(conn, reversal_id: str, transfer_id: str) -> None:
    await conn.execute(
        "INSERT INTO reversals (reversal_id, transfer_id) VALUES ($1, $2)",
        reversal_id, transfer_id,
    )
