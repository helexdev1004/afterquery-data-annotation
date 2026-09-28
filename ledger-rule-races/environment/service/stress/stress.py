#!/usr/bin/env python3
"""Load generator for the ledger.

Drives three overlapping workloads against a running service and reports what
the API said. It does not inspect the database and it does not tell you whether
the ledger is still consistent - work that out yourself, the same way you would
against a real system. `psql "$DATABASE_URL"` is installed.

  transfers  - N transfers at a fixed concurrency across the seeded pools
  reversals  - the same transfer reversed from several clients at once
  closures   - every empty account closed while money is still aimed at it

    python stress/stress.py                       # 400 transfers, concurrency 16
    python stress/stress.py --transfers 800 --concurrency 32
    python stress/stress.py --rounds 5            # reseed and repeat

Exit status is 0 unless the run itself could not be driven.
"""

import argparse
import asyncio
import os
import random
import subprocess
import sys
import uuid

import asyncpg
import httpx

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://ledger@127.0.0.1:5432/ledger"
)
BASE_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8000")


async def deadlock_count() -> int:
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        return await conn.fetchval(
            "SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()"
        )
    finally:
        await conn.close()


async def layout() -> tuple[dict[int, list[int]], list[int]]:
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch("SELECT id, pool_id, balance FROM accounts ORDER BY id")
    finally:
        await conn.close()
    by_pool: dict[int, list[int]] = {}
    empties: list[int] = []
    for row in rows:
        by_pool.setdefault(row["pool_id"], []).append(row["id"])
        if row["balance"] == 0:
            empties.append(row["id"])
    return by_pool, empties


async def run_round(transfers: int, concurrency: int, rng: random.Random) -> None:
    by_pool, empties = await layout()
    pools = sorted(by_pool)

    gate = asyncio.Semaphore(concurrency)
    statuses: dict[int, int] = {}
    accepted: list[str] = []

    def note(code: int) -> None:
        statuses[code] = statuses.get(code, 0) + 1

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:

        async def do_transfer(transfer_id, src, dst, amount):
            async with gate:
                try:
                    code = (await client.post("/transfer", json={
                        "transfer_id": transfer_id,
                        "source_account_id": src,
                        "destination_account_id": dst,
                        "amount_cents": amount,
                    })).status_code
                except Exception:
                    code = 0
            note(code)
            if code == 200:
                accepted.append(transfer_id)

        plan = []
        for _ in range(transfers):
            src_pool, dst_pool = rng.sample(pools, 2)
            plan.append((
                str(uuid.uuid4()),
                rng.choice(by_pool[src_pool]),
                rng.choice(by_pool[dst_pool]),
                rng.randrange(5_000, 20_000),
            ))
        await asyncio.gather(*(do_transfer(*item) for item in plan))
        print(f"  transfers: {dict(sorted(statuses.items()))}")

        statuses.clear()

        async def do_reversal(reversal_id, transfer_id):
            async with gate:
                try:
                    note((await client.post("/reversals", json={
                        "reversal_id": reversal_id,
                        "transfer_id": transfer_id,
                    })).status_code)
                except Exception:
                    note(0)

        targets = rng.sample(accepted, min(40, len(accepted))) if accepted else []
        jobs = [(f"{t}-r{i}", t) for t in targets for i in range(3)]
        rng.shuffle(jobs)
        if jobs:
            await asyncio.gather(*(do_reversal(*job) for job in jobs))
        print(f"  reversals: {dict(sorted(statuses.items()))}")

        statuses.clear()

        async def do_close(account):
            async with gate:
                try:
                    note((await client.post(f"/accounts/{account}/close")).status_code)
                except Exception:
                    note(0)

        async def do_fund(account, funder):
            async with gate:
                try:
                    note((await client.post("/transfer", json={
                        "transfer_id": str(uuid.uuid4()),
                        "source_account_id": funder,
                        "destination_account_id": account,
                        "amount_cents": 100,
                    })).status_code)
                except Exception:
                    note(0)

        funders = [a for ids in by_pool.values() for a in ids if a not in empties]
        work = []
        for index, account in enumerate(empties):
            work.append(do_close(account))
            work.append(do_fund(account, funders[index % len(funders)]))
        if work:
            await asyncio.gather(*work)
        print(f"  closures : {dict(sorted(statuses.items()))}")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transfers", type=int, default=400)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--pools", type=int, default=2)
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--no-reseed", action="store_true",
                        help="drive load against whatever is already in the database")
    args = parser.parse_args()

    for round_index in range(1, args.rounds + 1):
        if not args.no_reseed:
            subprocess.run(
                [sys.executable, "/app/service/devseed.py", "--pools", str(args.pools)],
                check=True,
                stdout=subprocess.DEVNULL,
            )
        print(f"round {round_index}/{args.rounds}")
        before = await deadlock_count()
        rng = random.Random(args.seed if args.seed is not None else round_index)
        await run_round(args.transfers, args.concurrency, rng)
        print(f"  deadlocks broken by the server: {await deadlock_count() - before}")

    print("\nLoad finished. Whether the ledger still holds its rules is not")
    print("something this tool decides - check the database.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
