"""Acquisition, display and visual-system transfer chain (protocol section 5).

Every component is implemented independently from the primary literature /
standard and cross-checked against published anchor values in ``tests/``:

- ``gsdf_luminance``       DICOM PS3.14 Grayscale Standard Display Function
- ``display_pixel_mtf``    pixel-aperture MTF of the display
- ``pupil_diameter_mm``    luminance-dependent pupil model (Barten 1999)
- ``eye_mtf``              ocular optics MTF (Gaussian approximation, Barten 1999)
- ``barten_csf``           Barten contrast sensitivity function (Barten 1999/2004)
- ``barten_visual_noise_density``  the internal noise that CSF is derived from
- ``ct_ttf`` / ``ct_nps``  CT acquisition stage (H_scanner, N_image)
- ``assemble_chain``       H_effective and N_effective of section 5.1

Units convention:
- spatial frequency in the object (patient) plane: cycles/mm (``f_obj``)
- spatial frequency on the display plane:          cycles/mm (``f_mm``)
- spatial frequency at the eye:                    cycles/degree (``u_deg``)
- luminance: cd/m^2;  CT attenuation: HU;  noise power: HU^2 mm^2
"""

from __future__ import annotations

import dataclasses
from functools import lru_cache

import numpy as np

__all__ = [
    "gsdf_luminance",
    "gsdf_jnd_contrast",
    "display_pixel_mtf",
    "pupil_diameter_mm",
    "eye_mtf",
    "barten_csf",
    "barten_csf_peak",
    "barten_integration_area_deg2",
    "barten_visual_noise_density",
    "cycles_per_mm_to_cycles_per_degree",
    "radial_band_integral",
    "CT_KERNEL_F50_LPMM",
    "ct_ttf",
    "ct_nps",
    "ct_nps_variance",
    "ct_nps_scale_for_variance",
    "quantum_noise_scaling",
    "ViewingGeometry",
    "display_quantisation_noise_power",
    "neural_noise_power",
    "ChainSpectra",
    "assemble_chain",
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


def barten_integration_area_deg2(u_deg, field_deg=10.0):
    """Effective visual integration area A_int(u) [deg^2] (Barten 1999).

    The inverse of Barten's spatial bandwidth term,
    ``1/X0^2 + 1/Xmax^2 + u^2/Nmax^2``: the observer integrates over the
    stimulus field, but never over more than Xmax degrees or Nmax cycles.
    """
    u = np.asarray(u_deg, dtype=float)
    if np.any(u < 0):
        raise ValueError("spatial frequency must be non-negative")
    if field_deg <= 0:
        raise ValueError("field size must be positive")
    B = _BARTEN
    return 1.0 / (
        1.0 / field_deg**2 + 1.0 / B["Xmax"] ** 2 + u**2 / B["Nmax"] ** 2
    )


def barten_visual_noise_density(u_deg, luminance_cdm2=100.0, field_deg=10.0):
    """Spatial noise density of the visual system [modulation^2 deg^2].

    Barten's photon noise plus lateral-inhibition-shaped neural noise, divided
    by the temporal integration time. This is the internal noise the CSF is
    *derived* from, so using it in N_effective and using the CSF as a
    numerator weight are two descriptions of one model, related by

        Phi(u) = A_int(u) / (2 k^2 S_neural(u)^2)

    which ``tests/`` checks identically. IORN-009A v0.4 takes this noise form
    as primary: a weight in the numerator cancels against the noise it is
    supposed to limit (see paper/NOTES.md), a noise term does not.
    """
    u = np.asarray(u_deg, dtype=float)
    if np.any(u < 0):
        raise ValueError("spatial frequency must be non-negative")
    B = _BARTEN
    pupil = pupil_diameter_mm(luminance_cdm2, field_deg=field_deg)
    E_td = _retinal_illuminance_td(luminance_cdm2, pupil)
    u_safe = np.maximum(u, 1e-9)
    lateral = 1.0 - np.exp(-((u_safe / B["u0"]) ** 2))
    photon = 1.0 / (B["eta"] * B["p"] * E_td)
    return (photon + B["Phi0"] / lateral) / B["T"]


def barten_csf(u_deg, luminance_cdm2=100.0, field_deg=10.0, include_optics=True):
    """Barten contrast sensitivity S(u) for the standard observer.

    Parameters
    ----------
    u_deg : array-like, spatial frequency at the eye [cycles/degree]
    luminance_cdm2 : adaptation luminance [cd/m^2]
    field_deg : angular field (object) size X0 [deg]
    include_optics : if False the ocular MTF factor is left out, returning the
        *neural* sensitivity. Barten's CSF already contains ``eye_mtf``, so a
        chain that carries ``eye_mtf`` explicitly in H_effective (section 5.1)
        must use ``include_optics=False`` to avoid counting the optics twice.
        By construction ``eye_mtf(u) * barten_csf(u, include_optics=False)``
        equals ``barten_csf(u)``.
    """
    u = np.asarray(u_deg, dtype=float)
    if np.any(u < 0):
        raise ValueError("spatial frequency must be non-negative")
    B = _BARTEN
    pupil = pupil_diameter_mm(luminance_cdm2, field_deg=field_deg)
    E_td = _retinal_illuminance_td(luminance_cdm2, pupil)

    # avoid the u=0 singularity of the lateral-inhibition term
    u_safe = np.maximum(u, 1e-9)
    lateral = 1.0 - np.exp(-((u_safe / B["u0"]) ** 2))

    bandwidth = (2.0 / B["T"]) * (
        1.0 / field_deg**2 + 1.0 / B["Xmax"] ** 2 + u**2 / B["Nmax"] ** 2
    )
    noise = 1.0 / (B["eta"] * B["p"] * E_td) + B["Phi0"] / lateral
    csf = (1.0 / B["k"]) / np.sqrt(bandwidth * noise)
    if include_optics:
        csf = csf * eye_mtf(u, pupil)
    return csf


@lru_cache(maxsize=256)
def barten_csf_peak(
    luminance_cdm2=100.0, field_deg=10.0, include_optics=True,
    u_max_deg=60.0, samples=4096,
):
    """Peak of the Barten CSF, scanned on a fixed deterministic grid.

    Used to normalise the visual weighting to unit peak so that
    ``R_perceptual`` is a utilisation ratio (the absolute sensitivity scale is
    absorbed into ``eta_cog``, protocol section 5.3).
    """
    if u_max_deg <= 0 or samples < 2:
        raise ValueError("need a positive frequency range and >= 2 samples")
    u = np.linspace(u_max_deg / samples, u_max_deg, samples)
    s = barten_csf(u, luminance_cdm2, field_deg, include_optics=include_optics)
    return float(np.max(s))


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


def radial_band_integral(f, power):
    """Isotropic 2-D integral ``int power d^2f = 2 pi int power f df``.

    The trapezoid runs over the supplied 1-D radial grid, so the caller
    controls the band limits.
    """
    f = np.asarray(f, dtype=float)
    p = np.asarray(power, dtype=float)
    if f.ndim != 1 or f.shape != p.shape:
        raise ValueError("f and power must be matching 1-D arrays")
    return float(2.0 * np.pi * np.trapezoid(p * f, f))


# --------------------------------------------------------------------------
# CT acquisition stage: H_scanner and N_image (protocol section 5.3)
# --------------------------------------------------------------------------

# Representative in-plane f_50 values (lp/mm) spanning the range published for
# clinical CT reconstruction kernels. Phase 1 treats these as *experimental
# variables* (protocol section 7) — they are not claims about any particular
# scanner. The U-HRCT case study (M3) substitutes published TTF/MTF values.
CT_KERNEL_F50_LPMM = {
    "smooth": 0.30,
    "standard": 0.50,
    "sharp": 0.75,
    "ultra_high_resolution": 1.30,
}


def ct_ttf(f_mm, f50_lpmm, sharpness=2.0):
    """Lumped CT task transfer function, generalised-Gaussian form.

    ``TTF(f) = exp(-ln2 (f/f50)^sharpness)`` so that ``TTF(0) = 1`` and
    ``TTF(f50) = 0.5`` exactly, which is how CT TTF is reported (f_50).
    The single lumped factor stands for detector aperture, focal spot and
    reconstruction kernel together; ``ct_nps`` shapes the noise with the same
    factor, as an FBP-like chain requires (see that docstring).
    """
    if f50_lpmm <= 0:
        raise ValueError("f50 must be positive")
    if sharpness <= 0:
        raise ValueError("sharpness must be positive")
    f = np.asarray(f_mm, dtype=float)
    if np.any(f < 0):
        raise ValueError("spatial frequency must be non-negative")
    return np.exp(-np.log(2.0) * (f / f50_lpmm) ** sharpness)


def ct_nps(f_mm, f50_lpmm, sharpness=2.0, ramp_exponent=1.0, scale=1.0):
    """Radial NPS of an FBP-like CT reconstruction [HU^2 mm^2].

    ``NPS(f) = scale * f^ramp * TTF(f)^2``. The ramp factor is the standard
    2-D FBP result (the |f| Jacobian of back-projection); the squared transfer
    factor is the same lumped filter that blurs the signal, because the
    quantum noise of the projections passes through the identical aperture and
    kernel. ``ramp_exponent=0`` gives a white field, which the tests use as an
    analytic anchor.

    ``scale`` carries the projection-noise level: it is set once from a
    reference variance (``ct_nps_scale_for_variance``) and then divided by
    dose and slice thickness (``quantum_noise_scaling``), so a sharper kernel
    automatically costs noise instead of being free.
    """
    if scale < 0:
        raise ValueError("scale must be non-negative")
    if ramp_exponent < 0:
        raise ValueError("ramp exponent must be non-negative")
    f = np.asarray(f_mm, dtype=float)
    return scale * f**ramp_exponent * ct_ttf(f, f50_lpmm, sharpness) ** 2


def ct_nps_variance(
    f_nyquist_lpmm, f50_lpmm, sharpness=2.0, ramp_exponent=1.0, scale=1.0,
    samples=4096,
):
    """Pixel variance implied by ``ct_nps`` over the disk |f| <= f_nyquist.

    ``var = int NPS d^2f``, the standard NPS/variance identity. The isotropic
    model integrates the disk rather than the square sampling band.
    """
    if f_nyquist_lpmm <= 0:
        raise ValueError("Nyquist frequency must be positive")
    if samples < 2:
        raise ValueError("need >= 2 samples")
    f = np.linspace(0.0, f_nyquist_lpmm, samples)
    nps = ct_nps(f, f50_lpmm, sharpness, ramp_exponent, scale)
    return radial_band_integral(f, nps)


def ct_nps_scale_for_variance(
    target_variance_hu2, f_nyquist_lpmm, f50_lpmm, sharpness=2.0,
    ramp_exponent=1.0, samples=4096,
):
    """``scale`` making ``ct_nps`` integrate to ``target_variance_hu2``."""
    if target_variance_hu2 <= 0:
        raise ValueError("target variance must be positive")
    unit = ct_nps_variance(
        f_nyquist_lpmm, f50_lpmm, sharpness, ramp_exponent, scale=1.0,
        samples=samples,
    )
    if unit <= 0:
        raise ValueError("degenerate NPS shape")
    return target_variance_hu2 / unit


def quantum_noise_scaling(
    dose_relative, slice_thickness_mm, slice_reference_mm=1.0
):
    """Variance multiplier for quantum-limited CT noise.

    Variance scales as 1/(dose x slice thickness): both multiply the number of
    detected quanta per voxel.
    """
    if dose_relative <= 0 or slice_thickness_mm <= 0:
        raise ValueError("dose and slice thickness must be positive")
    if slice_reference_mm <= 0:
        raise ValueError("reference slice thickness must be positive")
    return 1.0 / (dose_relative * slice_thickness_mm / slice_reference_mm)


# --------------------------------------------------------------------------
# Viewing geometry: object -> display -> eye
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ViewingGeometry:
    """Reading conditions that map object frequency to angular frequency.

    ``zoom`` is display pixels per reconstructed image pixel (1.0 = 1:1), the
    display magnification knob of hypothesis H3.
    """

    pixel_mm_object: float
    display_pitch_mm: float = 0.2
    zoom: float = 1.0
    distance_mm: float = 500.0
    luminance_cdm2: float = 100.0
    field_deg: float = 10.0

    def __post_init__(self):
        for name in (
            "pixel_mm_object", "display_pitch_mm", "zoom", "distance_mm",
            "luminance_cdm2", "field_deg",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")

    @property
    def magnification(self):
        """mm on the display per mm in the object."""
        return self.zoom * self.display_pitch_mm / self.pixel_mm_object

    @property
    def nyquist_object_lpmm(self):
        """Sampling Nyquist frequency of the reconstruction [lp/mm]."""
        return 0.5 / self.pixel_mm_object

    @property
    def pupil_mm(self):
        return float(
            pupil_diameter_mm(self.luminance_cdm2, field_deg=self.field_deg)
        )

    @property
    def object_mm_per_degree(self):
        """mm in the *object* subtended by one degree of visual angle.

        The single scale factor linking the two frequency axes
        (``u = object_mm_per_degree * f_obj``) and the factor by which an
        angular noise density converts into object-referred noise power.
        """
        return (
            self.distance_mm * np.tan(np.deg2rad(1.0)) / self.magnification
        )

    def display_frequency(self, f_obj):
        """Object frequency [c/mm] -> display-plane frequency [c/mm]."""
        return np.asarray(f_obj, dtype=float) / self.magnification

    def angular_frequency(self, f_obj):
        """Object frequency [c/mm] -> angular frequency at the eye [c/deg]."""
        return np.asarray(f_obj, dtype=float) * self.object_mm_per_degree


# --------------------------------------------------------------------------
# Noise floors that survive the display and the observer
# --------------------------------------------------------------------------


def display_quantisation_noise_power(
    window_width_hu, n_grey_levels, viewing
):
    """White noise power [HU^2 mm^2] from display grey-level quantisation.

    A window width WW mapped onto n displayed grey levels quantises with step
    WW/n and variance step^2/12 (uniform quantiser). That noise is white on
    the *display* raster, one sample of which covers
    ``pixel_mm_object / zoom`` in the object, so the object-referred power is
    variance x sample area. Zooming in therefore lowers the floor, which is
    the constructive half of H3.
    """
    if window_width_hu <= 0:
        raise ValueError("window width must be positive")
    if n_grey_levels < 2:
        raise ValueError("need at least 2 grey levels")
    step = window_width_hu / n_grey_levels
    sample_mm = viewing.pixel_mm_object / viewing.zoom
    return (step**2 / 12.0) * sample_mm**2


def neural_noise_power(f, viewing, window_width_hu, kappa=1.0):
    """Visual internal noise referred to the object [HU^2 mm^2].

    Barten's angular noise density is converted to object-referred noise power
    by the two changes of variable the chain implies: contrast is read against
    the display window (``modulation = dHU / window_width``, one window width
    spanning full modulation) and angle is read against the object
    (``a = object_mm_per_degree``):

        N_neural(f) = kappa^2 (WW a)^2 Phi(a f)

    ``kappa`` is dimensionless and defaults to 1, i.e. Barten's standard
    observer exactly as published; it is the literature range parameter that
    M3 propagates (protocol sections 5.3, 5.4), never a fitted value.
    """
    if kappa < 0:
        raise ValueError("kappa must be non-negative")
    if window_width_hu <= 0:
        raise ValueError("window width must be positive")
    f = np.asarray(f, dtype=float)
    if kappa == 0.0:
        return np.zeros_like(f)
    a = viewing.object_mm_per_degree
    phi = barten_visual_noise_density(
        viewing.angular_frequency(f), viewing.luminance_cdm2, viewing.field_deg
    )
    return kappa**2 * (window_width_hu * a) ** 2 * phi


# --------------------------------------------------------------------------
# Assembled chain (protocol section 5.1)
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ChainSpectra:
    """H_effective / N_effective and every stage that went into them.

    N_effective carries the three terms of protocol section 5.1 (v0.4), each
    entering where it is physically injected:

    - ``n_image`` at the scanner, so display and ocular MTF both act on it
    - ``n_quantisation`` at the display, so only the ocular MTF acts on it
    - ``n_neural`` inside the observer, filtered by nothing

    Keeping the last two outside |H_display|^2 is what lets pixel pitch and
    magnification influence detectability at all: a term that shares every
    factor with the signal cancels out of the ratio.
    """

    f_obj: np.ndarray
    u_deg: np.ndarray
    h_scanner: np.ndarray
    h_display: np.ndarray
    h_eye: np.ndarray
    csf_neural: np.ndarray
    csf_peak: float
    n_image: np.ndarray
    n_quantisation: np.ndarray
    n_neural: np.ndarray

    @property
    def h_eff(self):
        return self.h_scanner * self.h_display * self.h_eye

    @property
    def csf_weight(self):
        """Neural CSF normalised to unit peak.

        Only the superseded v0.3 numerator-weight form (kept as the ideal
        limit of the appendix) and the model observers use this; the primary
        integral gets its visual sensitivity from ``n_neural``.
        """
        return self.csf_neural / self.csf_peak

    @property
    def displayed_image_noise(self):
        return self.n_image * (self.h_display * self.h_eye) ** 2

    @property
    def n_eff(self):
        return (
            self.displayed_image_noise
            + self.n_quantisation * self.h_eye**2
            + self.n_neural
        )


def assemble_chain(
    f_obj,
    h_scanner,
    n_image,
    viewing,
    window_width_hu,
    n_grey_levels=None,
    neural_noise_kappa=1.0,
):
    """Build :class:`ChainSpectra` for one reading condition.

    The visual stage is split into the ocular MTF, which stays in
    H_effective, and the neural stage, which enters N_effective as
    ``neural_noise_power``. Both come from the same Barten model, so the
    optics are counted exactly once: ``csf_neural`` (optics divided out) is
    retained only for the observer models and the appendix form.

    ``window_width_hu`` is required because it fixes the HU-to-modulation
    reference of the visual noise; ``n_grey_levels=None`` switches the display
    quantisation floor off, ``neural_noise_kappa=0`` the neural floor.
    """
    f = np.asarray(f_obj, dtype=float)
    h_scan = np.asarray(h_scanner, dtype=float)
    n_img = np.asarray(n_image, dtype=float)
    if not (f.shape == h_scan.shape == n_img.shape):
        raise ValueError("f_obj, h_scanner and n_image must share one grid")

    u = viewing.angular_frequency(f)
    h_display = display_pixel_mtf(
        viewing.display_frequency(f), viewing.display_pitch_mm
    )
    h_eye = eye_mtf(u, viewing.pupil_mm)
    csf_neural = barten_csf(
        u, viewing.luminance_cdm2, viewing.field_deg, include_optics=False
    )
    csf_peak = barten_csf_peak(
        viewing.luminance_cdm2, viewing.field_deg, include_optics=False
    )

    if n_grey_levels is None:
        n_quant = np.zeros_like(f)
    else:
        n_quant = np.full_like(
            f,
            display_quantisation_noise_power(
                window_width_hu, n_grey_levels, viewing
            ),
        )

    return ChainSpectra(
        f_obj=f,
        u_deg=u,
        h_scanner=h_scan,
        h_display=h_display,
        h_eye=h_eye,
        csf_neural=csf_neural,
        csf_peak=csf_peak,
        n_image=n_img,
        n_quantisation=n_quant,
        n_neural=neural_noise_power(
            f, viewing, window_width_hu, neural_noise_kappa
        ),
    )
