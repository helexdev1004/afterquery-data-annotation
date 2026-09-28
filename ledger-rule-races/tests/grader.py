"""Sealed grader for the ledger transfer task.

Runs entirely inside the verifier container. Boots its own PostgreSQL, seeds its
own data, launches the submitted service as an unprivileged user with a fixed
deployment shape, and drives three sealed workloads:

  * functional  - single-threaded behavioural checks on the API contract
  * contention  - repeated concurrent rounds against a small set of pools, with
                  the ledger invariants and the daily pool limit checked
                  directly against the database, plus the server's own deadlock
                  counter
  * granularity - every client spends from its own pool while pg_stat_activity
                  is sampled, so a solution that serialises unrelated pools is
                  visible without timing anything

Nothing here reads agent-writable state except the service source itself.
"""

from __future__ import annotations

import os
import random
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field

import httpx
import psycopg

SERVICE_DIR = "/app/service"
DSN = "postgresql://ledger@127.0.0.1:5432/ledger"
BASE_URL = "http://127.0.0.1:8000"
POSTGRES_LOG = "/logs/verifier/postgres.log"

OPENING_CENTS = 10_000_000
POOL_DAILY_LIMIT = 200_000
# Spending pools are wide on purpose. With only a handful of accounts per pool,
# concurrent transfers keep colliding on the same account rows, which serialises
# them by accident and hides the defect being graded.
SPENDER_POOLS = (1, 2)
ACCOUNTS_PER_POOL = 24
SINK_POOL = 9
SINK_ACCOUNTS = 32
# Accounts seeded empty, so they are eligible to be closed while traffic is
# still trying to credit them.
CLOSE_POOL = 8
CLOSE_ACCOUNTS = 24
REVERSALS_PER_TRANSFER = 3
REVERSAL_TARGETS = 40
# Prior-day journal rows per spending account, in netting debit/credit pairs.
# The daily total is an aggregate over the journal, so its cost grows with the
# journal, which is what makes the read-then-write window wide enough to be a
# real defect rather than a microsecond of luck.
HISTORY_ROWS_PER_ACCOUNT = 1_200
CONTENTION_ROUNDS = 6
CONTENTION_TRANSFERS = 600
CONTENTION_CONCURRENCY = 16
MIN_AMOUNT = 5_000
MAX_AMOUNT = 20_000

# A solution that simply refuses traffic keeps every invariant. Each pool has to
# actually get most of its daily allowance spent.
UTILISATION_FLOOR = 0.60

# Wall-clock budget per contention round. A correct solution finishes a round in
# seconds; one that deadlocks and retries spends a full deadlock_timeout per
# cycle and would otherwise run for hours, blowing the verifier timeout and
# turning a clean verdict into a timeout.
CONTENTION_ROUND_BUDGET = 180.0

DISJOINT_CLIENTS = 32
DISJOINT_PER_CLIENT = 80
BULK_LIMIT = 10_000_000_000
BULK_AMOUNT = 100

SAMPLE_INTERVAL = 0.02
BLOCKED_BACKENDS = 3
LOCK_WAIT_SHARE_CEILING = 0.10

# The disjoint-progress probe. One account is held under a row lock for
# HOLD_SECONDS; a transfer on an unrelated pool must finish within
# DISJOINT_PROGRESS_CEILING. The reference answers in about 0.05 s, so the
# ceiling sits two orders of magnitude above a legitimate solution and well
# below the hold - nothing here is tuned to the hardware.
HOLD_SECONDS = 15.0
HOLD_SETTLE_SECONDS = 1.5
DISJOINT_PROGRESS_CEILING = 5.0

SERVICE_BOOT_TIMEOUT = 120

# The submitted service is executed under this account, never as root.
RUN_AS = os.environ.get("LEDGER_RUN_AS", "runner")

SPEND_TODAY_SQL = """
    SELECT p.id, p.daily_limit_cents,
           COALESCE(-SUM(e.amount) FILTER (WHERE e.amount < 0), 0)::bigint AS spent
    FROM pools p
    JOIN accounts a ON a.pool_id = p.id
    LEFT JOIN entries e ON e.account_id = a.id
         AND e.created_at >= date_trunc('day', now())
         AND e.transfer_id NOT LIKE 'genesis-%%'
    GROUP BY p.id, p.daily_limit_cents
"""


