"""The graded checks."""

import pytest

import grader


@pytest.fixture(scope="session")
def result():
    return grader.grade()


def test_the_answer_exists(result):
    _, _, wrong = result
    assert not any("nothing was left" in w or "not readable" in w
                   for w in wrong), wrong[0]


def test_the_trial_numbers_are_right(result):
    right, total, wrong = result
    detail = "\n".join("  " + w for w in wrong[:25])
    assert right >= grader.PASS_MARK, (
        f"{right} of {total} trial numbers were right; "
        f"{grader.PASS_MARK} are required.\n" + detail
    )
