"""Task-weighted perceptual detectability integrals (protocol section 5.2).

d'^2_human = eta_cog * Integral |W(f)|^2 |H_eff(f)|^2 V^2(f) / N_eff(f) df

plus the derived indices f_sat, R_perceptual and G_useful.

The visual weight ``V`` is unity in the v0.4 primary form, where visual
sensitivity lives in N_eff as Barten's internal noise; passing the normalised
CSF instead recovers the superseded v0.3 weight form, kept as the ideal limit
of the appendix. Both are evaluated in ``ptx.phase1``.

All integrals are deterministic trapezoids on caller-supplied grids.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "dprime_squared",
    "contribution_density",
    "f_sat",
    "r_perceptual",
    "g_useful",
]


def contribution_density(
    f, w_task, h_eff, visual_weight, n_eff, eta_cog=1.0, radial=False
):
    """Integrand of the d'^2 integral (per-frequency contribution density).

    With ``radial=True`` the isotropic 2-D Jacobian is folded in
    (``int ... d^2f = int ... 2 pi f df``), which is the form a 2-D imaging
    task needs; ``f_sat`` is then read off the same 2-D density.
    """
    f = np.asarray(f, dtype=float)
    w = np.asarray(w_task, dtype=float)
    h = np.asarray(h_eff, dtype=float)
    s = np.asarray(visual_weight, dtype=float)
    n = np.asarray(n_eff, dtype=float)
    if not (f.shape == w.shape == h.shape == s.shape == n.shape):
        raise ValueError("all spectral arrays must share one grid")
    if np.any(n <= 0):
        raise ValueError("effective noise power must be positive")
    dens = eta_cog * (np.abs(w) ** 2) * (np.abs(h) ** 2) * (s**2) / n
    if radial:
        if np.any(f < 0):
            raise ValueError("radial form needs non-negative frequencies")
        dens = dens * 2.0 * np.pi * f
    return dens


def dprime_squared(
    f, w_task, h_eff, visual_weight, n_eff, eta_cog=1.0, radial=False
):
    """d'^2_human via trapezoidal integration on the grid ``f``."""
    dens = contribution_density(
        f, w_task, h_eff, visual_weight, n_eff, eta_cog, radial
    )
    return float(np.trapezoid(dens, np.asarray(f, dtype=float)))


def f_sat(f, density, fraction=0.95):
    """Perceptual saturation frequency (protocol section 5.2).

    The frequency below which ``fraction`` of the total integrated
    contribution accumulates, found by linear interpolation on the
    cumulative trapezoid.
    """
    if not 0.0 < fraction < 1.0:
        raise ValueError("fraction must be in (0, 1)")
    f = np.asarray(f, dtype=float)
    d = np.asarray(density, dtype=float)
    if f.ndim != 1 or f.shape != d.shape:
        raise ValueError("f and density must be matching 1-D arrays")
    seg = np.diff(f) * 0.5 * (d[1:] + d[:-1])
    cum = np.concatenate(([0.0], np.cumsum(seg)))
    total = cum[-1]
    if total <= 0:
        raise ValueError("total contribution must be positive")
    target = fraction * total
    idx = int(np.searchsorted(cum, target))
    if idx == 0:
        return float(f[0])
    lo, hi = cum[idx - 1], cum[idx]
    frac_seg = 0.0 if hi == lo else (target - lo) / (hi - lo)
    return float(f[idx - 1] + frac_seg * (f[idx] - f[idx - 1]))


def r_perceptual(dprime_human, dprime_ideal):
    """Perceptual utilisation ratio d'_human / d'_ideal."""
    if dprime_ideal <= 0:
        raise ValueError("ideal d' must be positive")
    return float(dprime_human / dprime_ideal)


def g_useful(dprime_values, doses):
    """Perceptual information gain per unit dose, dDelta d'/dDelta D.

    Returns the sequence of finite-difference slopes between successive
    (dose, d') points, ordered by dose.
    """
    d = np.asarray(dprime_values, dtype=float)
    x = np.asarray(doses, dtype=float)
    if d.shape != x.shape or d.ndim != 1 or d.size < 2:
        raise ValueError("need matching 1-D arrays with >= 2 points")
    order = np.argsort(x)
    x, d = x[order], d[order]
    dx = np.diff(x)
    if np.any(dx <= 0):
        raise ValueError("doses must be strictly increasing after sorting")
    return np.diff(d) / dx
