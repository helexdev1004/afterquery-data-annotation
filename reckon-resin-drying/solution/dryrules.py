"""The shop's drying procedure, as arithmetic, and the ways a time gets written.

A dryer is run down and refilled in one go, on the run; the drying clock starts
again at the refill. The drying time of a shot is the time from the last refill
of its machine's dryer before the shot to the shot itself, in hours, and its
resin is the resin that refill put in.
"""

import bisect
import datetime as dt

DAY0_UNIX = dt.datetime(1970, 1, 1)
DAY0_SHEET = dt.datetime(1899, 12, 30)
HOURS_WITHIN = 0.1
RESINS = ("virgin", "blend 20", "blend 40")     # share of regrind, per cent


def seconds(moment):
    return (moment - DAY0_UNIX).total_seconds()


def iso(text):
    """'2026-09-14 07:31:05.2' or '2026-09-14 07:31' -> seconds since 1970."""
    for shape in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S",
                  "%Y-%m-%d %H:%M"):
        try:
            return seconds(dt.datetime.strptime(text, shape))
        except ValueError:
            continue
    raise ValueError(text)


def continental(text):
    """'14.09.2026 07:31:05,2' -> seconds since 1970."""
    return seconds(dt.datetime.strptime(text.replace(",", "."),
                                        "%d.%m.%Y %H:%M:%S.%f"))


def sheet_day(number):
    return seconds(DAY0_SHEET) + float(number) * 86400.0


class Dryer:
    """The refills of one dryer, oldest first: (site time, resin)."""

    def __init__(self, refills):
        self.refills = sorted(refills)
        self.times = [t for t, _ in self.refills]

    def drying(self, site_time):
        """(hours on the dryer, resin) for a shot made at `site_time`."""
        at = bisect.bisect_right(self.times, site_time) - 1
        if at < 0:
            return None
        began, resin = self.refills[at]
        return (site_time - began) / 3600.0, resin


def same(said, want):
    """Does {'hours': 3.2, 'resin': 'virgin'} agree with the sealed entry?"""
    try:
        return said["resin"] == want["resin"] and not isinstance(
            said["hours"], bool) and abs(float(said["hours"])
                                         - want["hours"]) <= HOURS_WITHIN + 1e-9
    except (KeyError, TypeError, ValueError):
        return False
