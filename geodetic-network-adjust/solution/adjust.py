"""Correct least-squares adjustment, written first so ground truth is real.

Everything is done in the scaled system: each observation equation is divided by
its own standard deviation, in the unit that observation is actually quoted in.
That makes the problem unitless, which is the only way a network mixing metres
with arc seconds has a meaningful weight matrix at all, and it makes the
residual statistics below fall out directly.

Solved with a QR factorisation of the scaled design matrix rather than by
forming and inverting the normal equations. A^T A squares the condition number,
which costs roughly half the available digits - harmless on a braced network,
ruinous on a long traverse.
"""

from __future__ import annotations

import math

import numpy as np

ARCSEC = math.pi / (180.0 * 3600.0)
BLUNDER_CRITICAL = 3.29          # two-sided normal, alpha = 0.001
MAX_ITERATIONS = 25
CONVERGENCE_M = 1e-7


def free_points(net: dict) -> list[str]:
    fixed = set(net["datum"]["fixed"])
    return sorted(p for p in net["points"] if p not in fixed)


def _row(net, obs, coords, order):
    """One scaled observation equation: (partials, residual)."""
    a, b = obs["from"], obs["to"]
    ax, ay = coords[a]
    bx, by = coords[b]
    dx, dy = bx - ax, by - ay
    dist2 = dx * dx + dy * dy
    dist = math.sqrt(dist2)
    row = np.zeros(2 * len(order))

    def put(point, d_dx, d_dy):
        if point in order:
            i = order.index(point)
            row[2 * i] = d_dx
            row[2 * i + 1] = d_dy

    if obs["type"] == "distance":
        sigma = obs["sigma_m"]
        put(a, -dx / dist, -dy / dist)
        put(b, dx / dist, dy / dist)
        residual = obs["value_m"] - dist
    else:
        # Azimuth measured clockwise from +y. Partials are radians per metre,
        # so the residual has to be radians too.
        sigma = obs["sigma_arcsec"] * ARCSEC
        put(a, -dy / dist2, dx / dist2)
        put(b, dy / dist2, -dx / dist2)
        computed = math.atan2(dx, dy)
        observed = math.radians(obs["value_deg"])
        residual = (observed - computed + math.pi) % (2 * math.pi) - math.pi

    return row / sigma, residual / sigma


def _build(net, coords, order, used):
    rows, rhs = [], []
    for obs in net["observations"]:
        if obs["id"] not in used:
            continue
        row, res = _row(net, obs, coords, order)
        rows.append(row)
        rhs.append(res)
    return np.asarray(rows), np.asarray(rhs)


def _solve_once(net, order, used):
    """Gauss-Newton to convergence. Returns coords, scaled residuals, design."""
    coords = {p: (v["x"], v["y"]) for p, v in net["points"].items()}
    design = residual = None
    for _ in range(MAX_ITERATIONS):
        design, residual = _build(net, coords, order, used)
        if design.size == 0:
            break
        # QR, not the normal equations.
        step, *_ = np.linalg.lstsq(design, residual, rcond=None)
        for i, point in enumerate(order):
            x, y = coords[point]
            coords[point] = (x + step[2 * i], y + step[2 * i + 1])
        if np.max(np.abs(step)) < CONVERGENCE_M:
            break
    design, residual = _build(net, coords, order, used)
    return coords, design, residual


def rank_deficient(design: np.ndarray, unknowns: int) -> bool:
    if design.size == 0:
        return True
    return int(np.linalg.matrix_rank(design)) < unknowns


def adjust(net: dict) -> dict:
    order = free_points(net)
    unknowns = 2 * len(order)
    used = {o["id"] for o in net["observations"]}

    coords, design, residual = _solve_once(net, order, used)
    if rank_deficient(design, unknowns):
        # Orientation, scale or position is not determined by these
        # observations. Any answer would be one of infinitely many, so report
        # the defect instead of inventing one.
        return {
            "rank_deficient": True,
            "points": {},
            "variance_factor": None,
            "blunders": [],
            "degrees_of_freedom": len(used) - unknowns,
        }

    blunders: list[str] = []
    while True:
        coords, design, residual = _solve_once(net, order, used)
        dof = len(used) - unknowns
        if dof <= 0:
            break
        # Redundancy numbers from the hat matrix of the scaled system.
        q, _ = np.linalg.qr(design)
        leverage = np.sum(q * q, axis=1)
        redundancy = np.clip(1.0 - leverage, 1e-12, None)
        sigma0_sq = float(residual @ residual) / dof
        standardised = residual / np.sqrt(redundancy)

        worst = int(np.argmax(np.abs(standardised)))
        if abs(standardised[worst]) <= BLUNDER_CRITICAL:
            break
        ids = [o["id"] for o in net["observations"] if o["id"] in used]
        blunders.append(ids[worst])
        used.discard(ids[worst])
        if len(used) - unknowns <= 0:
            break

    coords, design, residual = _solve_once(net, order, used)
    dof = len(used) - unknowns          # every removed observation costs one
    sigma0_sq = float(residual @ residual) / dof if dof > 0 else None

    return {
        "rank_deficient": False,
        "points": {p: {"x": coords[p][0], "y": coords[p][1]} for p in net["points"]},
        "variance_factor": sigma0_sq,
        "blunders": sorted(blunders),
        "degrees_of_freedom": dof,
    }
