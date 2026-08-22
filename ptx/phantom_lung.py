"""Deterministic lung-texture phantom with nodule insertion (M2 target).

M1 ships a functional minimal core: an isotropic 1/f^beta random field
(seeded, deterministic) and Gaussian nodule insertion. The full clinical
texture model (anisotropy, vessel trees, HU calibration) lands in M2 —
see docs/IORN-009A_research_protocol_v0.3.md section 6.
"""

from __future__ import annotations

import numpy as np

__all__ = ["power_law_texture", "insert_gaussian_nodule"]


def power_law_texture(shape, beta, seed, mean=0.0, sd=1.0):
    """Deterministic 2-D/3-D random field with power spectrum ~ 1/f^beta."""
    if beta < 0:
        raise ValueError("beta must be non-negative")
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(shape)
    spec = np.fft.fftn(white)
    grids = np.meshgrid(
        *[np.fft.fftfreq(n) for n in shape], indexing="ij"
    )
    f = np.sqrt(sum(g**2 for g in grids))
    f[tuple(0 for _ in shape)] = np.inf  # kill DC scaling
    amp = f ** (-beta / 2.0)
    amp[~np.isfinite(amp)] = 0.0
    field = np.real(np.fft.ifftn(spec * amp))
    field -= field.mean()
    s = field.std()
    if s > 0:
        field *= sd / s
    return field + mean


def insert_gaussian_nodule(volume, center, diameter_px, contrast):
    """Add a Gaussian blob nodule (FWHM = diameter) in place-safe copy."""
    vol = np.array(volume, dtype=float, copy=True)
    sigma = diameter_px / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    grids = np.meshgrid(
        *[np.arange(n, dtype=float) for n in vol.shape], indexing="ij"
    )
    r2 = sum((g - c) ** 2 for g, c in zip(grids, center))
    vol += contrast * np.exp(-r2 / (2.0 * sigma**2))
    return vol
