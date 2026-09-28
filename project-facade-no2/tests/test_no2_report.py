"""The graded checks."""
import grader


def test_report_can_be_read():
    assert grader.load_report()


def test_all_ten_sites_within_tolerance():
    out = grader.sites_out()
    print("OUT %d" % len(out))
    assert out == [], "; ".join("%s: %s" % pair for pair in out)
