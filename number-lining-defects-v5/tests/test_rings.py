"""The graded checks."""

import pytest

import grader


@pytest.fixture(scope="session")
def result():
    return grader.grade()


def test_an_answer_was_left(result):
    _, _, wrong = result
    assert not any("nothing was left" in item or "could not be read" in item
                   for item in wrong), wrong[0]


def test_the_rings_are_right(result):
    right, total, wrong = result
    detail = "\n".join("  " + item for item in wrong[:25])
    print("RIGHT %d of %d, enough %d" % (right, total, grader.ENOUGH))
    assert right >= grader.ENOUGH, (
        "%d of %d defects were filed under the right ring; %d are needed.\n%s"
        % (right, total, grader.ENOUGH, detail))
