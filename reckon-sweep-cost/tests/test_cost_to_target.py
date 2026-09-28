"""The graded checks."""
import grader


def test_costs_were_written():
    lines, fault = grader.cost_lines()
    assert lines is not None, fault


def test_every_line_is_right():
    wrong, total, remarks = grader.lines_wrong()
    print("WRONG %d of %d" % (wrong, total))
    assert wrong == 0, "\n".join(remarks)
