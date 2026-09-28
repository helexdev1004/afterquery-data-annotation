"""The graded checks."""
import grader


def test_a_file_was_written():
    written, why_not = grader.lines_written()
    assert written is not None, why_not


def test_the_expected_proteins_are_right():
    out, total, lines = grader.mark()
    print("WRONG %d of %d, allowed %d" % (out, total,
                                          grader.SAMPLES_THAT_MAY_BE_OUT))
    assert out <= grader.SAMPLES_THAT_MAY_BE_OUT, "\n".join(lines[:30])