@dataclass
class Report:
    boot_error: str | None = None
    functional_failures: list[str] = field(default_factory=list)
    contention_violations: dict[int, list[str]] = field(default_factory=dict)
    server_errors: dict[int, dict[int, int]] = field(default_factory=dict)
    accepted_total: int = 0
    min_utilisation: float = 0.0
    deadlocks: int = 0
    deadlock_samples: list[str] = field(default_factory=list)
    stats_reset_moved: bool = False
    lock_wait_share: float = 0.0
    max_blocked_backends: int = 0
    busy_samples: int = 0
    disjoint_transfers: int = 0
    contention_error: str | None = None
    disjoint_while_held_seconds: float = 0.0
    disjoint_while_held_status: int = 0
    held_transfer_status: int = 0


# --------------------------------------------------------------------------
# environment
# --------------------------------------------------------------------------

def boot_postgres() -> None:
    subprocess.run(["/tests/pgboot.sh"], check=True, timeout=180)


def apply_schema() -> None:
    """Apply the submitted schema. Extra columns, indexes and constraints are
    the author's business; the grader only needs the contract columns."""
    with open(os.path.join(SERVICE_DIR, "schema.sql"), "r", encoding="utf-8") as handle:
        ddl = handle.read()
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS reversals CASCADE")
        conn.execute("DROP TABLE IF EXISTS entries CASCADE")
        conn.execute("DROP TABLE IF EXISTS accounts CASCADE")
        conn.execute("DROP TABLE IF EXISTS pools CASCADE")
        conn.execute(ddl)


def seed(
    pools: dict[int, tuple[int, list[int]]],
    opening: int = OPENING_CENTS,
    history_pools: tuple[int, ...] = (),
) -> None:
    """Seed pools and their accounts.

    Truncates rather than drops: dropping would change the relation OIDs and
    invalidate the running service's cached statements.

    `history_pools` get prior-day journal rows, inserted in matching debit and
    credit pairs so they net to zero and disturb no invariant. They are there
    because a daily total is computed over the journal, and a journal with
    history in it is what the query actually costs in a running system.
    """
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("TRUNCATE reversals, entries, accounts, pools RESTART IDENTITY CASCADE")
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO pools (id, daily_limit_cents) VALUES (%s, %s)",
                [(pool_id, limit) for pool_id, (limit, _) in pools.items()],
            )
            accounts = [
                (account_id, pool_id, opening)
                for pool_id, (_, account_ids) in pools.items()
                for account_id in account_ids
            ]
            cur.executemany(
                "INSERT INTO accounts (id, pool_id, balance) VALUES (%s, %s, %s)", accounts
            )
            cur.executemany(
                "INSERT INTO entries (transfer_id, account_id, amount) VALUES (%s, %s, %s)",
                [(f"genesis-{a}", a, opening) for a, _, _ in accounts],
            )
            if history_pools and HISTORY_ROWS_PER_ACCOUNT:
                cur.execute(
                    """
                    INSERT INTO entries (transfer_id, account_id, amount, created_at)
                    SELECT 'history-' || a.id || '-' || g.i,
                           a.id,
                           CASE WHEN g.i %% 2 = 0 THEN 250 ELSE -250 END,
                           now() - interval '3 days'
                    FROM accounts a
                    CROSS JOIN generate_series(1, %s) AS g(i)
                    WHERE a.pool_id = ANY(%s)
                    """,
                    (HISTORY_ROWS_PER_ACCOUNT, list(history_pools)),
                )


def contention_layout() -> dict[int, tuple[int, list[int]]]:
    """Two wide spending pools that share a daily limit, plus one sink pool that
    only ever receives, so the graded pressure is on the limit rather than on
    account row locks."""
    layout = {
        pool: (POOL_DAILY_LIMIT, [pool * 1000 + k for k in range(ACCOUNTS_PER_POOL)])
        for pool in SPENDER_POOLS
    }
    layout[SINK_POOL] = (BULK_LIMIT, [SINK_POOL * 1000 + k for k in range(SINK_ACCOUNTS)])
    layout[CLOSE_POOL] = (BULK_LIMIT, [CLOSE_POOL * 1000 + k for k in range(CLOSE_ACCOUNTS)])
    return layout


def empty_the_close_pool() -> None:
    """Leave the closable accounts at zero so they are eligible for closure
    while transfers are still being aimed at them."""
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("UPDATE accounts SET balance = 0 WHERE pool_id = %s", (CLOSE_POOL,))
        conn.execute(
            "UPDATE entries SET amount = 0 WHERE transfer_id LIKE 'genesis-%%' "
            "AND account_id IN (SELECT id FROM accounts WHERE pool_id = %s)",
            (CLOSE_POOL,),
        )


def disjoint_layout() -> dict[int, tuple[int, list[int]]]:
    layout: dict[int, tuple[int, list[int]]] = {}
    for index in range(DISJOINT_CLIENTS):
        layout[3000 + index] = (BULK_LIMIT, [300000 + index])
        layout[4000 + index] = (BULK_LIMIT, [400000 + index])
    return layout


