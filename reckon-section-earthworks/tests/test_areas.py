"""The graded checks."""
import grader


def test_a_sheet_was_written():
    written, why_not = grader.rows_written()
    assert written is not None, why_not


def test_the_areas_are_right():
    wrong, total, lines = grader.mark()
    print("WRONG %d of %d, allowed %d" % (wrong, total,
                                          grader.ROWS_ALLOWED_WRONG))
    assert wrong <= grader.ROWS_ALLOWED_WRONG, "\n".join(lines[:30])
