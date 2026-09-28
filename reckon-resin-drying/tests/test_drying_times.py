"""The graded checks."""
import grader


def test_a_table_was_written():
    said, why_not = grader.submitted()
    assert said is not None, why_not


def test_the_table_is_right():
    wrong, total, detail = grader.mark()
    print("WRONG %d of %d, allowed %d"
          % (wrong, total, grader.ENTRIES_THAT_MAY_BE_WRONG))
    assert wrong <= grader.ENTRIES_THAT_MAY_BE_WRONG, "\n".join(detail[:30])