def start_service() -> subprocess.Popen:
    """Run the submitted code as an unprivileged user.

    The log file is opened here, as root, and handed over as an inherited
    descriptor, so the service never needs write access to /logs/verifier. It
    therefore cannot create or replace reward.txt whatever it does.
    """
    env = dict(os.environ, DATABASE_URL=DSN, PYTHONUNBUFFERED="1", HOME="/home/runner")
    log = open("/logs/verifier/service.log", "wb")
    launch: dict = {}
    if RUN_AS and os.geteuid() == 0:
        launch["user"] = RUN_AS
    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000",
         "--workers", "3", "--log-level", "warning"],
        cwd=SERVICE_DIR,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        **launch,
    )
    deadline = time.time() + SERVICE_BOOT_TIMEOUT
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("service exited during startup; see service.log")
        try:
            if httpx.get(f"{BASE_URL}/health", timeout=5.0).status_code == 200:
                return process
        except Exception:
            time.sleep(1)
    raise RuntimeError("service did not become healthy within the boot timeout")


def stop_service(process: subprocess.Popen) -> None:
    """Stop the service and then sweep the account it ran under.

    Killing the process group is not enough on its own: anything the submitted
    code double-forked into a new session would survive it. Nothing owned by the
    service account may still be alive when the reward is written.
    """
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait(timeout=30)
    except Exception:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            pass

    if RUN_AS and os.geteuid() == 0:
        for flag in ("-TERM", "-KILL"):
            subprocess.run(["pkill", flag, "-u", RUN_AS], capture_output=True, check=False)
            time.sleep(1)


# --------------------------------------------------------------------------
# observation
# --------------------------------------------------------------------------

def server_day():
    """The database's own calendar day, which is what the daily cap is cut on."""
    with psycopg.connect(DSN) as conn:
        return conn.execute("SELECT current_date").fetchone()[0]


def deadlock_counter() -> int:
    """Cumulative deadlock count for this database, straight from the server's
    own statistics rather than parsed out of log text.

    Corroborated, never trusted alone: `pg_stat_reset()` sets it back to zero,
    and a submission that polls the counter and resets it whenever it moves
    reads as deadlock-free while deadlocking freely. The server's log cannot be
    rewritten that way, so `deadlock_log_hits` is the primary signal and
    `stats_reset_at` catches the reset itself.
    """
    with psycopg.connect(DSN) as conn:
        row = conn.execute(
            "SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()"
        ).fetchone()
    return int(row[0]) if row else 0


def stats_reset_at():
    """When this database's statistics were last reset.

    Nothing a legitimate solution does moves this. A submission calling
    pg_stat_reset() to launder the deadlock counter moves it every time.
    """
    with psycopg.connect(DSN) as conn:
        row = conn.execute(
            "SELECT stats_reset FROM pg_stat_database WHERE datname = current_database()"
        ).fetchone()
    return row[0] if row else None


def log_position() -> int:
    try:
        return os.path.getsize(POSTGRES_LOG)
    except OSError:
        return 0


def deadlock_log_hits(offset: int) -> list[str]:
    """Every 'deadlock detected' the server logged since `offset`.

    This is the graded signal. The log is opened by the verifier as root and
    lives under /logs/verifier, which the account the service runs as cannot
    write, so a submission can neither edit nor truncate it.
    """
    try:
        with open(POSTGRES_LOG, "r", encoding="utf-8", errors="replace") as handle:
            handle.seek(offset)
            return [line.rstrip() for line in handle if "deadlock detected" in line]
    except OSError:
        return []


def deadlock_samples_since(offset: int) -> list[str]:
    return deadlock_log_hits(offset)[:5]


