"""Run the submitted program on assay days it has not seen and mark its lines."""
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import marking                                                  # noqa: E402

PROGRAM = pathlib.Path("/app/activities.py")


@pytest.fixture(scope="module")
def tally():
    assert PROGRAM.is_file(), "no program at /app/activities.py"
    return marking.mark_program(PROGRAM)


def test_program_runs_on_every_day(tally):
    assert not tally["trouble"], "; ".join(tally["trouble"][:3])


def test_nine_lines_in_ten_are_right(tally):
    share = tally["right"] / tally["total"]
    print(json.dumps(tally["by_day"]))
    assert share >= marking.BAR, "%d of %d lines right (%.1f%%), %d%% needed" % (
        tally["right"], tally["total"], 100 * share, round(100 * marking.BAR))
