"""The graded checks."""

import pytest

import grader


@pytest.fixture(scope="session")
def scores():
    return grader.run_all()


def test_solution_module_exists():
    import pathlib
    assert pathlib.Path("/app/solution/adjust.py").is_file(), (
        "no adjustment was left at /app/solution/adjust.py"
    )


def test_networks_are_adjusted_correctly(scores):
    wrong = {name: why for name, why in scores.items() if why}
    correct = len(scores) - len(wrong)
    detail = "\n".join(f"  {name}: {why}" for name, why in sorted(wrong.items()))
    assert correct >= grader.PASS_MARK, (
        f"{correct} of {len(scores)} networks were adjusted correctly; "
        f"{grader.PASS_MARK} are required.\n" + detail
    )