def post_transfer(client: httpx.Client, transfer_id: str, src: int, dst: int, amount: int) -> int:
    try:
        return client.post(
            "/transfer",
            json={
                "transfer_id": transfer_id,
                "source_account_id": src,
                "destination_account_id": dst,
                "amount_cents": amount,
            },
        ).status_code
    except Exception:
        return 0


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def functional_checks() -> list[str]:
    """Single-threaded behaviour. A fix that breaks the API contract fails here."""
    failures: list[str] = []
    seed({1: (100_000, [101, 102]), 2: (100_000, [201])})
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:

        def expect(label: str, actual, wanted) -> None:
            if actual != wanted:
                failures.append(f"{label}: got {actual!r}, expected {wanted!r}")

        expect("health", client.get("/health").json().get("status"), "ok")
        expect("balance read", client.get("/accounts/101").json().get("balance_cents"), OPENING_CENTS)
        expect("pool on account", client.get("/accounts/101").json().get("pool_id"), 1)
        expect("unknown account read", client.get("/accounts/9999").status_code, 404)

        tid = str(uuid.uuid4())
        expect("accepted transfer", post_transfer(client, tid, 101, 201, 25_000), 200)
        expect("source debited", client.get("/accounts/101").json().get("balance_cents"), OPENING_CENTS - 25_000)
        expect("destination credited", client.get("/accounts/201").json().get("balance_cents"), OPENING_CENTS + 25_000)
        with psycopg.connect(DSN) as conn:
            rows = conn.execute(
                "SELECT account_id, amount FROM entries WHERE transfer_id = %s", (tid,)
            ).fetchall()
        expect("double entry written", sorted(rows), sorted([(101, -25_000), (201, 25_000)]))
        expect("pool usage reported", client.get("/pools/1").json().get("spent_today_cents"), 25_000)

        # 25000 already spent from pool 1 against a 100000 limit, so 80000 is over.
        over = str(uuid.uuid4())
        expect("over daily limit", post_transfer(client, over, 102, 201, 80_000), 409)
        with psycopg.connect(DSN) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM entries WHERE transfer_id = %s", (over,)
            ).fetchone()[0]
        expect("rejected transfer writes nothing", count, 0)
        expect("limit counts the whole pool",
               client.get("/pools/1").json().get("spent_today_cents"), 25_000)

        expect("exactly to the limit", post_transfer(client, str(uuid.uuid4()), 102, 201, 75_000), 200)
        expect("limit now fully used",
               client.get("/pools/1").json().get("spent_today_cents"), 100_000)
        expect("nothing more allowed", post_transfer(client, str(uuid.uuid4()), 101, 201, 1), 409)

        seed({1: (100_000, [101, 102]), 2: (100_000, [201])})
        short = str(uuid.uuid4())
        expect("insufficient funds", post_transfer(client, short, 101, 201, 99_000_000), 409)
        expect("same account rejected", post_transfer(client, str(uuid.uuid4()), 101, 101, 100), 400)
        expect("unknown destination rejected", post_transfer(client, str(uuid.uuid4()), 101, 9999, 100), 404)
        expect(
            "non-positive amount rejected",
            client.post("/transfer", json={
                "transfer_id": str(uuid.uuid4()),
                "source_account_id": 101,
                "destination_account_id": 201,
                "amount_cents": 0,
            }).status_code,
            422,
        )

        # --- reversal -----------------------------------------------------
        # A service that answered 409 to every reversal would keep every
        # invariant the contention rounds check, so the happy path is asserted
        # here as well as the once-only rule.
        seed({1: (100_000, [101, 102]), 2: (100_000, [201])})
        moved = str(uuid.uuid4())
        expect("transfer to reverse", post_transfer(client, moved, 101, 201, 20_000), 200)
        expect(
            "reversal accepted",
            post_reversal(client, str(uuid.uuid4()), moved),
            200,
        )
        expect("source restored", client.get("/accounts/101").json().get("balance_cents"), OPENING_CENTS)
        expect("destination restored", client.get("/accounts/201").json().get("balance_cents"), OPENING_CENTS)
        with psycopg.connect(DSN) as conn:
            legs = conn.execute(
                "SELECT COUNT(*) FROM entries WHERE transfer_id LIKE 'rev:%%'"
            ).fetchone()[0]
            recorded = conn.execute(
                "SELECT COUNT(*) FROM reversals WHERE transfer_id = %s", (moved,)
            ).fetchone()[0]
        expect("reversal wrote two journal rows", legs, 2)
        expect("reversal recorded once", recorded, 1)
        # Deliberately not asserted: whether a reversal frees the day's
        # allowance again. The instruction does not say either way, so grading
        # it would be inventing a rule the solver was never given.
        expect("second reversal refused",
               post_reversal(client, str(uuid.uuid4()), moved), 409)
        expect("unknown transfer cannot be reversed",
               post_reversal(client, str(uuid.uuid4()), "no-such-transfer"), 404)

        # --- closure ------------------------------------------------------
        # A service that never actually set status='closed' would also keep
        # every invariant, so closure is asserted to take effect.
        seed({1: (100_000, [101, 102]), 2: (100_000, [201])})
        with psycopg.connect(DSN, autocommit=True) as conn:
            conn.execute("UPDATE accounts SET balance = 0 WHERE id = 102")
            conn.execute(
                "UPDATE entries SET amount = 0 WHERE account_id = 102 "
                "AND transfer_id LIKE 'genesis-%%'"
            )
        expect("funded account cannot be closed",
               client.post("/accounts/101/close").status_code, 409)
        expect("funded account still open",
               client.get("/accounts/101").json().get("status"), "open")
        expect("empty account closes", client.post("/accounts/102/close").status_code, 200)
        expect("closure took effect",
               client.get("/accounts/102").json().get("status"), "closed")
        blocked = str(uuid.uuid4())
        expect("closed account takes no money in",
               post_transfer(client, blocked, 101, 102, 100), 409)
        expect("closed account takes no money out",
               post_transfer(client, str(uuid.uuid4()), 102, 101, 100), 409)
        with psycopg.connect(DSN) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM entries WHERE transfer_id = %s", (blocked,)
            ).fetchone()[0]
        expect("rejected transfer into closed account writes nothing", count, 0)
        expect("closed account still empty",
               client.get("/accounts/102").json().get("balance_cents"), 0)
        expect("closing a closed account is idempotent",
               client.post("/accounts/102/close").status_code, 200)
        expect("unknown account cannot be closed",
               client.post("/accounts/9999/close").status_code, 404)
    return failures


