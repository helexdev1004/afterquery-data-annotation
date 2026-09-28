"""The graded checks.

Both datasets are scored. The visible one is the dataset the agent was given
along with its expected output, so a query rewritten to fit the hidden shape
fails here; the hidden one is what makes a query repaired only until the
visible diff went clean fail there.
"""

import pytest

import grader


@pytest.fixture(scope="session")
def scores():
    return grader.run_all()


def _report(results):
    bad = {n: p for n, p in results.items() if p}
    return "\n".join(f"  {n}: {p}" for n, p in sorted(bad.items()))


@pytest.mark.parametrize("dataset", list(grader.DATASETS))
def test_ported_queries_reproduce_the_originals(scores, dataset):
    results = scores[dataset]
    matched = sum(1 for problem in results.values() if problem is None)
    assert matched >= grader.PASS_MARK, (
        f"{matched} of {len(results)} queries reproduced the original result on "
        f"the {dataset} dataset; {grader.PASS_MARK} are required.\n"
        + _report(results)
    )


def test_every_query_was_delivered(scores):
    missing = sorted(
        name for name, problem in scores["visible"].items()
        if problem and "missing from" in str(problem)
    )
    assert not missing, (
        "these queries were not left in /app/ported: " + ", ".join(missing)
    )
