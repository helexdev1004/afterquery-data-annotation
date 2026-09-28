"""The graded checks."""

import pytest

import grader


@pytest.fixture(scope="session")
def result():
    return grader.grade()


def test_both_answers_exist(result):
    _, _, wrong = result
    assert not any("nothing was left at" in w or "not readable" in w
                   for w in wrong), wrong[0]


def test_the_answers_are_right(result):
    right, total, wrong = result
    detail = "\n".join("  " + w for w in wrong[:25])
    assert right >= grader.PASS_MARK, (
        f"{right} of {total} graded answers were right; "
        f"{grader.PASS_MARK} are required.\n" + detail
    )
