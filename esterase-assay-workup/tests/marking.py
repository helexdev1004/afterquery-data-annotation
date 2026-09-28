"""Marking for the esterase plates task.

The unseen days are made here, in the verifier, by the same bench model that
made the three past days the agent was given, from seeds that were never
shipped.  A day's true figures are the note's arithmetic applied to each plate
the way round it really went into the reader, which the bench knows because it
put the plate there.

The submitted program is somebody else's code, so it is not run as the marker
is.  It is copied to a room of its own and run there as `nobody`, with a bare
environment: it cannot read /tests, where the bench and the seeds are, and it
cannot write under /logs/verifier, where the reward goes.
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile

import activities
import bench

UNSEEN_SEEDS = [7103, 7127, 7144, 7159, 7188, 7210, 7236, 7251, 7279, 7302, 7318, 7345]
BAR = 0.90
TOLERANCE = 0.02
FLOOR = 0.05
SECONDS_A_DAY = 120


def line_is_right(got, want):
    return abs(got - want) <= max(TOLERANCE * abs(want), FLOOR)


def true_figures(day, was_turned):
    figures = {}
    for plate in day["plates"]:
        as_filled = dict(plate)
        if was_turned[plate["plate"]]:
            as_filled["reads"] = {activities.turned(w): s for w, s in plate["reads"].items()}
        figures.update(activities.work_up({"plates": [as_filled]}, judge="as_laid"))
    return figures


def printed_lines(text):
    got = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            got[parts[0]] = float(parts[1])
        except ValueError:
            continue
    return got


def marker_is_root():
    return os.name == "posix" and os.geteuid() == 0


def a_room_for(program):
    """A directory holding nothing but a copy of the program, which `nobody`
    may read and write in."""
    room = tempfile.mkdtemp(prefix="assay-")
    copy = os.path.join(room, "activities.py")
    shutil.copyfile(str(program), copy)
    os.chmod(room, 0o755)
    os.chmod(copy, 0o644)
    if marker_is_root():
        import pwd
        who = pwd.getpwnam("nobody")
        os.chown(room, who.pw_uid, who.pw_gid)
        os.chown(copy, who.pw_uid, who.pw_gid)
    return room, copy


def run_on(copy, room, day):
    """The program's standard output for one day, or a word on what went wrong."""
    how = {"cwd": room,
           "env": {"PATH": os.environ.get("PATH", ""), "HOME": room,
                   "PYTHONDONTWRITEBYTECODE": "1"}}
    if marker_is_root():
        how.update(user="nobody", group="nogroup", extra_groups=[], start_new_session=True)
    child = subprocess.Popen([sys.executable, copy], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             text=True, **how)
    try:
        out, _ = child.communicate(json.dumps(day), timeout=SECONDS_A_DAY)
        if child.returncode != 0:
            return None, "exited %d" % child.returncode
        return out, None
    except subprocess.TimeoutExpired:
        return None, "took over %d s" % SECONDS_A_DAY
    finally:
        # nothing the program started outlives its day
        if marker_is_root():
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        else:
            child.kill()
        child.wait()


def mark_program(program, seeds=UNSEEN_SEEDS):
    tally = {"right": 0, "total": 0, "trouble": [], "by_day": {}}
    room, copy = a_room_for(program)
    try:
        for seed in seeds:
            day, was_turned = bench.one_day(seed)
            want = true_figures(day, was_turned)
            tally["total"] += len(want)
            out, wrong = run_on(copy, room, day)
            if wrong:
                tally["trouble"].append("%s %s" % (day["day"], wrong))
                continue
            got = printed_lines(out)
            ok = sum(1 for k, v in want.items() if k in got and line_is_right(got[k], v))
            tally["right"] += ok
            tally["by_day"][day["day"]] = [ok, len(want)]
    finally:
        shutil.rmtree(room, ignore_errors=True)
    return tally
