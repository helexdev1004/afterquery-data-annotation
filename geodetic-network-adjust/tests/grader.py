"""Score the submitted adjustment over the graded networks."""

from __future__ import annotations

import json
import math
import os
import pathlib
import subprocess
import tempfile

TESTS = pathlib.Path("/tests")
NETWORKS = TESTS / "graded"
TRUTH = TESTS / "truth"
REFERENCE = TESTS / "reference"

PASS_MARK = 9
COORD_TOLERANCE_M = 0.05
VARIANCE_TOLERANCE = 0.25
PER_NETWORK_TIMEOUT = 300
RUN_AS = "runner"


def network_names() -> list[str]:
    return sorted(p.stem for p in NETWORKS.glob("*.json"))


def _drop_privileges() -> dict:
    """Arguments that make subprocess.run drop to the unprivileged account.

    Deliberately degrades rather than fails. If the account is missing, or this
    is not running as root, the submission still runs in its own process - one
    less layer, but the grading is unaffected. Wiring this to an external
    binary that might not be installed would have failed EVERY network and
    scored the reference solution zero.
    """
    try:
        import pwd
        entry = pwd.getpwnam(RUN_AS)
    except (ImportError, KeyError):
        return {}
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        return {}
    return {"user": entry.pw_uid, "group": entry.pw_gid}


PRIVILEGES = _drop_privileges()


def run_one(name: str) -> tuple[dict | None, str]:
    """Run the submission in its own process, as an unprivileged user."""
    net = NETWORKS / f"{name}.json"
    with tempfile.TemporaryDirectory() as work:
        os.chmod(work, 0o777)
        out = pathlib.Path(work) / "out.json"
        cmd = ["python", str(TESTS / "runner.py"), str(net), str(out)]
        try:
            done = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=PER_NETWORK_TIMEOUT, cwd=work,
                                  **PRIVILEGES)
        except subprocess.TimeoutExpired:
            return None, "timed out"
        if done.returncode != 0:
            tail = (done.stderr or "").strip().splitlines()
            return None, "raised: " + (tail[-1][:160] if tail else "no output")
        try:
            return json.loads(out.read_text()), ""
        except Exception as exc:
            return None, f"did not write a readable answer: {exc}"


def score_one(name: str) -> str:
    """Empty string means correct; otherwise what was wrong."""
    result, problem = run_one(name)
    if result is None:
        return problem
    if not isinstance(result, dict):
        return "did not return an object"

    truth = json.loads((TRUTH / f"{name}.json").read_text())
    reference = json.loads((REFERENCE / f"{name}.json").read_text())

    claimed = bool(result.get("rank_deficient"))
    expected_rank = bool(reference["rank_deficient"])
    if claimed != expected_rank:
        return ("reported rank_deficient=%s; the observations %s determine the "
                "coordinates" % (claimed,
                                 "do not" if expected_rank else "do"))
    if expected_rank:
        return ""

    points = result.get("points")
    if not isinstance(points, dict):
        return "no points returned"
    worst, worst_at = 0.0, None
    for point, true_xy in truth["true_points"].items():
        got = points.get(point)
        if not isinstance(got, dict) or "x" not in got or "y" not in got:
            return f"no coordinates for {point}"
        offset = math.hypot(float(got["x"]) - true_xy["x"],
                            float(got["y"]) - true_xy["y"])
        if offset > worst:
            worst, worst_at = offset, point
    if worst > COORD_TOLERANCE_M:
        return (f"{worst_at} is out by {worst * 1000:.0f} mm; the tolerance is "
                f"{COORD_TOLERANCE_M * 1000:.0f} mm")

    got_var = result.get("variance_factor")
    ref_var = reference["variance_factor"]
    if got_var is None:
        return "no variance factor returned"
    if abs(float(got_var) - ref_var) > VARIANCE_TOLERANCE * ref_var:
        return (f"variance factor {float(got_var):.3f}; expected about "
                f"{ref_var:.3f}")

    got_blunders = sorted(result.get("blunders") or [])
    if got_blunders != sorted(truth["blunders"]):
        return (f"rejected {got_blunders or 'nothing'}; the observations "
                f"actually in error are {sorted(truth['blunders'])}")
    return ""


def run_all() -> dict[str, str]:
    return {name: score_one(name) for name in network_names()}
