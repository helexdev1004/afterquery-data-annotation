"""Inspection evaluated the way ASME Y14.5 defines it.

Written first, so the truth a plate is graded against is a property of its
measured points rather than of any particular implementation.

Four things here are the standard rather than a choice:

  the datum reference frame is built in precedence - the seating face fixes the
  Z direction, the secondary face fixes the rotation about it, the tertiary
  face only fixes the remaining translation;

  flatness is the MINIMUM ZONE: the smallest separation between two parallel
  planes that contain every point. Least squares minimises the sum of squares,
  which is a different problem and always reports less;

  position is a DIAMETRAL zone, so it is twice the distance from nominal;

  at maximum material condition the position tolerance GROWS by however much
  the bore is larger than its maximum material size.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import linprog

POSITION_NOMINAL_KEY = "nominal"


# -- primitive fits ---------------------------------------------------------

def least_squares_plane(points: np.ndarray):
    """Return (unit normal, point on plane) of the least-squares plane."""
    centroid = points.mean(axis=0)
    _, _, vt = np.linalg.svd(points - centroid)
    return vt[2] / np.linalg.norm(vt[2]), centroid


def minimum_zone_flatness(points: np.ndarray) -> float:
    """The smallest separation of two parallel planes containing every point.

    A minimax problem, not a least-squares one. Written in a frame whose third
    axis is roughly the surface normal, a plane is z = a*x + b*y + c and the
    zone is the range of the residuals, so this is a linear program:

        minimise   t
        such that  -t <= z_i - (a x_i + b y_i + c) <= 0   for every point

    with the zone taken as t. Least squares on the same points always returns a
    smaller number, which is exactly why it is the wrong tool - it is not
    conservative, so it passes parts that are out of tolerance.
    """
    normal, centroid = least_squares_plane(points)
    # Local frame: e3 along the normal, e1/e2 spanning the surface.
    e3 = normal
    helper = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(helper, e3)) > 0.9:
        helper = np.array([0.0, 1.0, 0.0])
    e1 = np.cross(helper, e3)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(e3, e1)

    local = (points - centroid) @ np.column_stack([e1, e2, e3])
    x, y, z = local[:, 0], local[:, 1], local[:, 2]
    n = len(z)

    # Unknowns: a, b, c, t
    cost = np.array([0.0, 0.0, 0.0, 1.0])
    upper = np.column_stack([-x, -y, -np.ones(n), -np.ones(n)])   # z - plane <= 0 ... - t
    lower = np.column_stack([x, y, np.ones(n), np.zeros(n)])
    a_ub = np.vstack([lower, upper])
    b_ub = np.concatenate([z, -z])
    bounds = [(None, None), (None, None), (None, None), (0, None)]

    result = linprog(cost, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")
    if not result.success:
        # Fall back to the residual range about the least-squares plane, which
        # is an upper bound on nothing but is better than failing outright.
        return float(z.max() - z.min())
    return float(result.x[3])


def least_squares_circle(xy: np.ndarray):
    """Centre and diameter of the least-squares circle through 2-D points."""
    x, y = xy[:, 0], xy[:, 1]
    a = np.column_stack([x, y, np.ones(len(x))])
    b = x ** 2 + y ** 2
    solution, *_ = np.linalg.lstsq(a, b, rcond=None)
    cx, cy = solution[0] / 2.0, solution[1] / 2.0
    radius = math.sqrt(solution[2] + cx ** 2 + cy ** 2)
    return np.array([cx, cy]), 2.0 * radius


# -- datum reference frame --------------------------------------------------

def datum_frame(features: dict):
    """Build the frame from A, B and C in precedence order.

    A is primary and fixes the Z direction. B is secondary: its normal is taken
    only after the component along Z is removed, so it fixes the rotation about
    Z and nothing that A has already fixed. C is tertiary and by then can only
    fix the remaining translation. Doing this by fitting all three at once, or
    by trusting the machine axes, gives a different frame and therefore
    different positions.
    """
    na, pa = least_squares_plane(np.asarray(features["A"]))
    nb, pb = least_squares_plane(np.asarray(features["B"]))
    nc, pc = least_squares_plane(np.asarray(features["C"]))

    # Orient A's normal towards the bulk of the part.
    z = na
    if np.dot(np.asarray(features["H1"]).mean(axis=0) - pa, z) < 0:
        z = -z

    y = nb - np.dot(nb, z) * z
    y /= np.linalg.norm(y)
    if np.dot(np.asarray(features["H1"]).mean(axis=0) - pb, y) < 0:
        y = -y

    x = np.cross(y, z)
    x /= np.linalg.norm(x)
    if np.dot(np.asarray(features["H1"]).mean(axis=0) - pc, x) < 0:
        x = -x
        y = np.cross(z, x)

    # Origin: the common point of the three datum planes.
    normals = np.vstack([z, y, x])
    offsets = np.array([np.dot(z, pa), np.dot(y, pb), np.dot(x, pc)])
    origin = np.linalg.solve(normals, offsets)

    rotation = np.column_stack([x, y, z])
    return origin, rotation


def to_frame(points: np.ndarray, origin, rotation) -> np.ndarray:
    return (np.asarray(points) - origin) @ rotation


# -- the report -------------------------------------------------------------

def inspect(plate: dict) -> dict:
    features = {k: np.asarray(v, dtype=float)
                for k, v in plate["measurements"].items()}
    drawing = plate["drawing"]

    flatness = minimum_zone_flatness(features["A"])
    flatness_tol = drawing["flatness"]["tolerance"]

    origin, rotation = datum_frame(features)
    size = drawing["bore_size"]
    position = drawing["position"]
    mmc_size = size["min"]           # a hole is at maximum material when smallest

    callouts = [{
        "callout": "flatness",
        "feature": drawing["flatness"]["feature"],
        "actual": round(flatness, 6),
        "tolerance": flatness_tol,
        "pass": bool(flatness <= flatness_tol),
    }]

    for name, nominal in sorted(position[POSITION_NOMINAL_KEY].items()):
        local = to_frame(features[name], origin, rotation)
        centre, diameter = least_squares_circle(local[:, :2])
        deviation = math.hypot(centre[0] - nominal[0], centre[1] - nominal[1])
        actual_position = 2.0 * deviation
        bonus = max(0.0, diameter - mmc_size)
        allowed = position["tolerance"] + bonus

        callouts.append({
            "callout": "size",
            "feature": name,
            "actual": round(diameter, 6),
            "tolerance": [size["min"], size["max"]],
            "pass": bool(size["min"] <= diameter <= size["max"]),
        })
        callouts.append({
            "callout": "position",
            "feature": name,
            "actual": round(actual_position, 6),
            "tolerance": round(allowed, 6),
            "pass": bool(actual_position <= allowed),
        })

    return {"plate": plate["plate"], "callouts": callouts}
