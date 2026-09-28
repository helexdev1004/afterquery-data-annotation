"""The graded checks."""
import grader


def test_a_plan_was_written():
    lines, why = grader.plan_lines()
    assert lines is not None, why


def test_every_line_is_right():
    wrong, total, remarks = grader.lines_wrong()
    print("WRONG %d of %d" % (wrong, total))
    assert wrong == 0, "\n".join(remarks)
