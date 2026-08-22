"""Display and visual-system transfer chain (IORN-009A, protocol section 5).

Every component is implemented independently from the primary literature /
standard and cross-checked against published anchor values in ``tests/``:

- ``gsdf_luminance``       DICOM PS3.14 Grayscale Standard Display Function
- ``display_pixel_mtf``    pixel-aperture MTF of the display
- ``pupil_diameter_mm``    luminance-dependent pupil model (Barten 1999)
- ``eye_mtf``              ocular optics MTF (Gaussian approximation, Barten 1999)
- ``barten_csf``           Barten contrast sensitivity function (Barten 1999/2004)

Units convention:
- spatial frequency on the display plane: cycles/mm  (``f_mm``)
- spatial frequency at the eye:           cycles/degree (``u_deg``)
- luminance: cd/m^2
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "gsdf_luminance",
    "gsdf_jnd_contrast",
    "display_pixel_mtf",
    "pupil_diameter_mm",
    "eye_mtf",
    "barten_csf",
    "cycles_per_mm_to_cycles_per_degree",
]

# --------------------------------------------------------------------------
# DICOM PS3.14 Grayscale Standard Display Function
# --------------------------------------------------------------------------

# Coefficients of the GSDF rational polynomial, DICOM PS3.14 (2011+), eq. 7-1.
_GSDF_A = -1.3011877
_GSDF_B = -2.5840191e-2
_GSDF_C = 8.0242636e-2
_GSDF_D = -1.0320229e-1
_GSDF_E = 1.3646699e-1
_GSDF_F = 2.8745620e-2
_GSDF_G = -2.5468404e-2
_GSDF_H = -3.1978977e-3
_GSDF_K = 1.2992634e-4
_GSDF_M = 1.3635334e-3


def gsdf_luminance(j):
    """Luminance L(j) in cd/m^2 for JND index ``j`` (DICOM PS3.14 eq. 7-1).

    Valid for 1 <= j <= 1023 (luminance range ~0.05 to ~4000 cd/m^2).
    Anchor: L(1) = 10**a = 0.0500 cd/m^2 (ln 1 = 0 kills every other term).
    """
    j = np.asarray(j, dtype=float)
    if np.any(j < 1.0) or np.any(j > 1023.0):
        raise ValueError("GSDF JND index must be within [1, 1023]")
    x = np.log(j)
    num = (
        _GSDF_A
        + _GSDF_C * x
        + _GSDF_E * x**2
        + _GSDF_G * x**3
        + _GSDF_M * x**4
    )
    den = (
        1.0
        + _GSDF_B * x
        + _GSDF_D * x**2
        + _GSDF_F * x**3
        + _GSDF_H * x**4
        + _GSDF_K * x**5
    )
    return 10.0 ** (num / den)


def gsdf_jnd_contrast(j):
    """Per-JND Weber contrast dL/L at index ``j`` (finite difference)."""
    j = np.asarray(j, dtype=float)
    lo = gsdf_luminance(j)
    hi = gsdf_luminance(j + 1.0)
    return (hi - lo) / lo


# --------------------------------------------------------------------------
# Display pixel-aperture MTF
# --------------------------------------------------------------------------


def display_pixel_mtf(f_mm, pixel_pitch_mm):
    """|sinc| MTF of a square pixel aperture with 100% fill factor.

    ``np.sinc(x)`` is sin(pi x)/(pi x), so the first zero sits at
    f = 1/pixel_pitch as required.
    """
    if pixel_pitch_mm <= 0:
        raise ValueError("pixel pitch must be positive")
    return np.abs(np.sinc(np.asarray(f_mm, dtype=float) * pixel_pitch_mm))


# --------------------------------------------------------------------------
# Eye optics (Barten 1999)
# --------------------------------------------------------------------------


def pupil_diameter_mm(luminance_cdm2, field_deg=40.0):
    """Average pupil diameter (mm) vs adaptation luminance.

    Barten (1999), eq. 2.5: d = 5 - 3 tanh(0.4 log10(L X0^2 / 40^2)).
    """
    L = np.asarray(luminance_cdm2, dtype=float)
    if np.any(L <= 0):
        raise ValueError("luminance must be positive")
    arg = 0.4 * np.log10(L * field_deg**2 / 40.0**2)
    return 5.0 - 3.0 * np.tanh(arg)


_SIGMA0_ARCMIN = 0.50   # intrinsic blur, arcmin (Barten 1999)
_CAB_ARCMIN_PER_MM = 0.08  # chromatic/aberration slope, arcmin per mm pupil


def eye_mtf(u_deg, pupil_mm):
    """Ocular optics MTF, Gaussian approximation (Barten 1999, eq. 2.3-2.4).

    M_opt(u) = exp(-2 pi^2 sigma^2 u^2), sigma in degrees.
    """
    u = np.asarray(u_deg, dtype=float)
    sigma_arcmin = np.sqrt(
        _SIGMA0_ARCMIN**2 + (_CAB_ARCMIN_PER_MM * pupil_mm) ** 2
    )
    sigma_deg = sigma_arcmin / 60.0
    return np.exp(-2.0 * np.pi**2 * sigma_deg**2 * u**2)


# --------------------------------------------------------------------------
# Barten CSF
# --------------------------------------------------------------------------

# Standard-observer parameters, Barten (1999; 2004 SPIE tutorial).
_BARTEN = dict(
    k=3.0,          # signal-to-noise threshold
    T=0.1,          # integration time, s
    Xmax=12.0,      # maximum integration field, deg
    Nmax=15.0,      # maximum number of cycles
    eta=0.03,       # quantum efficiency
    Phi0=3.0e-8,    # neural noise spectral density, s*deg^2
    u0=7.0,         # lateral-inhibition corner frequency, cpd
    p=1.240e6,      # photon conversion factor, photons/(s*deg^2*Td)
)


def _retinal_illuminance_td(luminance_cdm2, pupil_mm):
    """Retinal illuminance in Troland with Stiles-Crawford correction."""
    d = pupil_mm
    sc = 1.0 - (d / 9.7) ** 2 + (d / 12.4) ** 4
    return (np.pi * d**2 / 4.0) * luminance_cdm2 * sc


def barten_csf(u_deg, luminance_cdm2=100.0, field_deg=10.0):
    """Barten contrast sensitivity S(u) for the standard observer.

    Parameters
    ----------
    u_deg : array-like, spatial frequency at the eye [cycles/degree]
    luminance_cdm2 : adaptation luminance [cd/m^2]
    field_deg : angular field (object) size X0 [deg]
    """
    u = np.asarray(u_deg, dtype=float)
    if np.any(u < 0):
        raise ValueError("spatial frequency must be non-negative")
    B = _BARTEN
    pupil = pupil_diameter_mm(luminance_cdm2, field_deg=field_deg)
    E_td = _retinal_illuminance_td(luminance_cdm2, pupil)
    m_opt = eye_mtf(u, pupil)

    # avoid the u=0 singularity of the lateral-inhibition term
    u_safe = np.maximum(u, 1e-9)
    lateral = 1.0 - np.exp(-((u_safe / B["u0"]) ** 2))

    bandwidth = (2.0 / B["T"]) * (
        1.0 / field_deg**2 + 1.0 / B["Xmax"] ** 2 + u**2 / B["Nmax"] ** 2
    )
    noise = 1.0 / (B["eta"] * B["p"] * E_td) + B["Phi0"] / lateral
    return (m_opt / B["k"]) / np.sqrt(bandwidth * noise)


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------


def cycles_per_mm_to_cycles_per_degree(f_mm, viewing_distance_mm):
    """Convert display-plane frequency to angular frequency at the eye.

    One degree subtends ``viewing_distance * tan(1 deg)`` mm on the display,
    so u[cpd] = f[c/mm] * D * tan(1 deg).
    """
    if viewing_distance_mm <= 0:
        raise ValueError("viewing distance must be positive")
    mm_per_deg = viewing_distance_mm * np.tan(np.deg2rad(1.0))
    return np.asarray(f_mm, dtype=float) * mm_per_deg
