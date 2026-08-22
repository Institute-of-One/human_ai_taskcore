"""Model observers (protocol section 6): NPWE now, channelized CHO in M2."""

from __future__ import annotations

import numpy as np

__all__ = ["npwe_dprime_squared", "cho_dprime_squared"]


def npwe_dprime_squared(f, signal_spectrum, noise_power, eye_filter=None):
    """Non-prewhitening observer with eye filter (NPWE), radial 1-D form.

    d'^2 = [Int |S|^2 E^2 df]^2 / Int |S|^2 E^4 N df

    With E == 1 and white noise this reduces to the ideal-observer
    d'^2 = Int |S|^2 / N df, which the tests exploit as an anchor.
    """
    f = np.asarray(f, dtype=float)
    s2 = np.abs(np.asarray(signal_spectrum, dtype=float)) ** 2
    n = np.asarray(noise_power, dtype=float)
    e = (
        np.ones_like(f)
        if eye_filter is None
        else np.asarray(eye_filter, dtype=float)
    )
    if not (f.shape == s2.shape == n.shape == e.shape):
        raise ValueError("all spectral arrays must share one grid")
    if np.any(n <= 0):
        raise ValueError("noise power must be positive")
    num = np.trapezoid(s2 * e**2, f) ** 2
    den = np.trapezoid(s2 * e**4 * n, f)
    if den <= 0:
        raise ValueError("degenerate NPWE denominator")
    return float(num / den)


def cho_dprime_squared(*args, **kwargs):
    """Channelized Hotelling observer — implemented in milestone M2."""
    raise NotImplementedError(
        "CHO lands in M2 (Gabor/DOG channels); see protocol section 6"
    )
