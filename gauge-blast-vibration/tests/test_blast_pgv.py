"""The graded checks: the report must exist, and every station must be right."""
import pytest

import grader


def test_report_has_rows():
    assert grader.report_rows(), "/app/blast_pgv.csv is missing, empty or unreadable"


@pytest.mark.parametrize("station", sorted(grader.SEALED))
def test_station(station):
    found = grader.fault(station)
    assert found == "", found
