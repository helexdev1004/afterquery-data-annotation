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


def test_the_peaks_are_right(result):
    right, total, wrong = result
    detail = "\n".join("  " + item for item in wrong[:25])
    print("SCORE %d of %d, bar %d" % (right, total, grader.BAR))
    assert right >= grader.BAR, (
        "%d of %d peaks were located right; %d are required.\n%s"
        % (right, total, grader.BAR, detail))
