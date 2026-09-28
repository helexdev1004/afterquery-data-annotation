"""The graded checks."""
import grader


def test_the_sheet_exists_and_parses():
    sheet, wrong = grader.read_sheet()
    assert sheet is not None, wrong


def test_enough_runs_are_right():
    out, asked, lines = grader.runs_out()
    print("OUT %d of %d, may be %d" % (out, asked, grader.RUNS_THAT_MAY_BE_OUT))
    assert out <= grader.RUNS_THAT_MAY_BE_OUT, "\n".join(lines[:30])