def check_invariants(
    accepted: dict[str, tuple[int, int, int]],
    rejected: set[str],
    unknown: set[str] = frozenset(),
) -> tuple[list[str], float]:
    """`unknown` are requests that never got an answer. The server may or may not
    have committed them, so their journal rows are neither expected nor
    forbidden; every other invariant still applies to them."""
    violations: list[str] = []
    with psycopg.connect(DSN) as conn:
        for account_id, balance, journal in conn.execute(
            """
            SELECT a.id, a.balance, COALESCE(SUM(e.amount), 0)
            FROM accounts a
            LEFT JOIN entries e ON e.account_id = a.id
            GROUP BY a.id, a.balance
            HAVING a.balance <> COALESCE(SUM(e.amount), 0)
            """
        ).fetchall():
            violations.append(
                f"account {account_id}: cached balance {balance} != journal sum {journal}"
            )

        for account_id, balance in conn.execute(
            "SELECT id, balance FROM accounts WHERE balance < 0"
        ).fetchall():
            violations.append(f"account {account_id}: negative balance {balance}")

        total = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM entries").fetchone()[0]
        opening = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM entries WHERE transfer_id LIKE 'genesis-%%'"
        ).fetchone()[0]
        if total != opening:
            violations.append(f"money not conserved: journal total {total} != {opening}")

        utilisation = 1.0
        for pool_id, limit, spent in conn.execute(SPEND_TODAY_SQL).fetchall():
            if spent > limit:
                violations.append(
                    f"pool {pool_id}: spent {spent} today against a daily limit of "
                    f"{limit}, over by {spent - limit}"
                )
            # Only the pools that are meant to spend say anything about whether
            # the service is refusing traffic to stay safe.
            if pool_id in SPENDER_POOLS and limit:
                utilisation = min(utilisation, spent / limit)

        for transfer_id, count in conn.execute(
            "SELECT transfer_id, COUNT(*) FROM reversals GROUP BY transfer_id "
            "HAVING COUNT(*) > 1"
        ).fetchall():
            violations.append(
                f"transfer {transfer_id} was reversed {count} times; a transfer may "
                "be reversed at most once"
            )

        for original, legs in conn.execute(
            """
            SELECT r.transfer_id, COUNT(e.id)
            FROM reversals r
            JOIN entries e ON e.transfer_id = 'rev:' || r.reversal_id
            GROUP BY r.transfer_id
            HAVING COUNT(e.id) <> 2
            """
        ).fetchall():
            violations.append(
                f"reversal of transfer {original} wrote {legs} journal rows, expected 2"
            )

        for account_id, balance in conn.execute(
            "SELECT id, balance FROM accounts WHERE status = 'closed' AND balance <> 0"
        ).fetchall():
            violations.append(
                f"account {account_id} is closed but still holds {balance}; money "
                "moved into it after it was closed"
            )

        rows = conn.execute(
            "SELECT transfer_id, account_id, amount FROM entries "
            "WHERE transfer_id NOT LIKE 'genesis-%%' AND transfer_id NOT LIKE 'history-%%' "
            "AND transfer_id NOT LIKE 'rev:%%'"
        ).fetchall()

    by_transfer: dict[str, list[tuple[int, int]]] = {}
    for transfer_id, account_id, amount in rows:
        by_transfer.setdefault(transfer_id, []).append((account_id, amount))

    for transfer_id, (src, dst, amount) in accepted.items():
        legs = by_transfer.get(transfer_id, [])
        if sorted(legs) != sorted([(src, -amount), (dst, amount)]):
            violations.append(
                f"accepted transfer {transfer_id}: journal legs {sorted(legs)} != "
                f"{sorted([(src, -amount), (dst, amount)])}"
            )

    for transfer_id in rejected:
        if transfer_id in by_transfer:
            violations.append(
                f"rejected transfer {transfer_id} wrote {len(by_transfer[transfer_id])} entries"
            )

    unexplained = set(by_transfer) - set(accepted) - set(unknown)
    for transfer_id in list(unexplained)[:5]:
        violations.append(f"transfer {transfer_id} wrote entries but was never accepted")

    return violations, utilisation


