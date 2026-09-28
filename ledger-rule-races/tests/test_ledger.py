"""Graded checks. Every one must pass for the reward to be 1."""

import pytest

import grader

REPORT = None


@pytest.fixture(scope="session", autouse=True)
def report():
    global REPORT
    if REPORT is None:
        REPORT = grader.run_all()
    return REPORT


def test_service_starts(report):
    assert report.boot_error is None, report.boot_error


def test_api_contract_preserved(report):
    assert report.functional_failures == [], "\n".join(report.functional_failures)


def test_no_server_errors_under_load(report):
    offenders = {
        round_index: codes for round_index, codes in report.server_errors.items() if codes
    }
    assert offenders == {}, (
        "transfers failed with 5xx or no response (an unhandled deadlock or "
        f"serialization failure counts here): {offenders}"
    )


@pytest.mark.parametrize("round_index", range(1, grader.CONTENTION_ROUNDS + 1))
def test_ledger_invariants_hold(report, round_index):
    violations = report.contention_violations.get(round_index)
    if violations is None:
        # Rounds stop at the first dirty one. A later round having no result is
        # only acceptable when an earlier round already failed and said why.
        dirty = [i for i, v in sorted(report.contention_violations.items()) if v]
        assert dirty, f"contention round {round_index} did not run"
        pytest.skip(f"stopped after round {dirty[0]} failed")
    assert violations == [], "\n".join(violations[:15])


def test_no_deadlocks_detected(report):
    assert report.deadlocks == 0, (
        f"PostgreSQL broke {report.deadlocks} lock cycle(s) during the contention "
        "rounds. Retrying a deadlock hides it from the client but it is still a "
        "deadlock.\n" + "\n".join(report.deadlock_samples)
    )


def test_database_statistics_were_not_reset(report):
    """The deadlock count is read from the server. Resetting the statistics
    zeroes it, so a service that polls pg_stat_database and calls
    pg_stat_reset() whenever the count moves looks deadlock-free while
    deadlocking freely. Nothing a real fix does touches this timestamp."""
    assert not report.stats_reset_moved, (
        "this database's statistics were reset while the task was being graded. "
        "The deadlock count is taken from pg_stat_database, so clearing it "
        "destroys the evidence rather than the deadlocks; the server's log is "
        "read as well and is what the deadlock result is actually based on"
    )


def test_pools_actually_spend_their_allowance(report):
    assert report.accepted_total > 0, "no transfer was ever accepted"
    assert report.min_utilisation >= grader.UTILISATION_FLOOR, (
        f"the least-used pool spent only {report.min_utilisation:.0%} of its daily "
        f"allowance; at least {grader.UTILISATION_FLOOR:.0%} is expected. Refusing "
        "traffic is not a way to keep the limit"
    )


def test_unrelated_pools_do_not_serialize(report):
    assert report.contention_error is None, report.contention_error
    assert report.disjoint_transfers > 0, (
        "no transfer between disjoint pools was accepted, so lock contention "
        "could not be measured"
    )
    assert report.busy_samples > 0, "the disjoint workload produced no observable activity"
    assert report.lock_wait_share < grader.LOCK_WAIT_SHARE_CEILING, (
        f"{report.lock_wait_share:.0%} of sampled moments had at least "
        f"{grader.BLOCKED_BACKENDS} backends waiting on a lock (peak "
        f"{report.max_blocked_backends}) while every client was spending from its "
        "own pool into its own destination pool. Transfers that share neither an "
        "account nor a pool must not wait for each other, so whatever guards the "
        "daily limit has to be scoped to the pool; the ceiling is "
        f"{grader.LOCK_WAIT_SHARE_CEILING:.0%}"
    )


def test_disjoint_work_proceeds_while_a_pool_is_held(report):
    """The sampler above watches for backends parked on a database lock, so it
    cannot see a gate that is not a database lock: serialise every request
    behind an asyncio lock or a file lock and the waiters queue inside the
    service, invisible to the server, while the sampler reads zero.

    This asks causally. One account is pinned under a row lock taken from
    outside the service, which parks any transfer drawing on it. A transfer on
    an unrelated pool is then timed. Correct row-level locking answers it in
    hundredths of a second; anything that funnels the whole service through one
    gate makes it wait for the pinned transfer instead."""
    assert report.held_transfer_status in (200, 0), (
        "the probe could not park a transfer behind a row lock, so disjoint "
        f"progress was not measured (held transfer answered "
        f"{report.held_transfer_status})"
    )
    assert report.disjoint_while_held_status == 200, (
        "a transfer between two pools that share nothing with the held account "
        f"answered {report.disjoint_while_held_status} rather than 200 while an "
        "unrelated account was locked. It should have been unaffected"
    )
    assert report.disjoint_while_held_seconds < grader.DISJOINT_PROGRESS_CEILING, (
        f"a transfer on an unrelated pool took "
        f"{report.disjoint_while_held_seconds:.1f}s while one account elsewhere "
        f"was held under a row lock; the ceiling is "
        f"{grader.DISJOINT_PROGRESS_CEILING:.0f}s and the reference answers in "
        "about 0.05s. Work on one pool is waiting for work on another, which "
        "means the service is funnelling every request through a single gate "
        "rather than locking what each transfer actually touches"
    )
