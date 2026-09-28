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


def test_the_faults_are_traced(result):
    missed, total, wrong = result
    detail = "\n".join("  " + item for item in wrong[:25])
    print("WRONG %d of %d, allowed %d" % (missed, total, grader.MAY_BE_WRONG))
    assert missed <= grader.MAY_BE_WRONG, (
        "%d of %d faults were traced to the wrong panel; no more than %d may "
        "be.\n%s" % (missed, total, grader.MAY_BE_WRONG, detail))
