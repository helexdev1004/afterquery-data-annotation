"""The graded checks."""
import grader


def test_answer_is_an_object_keyed_by_plot():
    given = grader.answer()
    assert isinstance(given, dict), given


def test_every_plot_within_tolerance():
    out = grader.plots_out()
    print("OUT %d" % len(out))
    assert not out, "; ".join("%s: %s" % item for item in sorted(out.items()))
