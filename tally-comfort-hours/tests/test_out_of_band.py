"""The graded checks."""
import grader


def test_a_result_was_written():
    lines, trouble = grader.result_lines()
    assert lines is not None, trouble


def test_enough_lines_are_accepted():
    out, total, notes = grader.lines_out()
    print("OUT %d of %d, may be %d" % (out, total, grader.LINES_THAT_MAY_BE_OUT))
    assert out <= grader.LINES_THAT_MAY_BE_OUT, "\n".join(notes[:30])
