"""The graded checks."""
import grader


def test_figures_were_written():
    lines, why = grader.figure_lines()
    assert lines is not None, why


def test_few_enough_lines_are_wrong():
    wrong, total, remarks = grader.lines_wrong()
    print("WRONG %d of %d, may be %d" % (wrong, total,
                                         grader.LINES_THAT_MAY_BE_WRONG))
    assert wrong <= grader.LINES_THAT_MAY_BE_WRONG, "\n".join(remarks)
