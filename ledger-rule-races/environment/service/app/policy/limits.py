"""The daily outbound limit.

A pool may send out at most `daily_limit_cents` across all of its accounts
between midnight and midnight. The amount already sent is aggregated from the
journal, so the policy never has to trust a cached total.
"""

from __future__ import annotations

from ..errors import DailyLimitExceeded, UnknownPool
from ..repositories import entries, pools


async def remaining_today(conn, pool_id: int) -> int:
    """How much this pool may still send out today."""
    limit = await pools.daily_limit(conn, pool_id)
    if limit is None:
        raise UnknownPool()
    spent = await entries.daily_debits(conn, pool_id)
    return limit - spent


async def check_outbound(conn, pool_id: int, amount: int) -> None:
    """Raise unless this pool may still send `amount` out today."""
    if amount > await remaining_today(conn, pool_id):
        raise DailyLimitExceeded()
