#!/usr/bin/env python3
"""Reset the development database: apply schema.sql, then seed pools/accounts.

Usage:
    python devseed.py                    # 2 pools, 16 funded accounts each
    python devseed.py --pools 8

Tables are created if missing and truncated otherwise, never dropped, so the
running service's connection pool keeps working across a reseed.

The grader seeds its own database with its own values; this script exists so
there is something to run the service against locally.
"""

import argparse
import asyncio
import os
import pathlib

import asyncpg

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://ledger@127.0.0.1:5432/ledger"
)
SCHEMA = pathlib.Path(__file__).with_name("schema.sql")


async def main(pools: int, per_pool: int, limit: int, opening: int, history: int,
               empty_per_pool: int) -> None:
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(SCHEMA.read_text())
        await conn.execute("TRUNCATE reversals, entries, accounts, pools RESTART IDENTITY CASCADE")

        await conn.executemany(
            "INSERT INTO pools (id, daily_limit_cents) VALUES ($1, $2)",
            [(p, limit) for p in range(1, pools + 1)],
        )

        accounts = []
        for p in range(1, pools + 1):
            for k in range(per_pool):
                accounts.append((p * 100 + k, p, opening))
            # A few accounts are seeded empty, so there is always something that
            # is eligible to be closed while traffic is still being aimed at it.
            for k in range(empty_per_pool):
                accounts.append((p * 100 + per_pool + k, p, 0))
        await conn.executemany(
            "INSERT INTO accounts (id, pool_id, balance) VALUES ($1, $2, $3)", accounts
        )
        await conn.executemany(
            "INSERT INTO entries (transfer_id, account_id, amount) VALUES ($1, $2, $3)",
            [(f"genesis-{a}", a, bal) for a, _, bal in accounts],
        )

        # Prior-day journal rows, in matching debit/credit pairs so they net to
        # zero. Real accounts have history, and the daily total is an aggregate
        # over the journal, so an empty table makes the service behave nothing
        # like it does in production.
        if history:
            await conn.execute(
                """
                INSERT INTO entries (transfer_id, account_id, amount, created_at)
                SELECT 'history-' || a.id || '-' || g.i,
                       a.id,
                       CASE WHEN g.i % 2 = 0 THEN 250 ELSE -250 END,
                       now() - interval '3 days'
                FROM accounts a
                CROSS JOIN generate_series(1, $1) AS g(i)
                """,
                history,
            )

        print(f"seeded {pools} pools x {per_pool} accounts, daily limit {limit}, "
              f"opening {opening}, {history} history rows per account")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pools", type=int, default=2)
    parser.add_argument("--per-pool", type=int, default=16)
    parser.add_argument("--limit-cents", type=int, default=200_000)
    parser.add_argument("--opening-cents", type=int, default=10_000_000)
    parser.add_argument("--empty-per-pool", type=int, default=6,
                        help="accounts seeded with a zero balance, eligible for closing")
    parser.add_argument("--history", type=int, default=4_000,
                        help="prior-day journal rows per account")
    args = parser.parse_args()
    asyncio.run(main(args.pools, args.per_pool, args.limit_cents,
                     args.opening_cents, args.history, args.empty_per_pool))
