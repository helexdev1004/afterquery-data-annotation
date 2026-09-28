"""The graded checks."""
import grader


def test_budget_file_is_there():
    found, trouble = grader.budget_lines()
    assert found is not None, trouble


def test_budget_is_closed():
    wrong, total, remarks = grader.mark()
    print("WRONG %d of %d" % (wrong, total))
    assert wrong <= grader.ALLOWED_WRONG, "\n".join(remarks)
