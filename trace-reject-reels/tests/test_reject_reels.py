"""The graded checks."""
import grader


def test_the_claim_file_reads():
    lines, reason = grader.claim_lines()
    assert lines is not None, reason


def test_enough_rejects_are_placed():
    out, total, words = grader.misplaced()
    print("OUT %d of %d, may be %d" % (out, total, grader.LINES_THAT_MAY_BE_OUT))
    assert out <= grader.LINES_THAT_MAY_BE_OUT, "\n".join(words[:30])
