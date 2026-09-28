"""The graded check."""
import grader


def test_program_reaches_the_bar():
    points, top, remarks = grader.mark()
    print("SCORED %d of %d, bar %d" % (points, top, grader.BAR))
    for remark in remarks[:10]:
        print("  " + remark)
    assert points >= grader.BAR, \
        "scored %d of %d, short of the bar at %d" % (points, top, grader.BAR)