def contention_round(
    rng: random.Random, layout: dict[int, tuple[int, list[int]]]
) -> tuple[dict[int, int], dict[str, tuple[int, int, int]], set[str], set[str], int]:
    sinks = layout[SINK_POOL][1]
    plan: list[tuple[str, int, int, int]] = []
    for _ in range(CONTENTION_TRANSFERS):
        src_pool = rng.choice(SPENDER_POOLS)
        plan.append((
            str(uuid.UUID(int=rng.getrandbits(128))),
            rng.choice(layout[src_pool][1]),
            rng.choice(sinks),
            rng.randrange(MIN_AMOUNT, MAX_AMOUNT),
        ))

    statuses: dict[int, int] = {}
    accepted: dict[str, tuple[int, int, int]] = {}
    rejected: set[str] = set()
    unknown: set[str] = set()
    deadline = time.monotonic() + CONTENTION_ROUND_BUDGET

    import concurrent.futures

    def worker(chunk):
        out = []
        with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
            for transfer_id, src, dst, amount in chunk:
                if time.monotonic() > deadline:
                    break
                out.append((transfer_id, src, dst, amount,
                            post_transfer(client, transfer_id, src, dst, amount)))
        return out

    attempted = 0
    chunks = [plan[i::CONTENTION_CONCURRENCY] for i in range(CONTENTION_CONCURRENCY)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONTENTION_CONCURRENCY) as pool:
        for result in pool.map(worker, chunks):
            for transfer_id, src, dst, amount, code in result:
                attempted += 1
                statuses[code] = statuses.get(code, 0) + 1
                if code == 200:
                    accepted[transfer_id] = (src, dst, amount)
                elif code == 409:
                    rejected.add(transfer_id)
                elif code == 0:
                    unknown.add(transfer_id)

    return statuses, accepted, rejected, unknown, attempted


def post_reversal(client: httpx.Client, reversal_id: str, transfer_id: str) -> int:
    try:
        return client.post(
            "/reversals",
            json={"reversal_id": reversal_id, "transfer_id": transfer_id},
        ).status_code
    except Exception:
        return 0


def reversal_storm(accepted: list[str], rng: random.Random) -> dict[int, int]:
    """Reverse the same transfer from several clients at once. A transfer may be
    reversed once; asking three times concurrently must still move the money
    once."""
    import concurrent.futures

    targets = rng.sample(accepted, min(REVERSAL_TARGETS, len(accepted)))
    jobs = [
        (f"{transfer_id}-r{attempt}", transfer_id)
        for transfer_id in targets
        for attempt in range(REVERSALS_PER_TRANSFER)
    ]
    rng.shuffle(jobs)

    statuses: dict[int, int] = {}

    def worker(chunk):
        out = []
        with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
            for reversal_id, transfer_id in chunk:
                out.append(post_reversal(client, reversal_id, transfer_id))
        return out

    chunks = [jobs[i::CONTENTION_CONCURRENCY] for i in range(CONTENTION_CONCURRENCY)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONTENTION_CONCURRENCY) as pool:
        for codes in pool.map(worker, chunks):
            for code in codes:
                statuses[code] = statuses.get(code, 0) + 1
    return statuses


def closure_storm(layout: dict[int, tuple[int, list[int]]], rng: random.Random) -> dict[int, int]:
    """Close an empty account while money is still being aimed at it. An account
    that reports itself closed must not end up holding anything."""
    import concurrent.futures

    empties = layout[CLOSE_POOL][1]
    funders = layout[SINK_POOL][1]
    statuses: dict[int, int] = {}
    accepted: dict[str, tuple[int, int, int]] = {}
    unknown: set[str] = set()

    def worker(index: int):
        # Each account gets exactly one close and one incoming transfer, issued
        # at the same time: the first pass of indices closes, the second funds.
        account = empties[index % len(empties)]
        funder = funders[index % len(funders)]
        with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
            if index < len(empties):
                try:
                    return [(client.post(f"/accounts/{account}/close").status_code, None)]
                except Exception:
                    return [(0, None)]
            transfer_id = str(uuid.uuid4())
            code = post_transfer(client, transfer_id, funder, account, BULK_AMOUNT)
            return [(code, (transfer_id, funder, account, BULK_AMOUNT))]

    jobs = list(range(len(empties) * 2))
    rng.shuffle(jobs)
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONTENTION_CONCURRENCY) as pool:
        for results in pool.map(worker, jobs):
            for code, movement in results:
                statuses[code] = statuses.get(code, 0) + 1
                if movement is not None:
                    transfer_id, src, dst, amount = movement
                    if code == 200:
                        accepted[transfer_id] = (src, dst, amount)
                    elif code == 0:
                        unknown.add(transfer_id)
    return statuses, accepted, unknown


