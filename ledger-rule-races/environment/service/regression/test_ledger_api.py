"""API regression suite for the ledger service.

Single-threaded behavioural tests. Run them against a live service:

    pytest /app/service/regression -q

Each test reseeds a small fixture: two pools of two accounts, a 100000 cent
daily limit per pool, no journal history. Account ids follow devseed's layout,
pool P account K is P * 100 + K, so pool 1 holds 100 and 101 and pool 2 holds
200 and 201.

The grader runs its own sealed copy of this suite against the submitted service,
so passing a locally edited copy proves nothing.
"""

import os
import pathlib
import subprocess
import sys
import uuid

import httpx
import psycopg
import pytest

BASE_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8000")
DSN = os.environ.get("DATABASE_URL", "postgresql://ledger@127.0.0.1:5432/ledger")

# Found relative to this file rather than by absolute path, so the suite runs
# wherever the service directory happens to be.
DEVSEED = pathlib.Path(__file__).resolve().parent.parent / "devseed.py"

OPENING = 1_000_000
LIMIT = 100_000
POOL_1, POOL_2 = 100, 200


@pytest.fixture()
def seeded():
    subprocess.run(
        [sys.executable, str(DEVSEED),
         "--pools", "2",
         "--per-pool", "2",
         "--limit-cents", str(LIMIT),
         "--opening-cents", str(OPENING),
         "--empty-per-pool", "2",
         "--history", "0"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


def entry_count(transfer_id: str) -> int:
    with psycopg.connect(DSN) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM entries WHERE transfer_id = %s", (transfer_id,)
        ).fetchone()
    return int(row[0])


def journal_sum(account_id: int) -> int:
    with psycopg.connect(DSN) as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM entries WHERE account_id = %s",
            (account_id,),
        ).fetchone()
    return int(row[0])


def transfer(client, src: int, dst: int, amount: int, transfer_id: str | None = None):
    return client.post(
        "/transfer",
        json={
            "transfer_id": transfer_id or str(uuid.uuid4()),
            "source_account_id": src,
            "destination_account_id": dst,
            "amount_cents": amount,
        },
    )


def test_health(seeded):
    assert seeded.get("/health").json()["status"] == "ok"


def test_account_lookup(seeded):
    body = seeded.get(f"/accounts/{POOL_1}").json()
    assert body["account_id"] == POOL_1
    assert body["pool_id"] == 1
    assert body["balance_cents"] == OPENING


def test_unknown_account_is_404(seeded):
    assert seeded.get("/accounts/9999").status_code == 404


def test_pool_starts_with_nothing_spent(seeded):
    body = seeded.get("/pools/1").json()
    assert body["daily_limit_cents"] == LIMIT
    assert body["spent_today_cents"] == 0


def test_unknown_pool_is_404(seeded):
    assert seeded.get("/pools/9999").status_code == 404


def test_transfer_moves_money_and_writes_two_entries(seeded):
    transfer_id = str(uuid.uuid4())
    assert transfer(seeded, POOL_1, POOL_2, 25_000, transfer_id).status_code == 200
    assert seeded.get(f"/accounts/{POOL_1}").json()["balance_cents"] == OPENING - 25_000
    assert seeded.get(f"/accounts/{POOL_2}").json()["balance_cents"] == OPENING + 25_000
    assert entry_count(transfer_id) == 2
    assert journal_sum(POOL_1) == OPENING - 25_000
    assert journal_sum(POOL_2) == OPENING + 25_000


def test_spending_counts_toward_the_pool(seeded):
    assert transfer(seeded, POOL_1, POOL_2, 25_000).status_code == 200
    assert seeded.get("/pools/1").json()["spent_today_cents"] == 25_000
    # Receiving is not spending.
    assert seeded.get("/pools/2").json()["spent_today_cents"] == 0


