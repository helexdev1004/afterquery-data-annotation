"""The graded checks."""

import pytest

import grader


@pytest.fixture(scope="session")
def result():
    return grader.grade()


def test_report_exists(result):
    right, total, wrong = result
    assert not any("no report was left" in w or "not readable" in w
                   for w in wrong), wrong[0]


def test_inspection_report_is_correct(result):
    right, total, wrong = result
    detail = "\n".join("  " + w for w in wrong[:25])
    assert right >= grader.PASS_MARK, (
        f"{right} of {total} callouts were reported correctly; "
        f"{grader.PASS_MARK} are required.\n" + detail
    )
