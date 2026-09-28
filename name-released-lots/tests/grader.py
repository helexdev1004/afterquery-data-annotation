"""Run the agent's program on the graded campaigns and score what it prints.

The campaigns are rebuilt here from a seed that never left this image. The
agent's program is run as a subprocess, one campaign at a time, with the
campaign on standard input; nothing of the agent's is imported into this
process.

Each request is worth 10 when the lot named is the one the store released and
nothing otherwise, so partial work scores partially and no single campaign
decides the reward.
"""
import json
import pathlib
import subprocess
import sys

PROGRAM = pathlib.Path("/app/releases.py")
EXACT = 10
BAR = 2790
PER_CAMPAIGN_SECONDS = 60

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import make_cases                                              # noqa: E402
import releases                                                # noqa: E402


class Unusable(Exception):
    pass


def answers_for(campaign):
    """What the agent's program prints for one campaign, as whole numbers."""
    if not PROGRAM.is_file():
        raise Unusable("%s was not written" % PROGRAM)
    try:
        done = subprocess.run(
            [sys.executable, str(PROGRAM)],
            input=json.dumps(campaign), capture_output=True, text=True,
            timeout=PER_CAMPAIGN_SECONDS)
    except subprocess.TimeoutExpired:
        return None, "did not finish inside %d seconds" % PER_CAMPAIGN_SECONDS
    if done.returncode != 0:
        return None, "exited %d: %s" % (done.returncode, done.stderr.strip()[:200])
    return done.stdout.split(), ""


def mark():
    """(points, top, one remark for each campaign that went wrong)."""
    campaigns = make_cases.graded_set()
    points, top, remarks = 0, 0, []
    for number, campaign in enumerate(campaigns, 1):
        wanted = releases.play(campaign)
        top += len(wanted) * EXACT
        given, trouble = answers_for(campaign)
        if given is None:
            remarks.append("campaign %d: %s" % (number, trouble))
            continue
        if len(given) != len(wanted):
            remarks.append("campaign %d: %d answers for %d requests"
                           % (number, len(given), len(wanted)))
        for a, b in zip(given, wanted):
            if a == b:
                points += EXACT
    return points, top, remarks