def test_limit_applies_across_the_whole_pool(seeded):
    assert transfer(seeded, POOL_1, POOL_2, 25_000).status_code == 200
    # 25000 already gone from pool 1; 80000 more would take it over 100000,
    # even though it leaves from the pool's other account.
    over = str(uuid.uuid4())
    assert transfer(seeded, POOL_1 + 1, POOL_2, 80_000, over).status_code == 409
    assert entry_count(over) == 0
    assert seeded.get("/pools/1").json()["spent_today_cents"] == 25_000


def test_spending_exactly_to_the_limit_is_allowed(seeded):
    assert transfer(seeded, POOL_1, POOL_2, 25_000).status_code == 200
    assert transfer(seeded, POOL_1 + 1, POOL_2, 75_000).status_code == 200
    assert seeded.get("/pools/1").json()["spent_today_cents"] == LIMIT
    assert transfer(seeded, POOL_1, POOL_2, 1).status_code == 409


def test_insufficient_funds_is_409_and_writes_nothing(seeded):
    short = str(uuid.uuid4())
    assert transfer(seeded, POOL_1, POOL_2, OPENING * 10, short).status_code == 409
    assert entry_count(short) == 0
    assert seeded.get(f"/accounts/{POOL_1}").json()["balance_cents"] == OPENING


def test_same_account_is_400(seeded):
    assert transfer(seeded, POOL_1, POOL_1, 100).status_code == 400


def test_unknown_destination_is_404(seeded):
    assert transfer(seeded, POOL_1, 9999, 100).status_code == 404


def test_non_positive_amount_is_rejected(seeded):
    assert transfer(seeded, POOL_1, POOL_2, 0).status_code == 422


def test_reversal_puts_the_money_back(seeded):
    transfer_id = str(uuid.uuid4())
    assert transfer(seeded, POOL_1, POOL_2, 25_000, transfer_id).status_code == 200
    response = seeded.post(
        "/reversals", json={"reversal_id": str(uuid.uuid4()), "transfer_id": transfer_id}
    )
    assert response.status_code == 200
    assert seeded.get(f"/accounts/{POOL_1}").json()["balance_cents"] == OPENING
    assert seeded.get(f"/accounts/{POOL_2}").json()["balance_cents"] == OPENING


def test_a_transfer_can_only_be_reversed_once(seeded):
    transfer_id = str(uuid.uuid4())
    assert transfer(seeded, POOL_1, POOL_2, 10_000, transfer_id).status_code == 200
    first = seeded.post(
        "/reversals", json={"reversal_id": str(uuid.uuid4()), "transfer_id": transfer_id}
    )
    assert first.status_code == 200
    second = seeded.post(
        "/reversals", json={"reversal_id": str(uuid.uuid4()), "transfer_id": transfer_id}
    )
    assert second.status_code == 409
    assert seeded.get(f"/accounts/{POOL_1}").json()["balance_cents"] == OPENING


def test_reversing_an_unknown_transfer_is_404(seeded):
    response = seeded.post(
        "/reversals", json={"reversal_id": str(uuid.uuid4()), "transfer_id": "nope"}
    )
    assert response.status_code == 404


def test_an_empty_account_can_be_closed(seeded):
    empty = POOL_1 + 2  # devseed seeds --empty-per-pool accounts after the funded ones
    assert seeded.get(f"/accounts/{empty}").json()["balance_cents"] == 0
    assert seeded.post(f"/accounts/{empty}/close").status_code == 200
    assert seeded.get(f"/accounts/{empty}").json()["status"] == "closed"


def test_a_funded_account_cannot_be_closed(seeded):
    assert seeded.post(f"/accounts/{POOL_1}/close").status_code == 409
    assert seeded.get(f"/accounts/{POOL_1}").json()["status"] == "open"


def test_a_closed_account_takes_no_more_money(seeded):
    empty = POOL_1 + 2
    assert seeded.post(f"/accounts/{empty}/close").status_code == 200
    assert transfer(seeded, POOL_2, empty, 100).status_code == 409
    assert seeded.get(f"/accounts/{empty}").json()["balance_cents"] == 0
