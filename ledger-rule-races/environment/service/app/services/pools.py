"""Pool reads.

Read-only. The daily figure is aggregated from the journal on every call, which
is the same number the limit is enforced against, so what a caller sees here
and what the transfer path decides on cannot drift apart.
"""

from __future__ import annotations

from .. import models
from ..errors import UnknownPool
from ..repositories import entries, pools


async def read(conn, pool_id: int) -> dict:
    row = await pools.get(conn, pool_id)
    if row is None:
        raise UnknownPool()
    spent = await entries.daily_debits(conn, pool_id)
    return models.pool_view(row, spent)