def _sample_lock_waits(stop_event, samples: list[tuple[int, int]]) -> None:
    """Poll the server's view of its own backends: how many are running, and how
    many are parked waiting for a lock."""
    with psycopg.connect(DSN) as conn:
        own_pid = conn.execute("SELECT pg_backend_pid()").fetchone()[0]
        while not stop_event.is_set():
            rows = conn.execute(
                """
                SELECT state, wait_event_type
                FROM pg_stat_activity
                WHERE datname = current_database()
                  AND pid <> %s
                  AND backend_type = 'client backend'
                """,
                (own_pid,),
            ).fetchall()
            running = sum(1 for state, wait in rows if state == "active" and wait != "Lock")
            blocked = sum(1 for _, wait in rows if wait == "Lock")
            samples.append((running, blocked))
            conn.commit()
            time.sleep(SAMPLE_INTERVAL)


def measure_lock_contention() -> dict:
    """Every client spends from its own pool into its own destination pool, so
    nothing shares an account or a pool and no transfer has any legitimate
    reason to wait.

    Deliberately not a timing measurement. One sequential client already
    saturates this service, so wall-clock throughput cannot separate a pool-wide
    or global lock from one that is scoped correctly; the server's own wait
    accounting can.
    """
    import concurrent.futures
    import threading

    seed(disjoint_layout())

    samples: list[tuple[int, int]] = []
    stop_event = threading.Event()
    sampler = threading.Thread(target=_sample_lock_waits, args=(stop_event, samples), daemon=True)
    sampler.start()

    completed = 0
    counter_lock = threading.Lock()

    def client_run(index: int) -> None:
        nonlocal completed
        src, dst = 300000 + index, 400000 + index
        done = 0
        with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
            for _ in range(DISJOINT_PER_CLIENT):
                if post_transfer(client, str(uuid.uuid4()), src, dst, BULK_AMOUNT) == 200:
                    done += 1
        with counter_lock:
            completed += done

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=DISJOINT_CLIENTS) as pool:
            list(pool.map(client_run, range(DISJOINT_CLIENTS)))
    finally:
        stop_event.set()
        sampler.join(timeout=10)

    busy = [(r, b) for r, b in samples if r or b]
    congested = sum(1 for _, blocked in busy if blocked >= BLOCKED_BACKENDS)
    return {
        "lock_wait_share": congested / len(busy) if busy else 1.0,
        "max_blocked_backends": max((b for _, b in samples), default=0),
        "busy_samples": len(busy),
        "disjoint_transfers": completed,
    }


def measure_disjoint_progress() -> dict:
    """Does work on one pool block unrelated work on another?

    The lock-wait sampler above only ever sees a backend parked in
    `wait_event_type = 'Lock'`, so it is blind to a gate that is not a database
    lock: serialise every request behind an asyncio lock or a file lock and the
    waiters queue in Python, where the server cannot see them, while the sampler
    reads a clean zero.

    So ask the question causally instead of statistically. A row lock is taken
    on one account from outside the service, which parks any transfer drawing on
    that account. While that transfer is parked, a transfer on a wholly disjoint
    pool is timed. Correct row-level locking lets it straight through. Any gate
    the whole service passes through is still held by the parked transfer, so
    the disjoint transfer queues behind it and takes the full hold.

    The separation is enormous - the reference answers in hundredths of a second
    against a ceiling of five - so this needs no hardware constant and no
    tuning. Sampling concurrent backends was tried first and abandoned: measured
    across runs of the same code it swung between a median of 2 and a median of
    11, which is far too noisy to gate on.
    """
    seed(disjoint_layout())
    held = {}

    def held_transfer():
        with httpx.Client(base_url=BASE_URL, timeout=HOLD_SECONDS + 60.0) as client:
            started = time.time()
            held["status"] = post_transfer(
                client, str(uuid.uuid4()), 300000, 400000, BULK_AMOUNT)
            held["seconds"] = time.time() - started

    result = {
        "disjoint_while_held_seconds": 0.0,
        "disjoint_while_held_status": 0,
        "held_transfer_status": 0,
    }

    with psycopg.connect(DSN) as holder:
        holder.execute("SELECT id FROM accounts WHERE id = 300000 FOR UPDATE")
        worker = threading.Thread(target=held_transfer, daemon=True)
        worker.start()
        time.sleep(HOLD_SETTLE_SECONDS)  # let it reach the row lock
        try:
            # Bounded deliberately. Under a global gate this request is waiting
            # on the very transaction this thread is holding, so an open-ended
            # timeout would deadlock the probe until the socket gave up. Giving
            # up just past the ceiling records the failure and moves on.
            with httpx.Client(base_url=BASE_URL,
                              timeout=DISJOINT_PROGRESS_CEILING + 2.0) as client:
                started = time.time()
                status = post_transfer(
                    client, str(uuid.uuid4()), 300001, 400001, BULK_AMOUNT)
                result["disjoint_while_held_seconds"] = time.time() - started
                result["disjoint_while_held_status"] = status
        finally:
            holder.rollback()

    worker.join(timeout=HOLD_SECONDS + 60.0)
    result["held_transfer_status"] = held.get("status", 0)
    return result


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------

