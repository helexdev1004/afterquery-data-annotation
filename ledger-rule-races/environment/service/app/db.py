"""Connection pool and transaction helpers.

Everything that talks to PostgreSQL goes through here. The pool is created
lazily on first use rather than at import, because the module is imported by
each of the worker processes and by the reconciliation job, and only the ones
that actually serve traffic should open connections.
"""

from __future__ import annotations

import contextlib
import os
from typing import AsyncIterator

import asyncpg

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://ledger@127.0.0.1:5432/ledger"
)

MIN_POOL = 2
MAX_POOL = 12
COMMAND_TIMEOUT = 30

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=MIN_POOL,
            max_size=MAX_POOL,
            command_timeout=COMMAND_TIMEOUT,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@contextlib.asynccontextmanager
async def connection() -> AsyncIterator[asyncpg.Connection]:
    """A pooled connection with no transaction started.

    Use this for reads that do not have to agree with each other.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


@contextlib.asynccontextmanager
async def unit_of_work() -> AsyncIterator[asyncpg.Connection]:
    """A pooled connection inside one transaction.

    Every write path runs inside one of these, so a handler either commits
    everything it did or leaves the books untouched. Nothing below this module
    opens a transaction of its own; repositories take the connection they are
    given and assume a transaction is already open.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            yield conn
