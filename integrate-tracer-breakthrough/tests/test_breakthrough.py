"""The graded checks."""
import grader


def test_answer_was_written():
    lines, why = grader.answer_lines()
    assert lines is not None, why


def test_all_columns_agree():
    wrong, total, remarks = grader.tally()
    print("WRONG %d of %d" % (wrong, total))
    assert wrong == 0, "\n".join(remarks)