def run_all() -> Report:
    report = Report()
    os.makedirs("/logs/verifier", exist_ok=True)

    entrypoint = os.path.join(SERVICE_DIR, "app", "main.py")
    if not os.path.isfile(entrypoint):
        report.boot_error = (
            f"{entrypoint} is missing; the submitted service source did not arrive "
            f"at {SERVICE_DIR}"
        )
        return report

    try:
        boot_postgres()
        apply_schema()
    except Exception as exc:
        report.boot_error = f"database setup failed: {exc}"
        return report

    try:
        process = start_service()
    except Exception as exc:
        report.boot_error = f"service failed to start: {exc}"
        return report

    try:
        try:
            report.functional_failures = functional_checks()
        except Exception as exc:
            report.functional_failures = [f"functional checks raised: {exc!r}"]

        layout = contention_layout()
        worst_utilisation = 1.0
        deadlock_offset = log_position()
        deadlocks_before = deadlock_counter()
        stats_reset_before = stats_reset_at()

        for round_index in range(1, CONTENTION_ROUNDS + 1):
            try:
                # The daily cap is defined against the server's calendar day, so
                # a round that runs across midnight is measured against a window
                # that moved underneath it. Detect that and take the round again;
                # a round lasts seconds, so this fires at most once per run.
                for _attempt in range(2):
                    day_at_start = server_day()
                    seed(layout, history_pools=SPENDER_POOLS)
                    empty_the_close_pool()
                    rng = random.Random(0xA5F0 + round_index)
                    statuses, accepted, rejected, unknown, _ = contention_round(rng, layout)
                    if accepted:
                        for code, count in reversal_storm(list(accepted), rng).items():
                            statuses[code] = statuses.get(code, 0) + count
                    closure_statuses, closure_accepted, closure_unknown = closure_storm(layout, rng)
                    for code, count in closure_statuses.items():
                        statuses[code] = statuses.get(code, 0) + count
                    accepted.update(closure_accepted)
                    unknown |= closure_unknown
                    # Only the service's own errors count. A request that never
                    # got an answer is ambiguous transport, and the invariants
                    # below already catch the dangerous version of it.
                    report.server_errors[round_index] = {
                        code: count for code, count in statuses.items() if code >= 500
                    }
                    violations, utilisation = check_invariants(accepted, rejected, unknown)
                    if server_day() == day_at_start:
                        break
                report.contention_violations[round_index] = violations
                report.accepted_total += len(accepted)
                worst_utilisation = min(worst_utilisation, utilisation)
            except Exception as exc:
                report.contention_violations[round_index] = [f"round raised: {exc!r}"]

            # Once a round is dirty the attempt has failed, and the remaining
            # rounds cost minutes without changing the verdict.
            if report.contention_violations[round_index]:
                break

        report.min_utilisation = worst_utilisation

        # The log is the graded signal; the counter only corroborates it. A
        # submission that resets the statistics to launder the counter reads
        # zero there but cannot touch the log, and moves stats_reset doing it.
        log_hits = deadlock_log_hits(deadlock_offset)
        counter_delta = max(0, deadlock_counter() - deadlocks_before)
        report.stats_reset_moved = stats_reset_at() != stats_reset_before
        report.deadlocks = max(counter_delta, len(log_hits))
        report.deadlock_samples = log_hits[:5]

        try:
            for key, value in measure_lock_contention().items():
                setattr(report, key, value)
        except Exception as exc:
            report.contention_error = f"lock contention measurement raised: {exc!r}"

        try:
            for key, value in measure_disjoint_progress().items():
                setattr(report, key, value)
        except Exception as exc:
            report.contention_error = (
                (report.contention_error or "")
                + f" disjoint progress probe raised: {exc!r}")
    except Exception as exc:
        report.boot_error = f"grading run failed: {exc!r}"
    finally:
        stop_service(process)

    return report
