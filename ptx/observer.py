"""Model observers (protocol section 6): NPWE and channelized Hotelling.

Two families are kept side by side so that model choice becomes a sensitivity
analysis rather than a hidden assumption (protocol sections 6 and 7):

- ``npwe_dprime_squared``  non-prewhitening observer with an eye filter
- ``cho_dprime_squared``   channelized Hotelling observer, DOG channels
- ``ideal_dprime_squared`` prewhitening ideal observer (the R_perceptual
  denominator and the upper bound both other observers must respect)

All three take radially symmetric spectra on a caller-supplied 1-D grid. With
``radial=True`` the isotropic 2-D measure ``d^2f = 2 pi f df`` is used, which
is the correct form for a 2-D detection task.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "npwe_dprime_squared",
    "ideal_dprime_squared",
    "dog_channels",
    "dog_channel_peak_factor",
    "dog_channels_spanning",
    "cho_dprime_squared",
]


def _measure(f, radial):
    """Integration weight: 2 pi f for the isotropic 2-D form, else 1."""
    f = np.asarray(f, dtype=float)
    if not radial:
        return np.ones_like(f)
    if np.any(f < 0):
        raise ValueError("radial form needs non-negative frequencies")
    return 2.0 * np.pi * f


def _checked(f, *arrays):
    f = np.asarray(f, dtype=float)
    out = [np.asarray(a, dtype=float) for a in arrays]
    for a in out:
        if a.shape != f.shape:
            raise ValueError("all spectral arrays must share one grid")
    return f, out


def npwe_dprime_squared(
    f, signal_spectrum, noise_power, eye_filter=None, radial=False
):
    """Non-prewhitening observer with eye filter (NPWE), radial 1-D form.

    d'^2 = [Int |S|^2 E^2 dm]^2 / Int |S|^2 E^4 N dm

    With E == 1 and white noise this reduces to the ideal-observer
    d'^2 = Int |S|^2 / N dm, which the tests exploit as an anchor.
    """
    f, (s, n) = _checked(f, signal_spectrum, noise_power)
    s2 = np.abs(s) ** 2
    e = np.ones_like(f) if eye_filter is None else np.asarray(eye_filter, float)
    if e.shape != f.shape:
        raise ValueError("all spectral arrays must share one grid")
    if np.any(n <= 0):
        raise ValueError("noise power must be positive")
    dm = _measure(f, radial)
    num = np.trapezoid(s2 * e**2 * dm, f) ** 2
    den = np.trapezoid(s2 * e**4 * n * dm, f)
    if den <= 0:
        raise ValueError("degenerate NPWE denominator")
    return float(num / den)


def ideal_dprime_squared(
    f, signal_spectrum, noise_power, transfer=None, radial=False
):
    """Prewhitening ideal observer, d'^2 = Int |S H|^2 / N dm.

    Serves as the R_perceptual denominator (protocol section 5.2) with the
    display and visual stages set to unity.
    """
    f, (s, n) = _checked(f, signal_spectrum, noise_power)
    h = np.ones_like(f) if transfer is None else np.asarray(transfer, float)
    if h.shape != f.shape:
        raise ValueError("all spectral arrays must share one grid")
    if np.any(n <= 0):
        raise ValueError("noise power must be positive")
    dm = _measure(f, radial)
    return float(np.trapezoid(np.abs(s * h) ** 2 / n * dm, f))


# --------------------------------------------------------------------------
# Channel sets
# --------------------------------------------------------------------------


def dog_channels(f, sigma0, n_channels=10, alpha=1.4, q=1.67):
    """Dense difference-of-Gaussian channel profiles (Abbey & Barrett form).

    ``C_j(f) = exp(-f^2 / 2 (q s_j)^2) - exp(-f^2 / 2 s_j^2)`` with
    ``s_j = sigma0 alpha^j``: a wide minus a narrow Gaussian, so each channel
    is band-pass and vanishes at DC. Radially symmetric channels suffice
    because the nodule task is rotationally symmetric; the published shape
    parameters are ``alpha = 1.4`` and ``q = 1.67``. The overall sign of a
    channel is immaterial — the CHO is invariant under ``C_j -> -C_j``.

    Returns an array of shape ``(n_channels, f.size)``. ``sigma0`` is in the
    units of ``f``.
    """
    if sigma0 <= 0:
        raise ValueError("sigma0 must be positive")
    if n_channels < 1:
        raise ValueError("need at least one channel")
    if alpha <= 1.0:
        raise ValueError("alpha must exceed 1 for a spanning channel set")
    if q <= 1.0:
        raise ValueError("q must exceed 1 for a band-pass channel")
    f = np.asarray(f, dtype=float)
    sigmas = sigma0 * alpha ** np.arange(n_channels, dtype=float)
    s = sigmas[:, None]
    return np.exp(-(f**2) / (2.0 * (q * s) ** 2)) - np.exp(
        -(f**2) / (2.0 * s**2)
    )


def dog_channel_peak_factor(q=1.67):
    """Ratio of a DOG channel's peak frequency to its ``sigma``.

    Setting dC/df = 0 for the wide-minus-narrow difference gives
    ``f_peak = sigma sqrt(4 ln q q^2 / (q^2 - 1))``.
    """
    if q <= 1.0:
        raise ValueError("q must exceed 1 for a band-pass channel")
    return float(np.sqrt(4.0 * np.log(q) * q**2 / (q**2 - 1.0)))


def dog_channels_spanning(f, f_max, n_channels=10, f_min=None, alpha=1.4, q=1.67):
    """DOG channel set whose highest channel *peaks* at ``f_max``.

    Convenience constructor that keeps the channel set matched to the physics
    of each condition instead of to a pixel-unit convention carried over from
    another study. With ``f_min`` the channel peaks are log-spaced across
    ``[f_min, f_max]``; otherwise they step down from ``f_max`` by ``alpha``.

    Covering the low-frequency end matters: a channel set that starts above
    the task's main lobe throws away most of the signal and makes a large
    lesion look *harder* than a small one, so ``f_min`` should sit below the
    first zero of the task spectrum.
    """
    if f_max <= 0:
        raise ValueError("f_max must be positive")
    peak_factor = dog_channel_peak_factor(q)
    if f_min is not None:
        if not 0 < f_min < f_max:
            raise ValueError("f_min must lie in (0, f_max)")
        if n_channels < 2:
            raise ValueError("spanning a band needs at least two channels")
        alpha = (f_max / f_min) ** (1.0 / (n_channels - 1))
        sigma0 = f_min / peak_factor
    else:
        sigma0 = f_max / peak_factor / alpha ** (n_channels - 1)
    return dog_channels(f, sigma0, n_channels, alpha, q)


# --------------------------------------------------------------------------
# Channelized Hotelling observer
# --------------------------------------------------------------------------


def cho_dprime_squared(
    f,
    signal_spectrum,
    noise_power,
    channels,
    transfer=None,
    visual_filter=None,
    channel_noise_fraction=0.0,
    radial=False,
):
    """Channelized Hotelling observer, d'^2 = t^T K^-1 t.

    For radially symmetric channels ``C_j`` the channel template response to
    the mean signal and the channel covariance are

        t_j  = Int C_j E S H dm
        K_ij = Int C_i C_j E^2 N dm

    with ``dm`` the integration measure and ``E`` an optional visual filter
    applied to the data before channelization. Filtering both signal and noise
    leaves a prewhitening observer unchanged but not a channelized one, which
    is precisely why the CSF has to be handed to the CHO explicitly if the two
    observer families are to see the same chain.

    ``channel_noise_fraction`` (beta) adds internal channel noise
    ``beta^2 diag(K)``, the standard way of degrading a CHO towards human
    efficiency.
    """
    f, (s, n) = _checked(f, signal_spectrum, noise_power)
    c = np.atleast_2d(np.asarray(channels, dtype=float))
    if c.ndim != 2 or c.shape[1] != f.size:
        raise ValueError("channels must have shape (n_channels, f.size)")
    h = np.ones_like(f) if transfer is None else np.asarray(transfer, float)
    e = (
        np.ones_like(f)
        if visual_filter is None
        else np.asarray(visual_filter, float)
    )
    if h.shape != f.shape or e.shape != f.shape:
        raise ValueError("all spectral arrays must share one grid")
    if np.any(n <= 0):
        raise ValueError("noise power must be positive")
    if channel_noise_fraction < 0:
        raise ValueError("channel noise fraction must be non-negative")

    dm = _measure(f, radial)
    t = np.trapezoid(c * (e * s * h * dm), f, axis=1)
    weighted = c * (e**2 * n * dm)
    k = np.trapezoid(c[:, None, :] * weighted[None, :, :], f, axis=2)
    k = 0.5 * (k + k.T)
    if channel_noise_fraction > 0:
        k = k + channel_noise_fraction**2 * np.diag(np.diag(k))
    try:
        solution = np.linalg.solve(k, t)
    except np.linalg.LinAlgError as exc:
        raise ValueError("singular channel covariance") from exc
    return float(max(t @ solution, 0.0))
