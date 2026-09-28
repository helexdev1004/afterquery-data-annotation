"""Consistency report, run out of band.

    python -m app.jobs.reconcile

Read-only. Says whether the books currently hang together: whether every cached
balance still equals the sum of that account's journal rows, whether anything
has gone negative, whether a closed account is still holding money, whether any
transfer has been reversed more than once, and how much each pool has sent out
today against its limit.

It reports; it does not repair. Run it after a load test to see whether the
ledger survived.
"""

from __future__ import annotations

import asyncio

from .. import db

DRIFT_SQL = """
    SELECT a.id, a.balance, COALESCE(SUM(e.amount), 0)::bigint AS journal
    FROM accounts a
    LEFT JOIN entries e ON e.account_id = a.id
    GROUP BY a.id, a.balance
    HAVING a.balance <> COALESCE(SUM(e.amount), 0)
    ORDER BY a.id
"""

NEGATIVE_SQL = "SELECT id, balance FROM accounts WHERE balance < 0 ORDER BY id"

CLOSED_WITH_MONEY_SQL = """
    SELECT id, balance FROM accounts
    WHERE status = 'closed' AND balance <> 0 ORDER BY id
"""

DOUBLE_REVERSED_SQL = """
    SELECT transfer_id, COUNT(*) AS times
    FROM reversals GROUP BY transfer_id HAVING COUNT(*) > 1
    ORDER BY transfer_id
"""

POOL_USAGE_SQL = """
    SELECT p.id, p.daily_limit_cents,
           COALESCE(-SUM(e.amount) FILTER (WHERE e.amount < 0), 0)::bigint AS spent
    FROM pools p
    LEFT JOIN accounts a ON a.pool_id = p.id
    LEFT JOIN entries e ON e.account_id = a.id
         AND e.created_at >= date_trunc('day', now())
    GROUP BY p.id, p.daily_limit_cents
    ORDER BY p.id
"""


async def main() -> int:
    problems = 0
    async with db.connection() as conn:
        for label, sql in (
            ("balance disagrees with the journal", DRIFT_SQL),
            ("negative balance", NEGATIVE_SQL),
            ("closed account still holding money", CLOSED_WITH_MONEY_SQL),
            ("transfer reversed more than once", DOUBLE_REVERSED_SQL),
        ):
            rows = await conn.fetch(sql)
            if rows:
                problems += len(rows)
                print(f"{label}: {len(rows)}")
                for row in rows[:10]:
                    print(f"    {dict(row)}")

        print("\npool usage today")
        for row in await conn.fetch(POOL_USAGE_SQL):
            over = " OVER LIMIT" if row["spent"] > row["daily_limit_cents"] else ""
            print(f"    pool {row['id']}: {row['spent']} of "
                  f"{row['daily_limit_cents']}{over}")
            if over:
                problems += 1

    print("\nclean" if not problems else f"\n{problems} problem(s)")
    await db.close_pool()
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
