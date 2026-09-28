"""The graded checks."""
import grader


def test_a_sheet_was_written():
    lines, fault = grader.sheet_lines()
    assert lines is not None, fault


def test_few_enough_lines_are_wrong():
    wrong, total, remarks = grader.lines_wrong()
    print("WRONG %d of %d, may be %d" % (wrong, total,
                                         grader.LINES_THAT_MAY_BE_WRONG))
    assert wrong <= grader.LINES_THAT_MAY_BE_WRONG, "\n".join(remarks)
