"""One reading condition, end to end (protocol section 5).

Phase 1, the uncertainty propagation and the U-HRCT case study all need the
same evaluation — acquisition and reading condition in, d'_human / f_sat /
R_perceptual out — so it lives here once. The split of the inputs mirrors what
each hypothesis varies:

- :class:`Acquisition` is what the scanner and reconstruction deliver
  (kernel, dose, slice, pixel size). H1 varies dose, H3 varies pixel size.
- :class:`Reading` is what the display and the observer contribute, including
  the two range parameters ``kappa`` and ``eta_cog`` that section 5.4
  propagates and never point-estimates.

All quantities are deterministic functions of these two objects: nothing here
draws random numbers.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from .chain import (
    CT_KERNEL_F50_LPMM,
    ChainSpectra,
    ViewingGeometry,
    assemble_chain,
    ct_nps,
    ct_nps_scale_for_variance,
    ct_ttf,
    quantum_noise_scaling,
    radial_band_integral,
)
from .detectability import contribution_density, dprime_squared, f_sat
from .observer import ideal_dprime_squared
from .phantom_lung import nodule_task_spectrum

__all__ = [
    "Acquisition",
    "Reading",
    "Task",
    "Evaluation",
    "frequency_grid",
    "build_chain",
    "evaluate",
]


@dataclasses.dataclass(frozen=True)
class Acquisition:
    """Scanner and reconstruction condition.

    ``f50_lpmm`` overrides the kernel table, which is how the U-HRCT case
    study feeds published TTF values in without inventing a kernel name.
    """

    kernel: str = "standard"
    dose_relative: float = 1.0
    slice_thickness_mm: float = 1.0
    pixel_mm_object: float = 200.0 / 512.0
    kernel_sharpness: float = 2.0
    ramp_exponent: float = 1.0
    reference_kernel: str = "standard"
    reference_sd_hu: float = 50.0
    reference_slice_mm: float = 1.0
    f50_lpmm: float | None = None
    noise_scale_at_reference: float | None = None

    def __post_init__(self):
        if self.f50_lpmm is None and self.kernel not in CT_KERNEL_F50_LPMM:
            raise ValueError(f"unknown kernel: {self.kernel!r}")
        if self.reference_kernel not in CT_KERNEL_F50_LPMM:
            raise ValueError("unknown reference kernel")
        if self.pixel_mm_object <= 0 or self.dose_relative <= 0:
            raise ValueError("pixel size and dose must be positive")

    @property
    def f50(self):
        if self.f50_lpmm is not None:
            return float(self.f50_lpmm)
        return CT_KERNEL_F50_LPMM[self.kernel]

    @property
    def nyquist_lpmm(self):
        return 0.5 / self.pixel_mm_object

    @property
    def noise_scale(self):
        """NPS scale: one projection-noise level, shared by all kernels.

        Fixing the scale from a reference condition rather than per kernel is
        what makes a sharper kernel pay for its resolution in noise.

        ``noise_scale_at_reference`` sets that level explicitly, which is what
        comparing two pixel sizes at equal dose requires: the dose fixes the
        projection noise, not the pixel variance, so deriving the scale from a
        per-chain pixel-variance target would quietly hand the finer chain a
        noise advantage it does not have.
        """
        if self.noise_scale_at_reference is not None:
            reference = float(self.noise_scale_at_reference)
        else:
            reference = ct_nps_scale_for_variance(
                self.reference_sd_hu**2,
                self.nyquist_lpmm,
                CT_KERNEL_F50_LPMM[self.reference_kernel],
                self.kernel_sharpness,
                self.ramp_exponent,
            )
        return reference * quantum_noise_scaling(
            self.dose_relative, self.slice_thickness_mm, self.reference_slice_mm
        )


@dataclasses.dataclass(frozen=True)
class Reading:
    """Display, viewing geometry and the observer's range parameters."""

    zoom: float = 1.0
    distance_mm: float = 500.0
    luminance_cdm2: float = 100.0
    field_deg: float = 10.0
    display_pitch_mm: float = 0.2
    window_width_hu: float = 1500.0
    n_grey_levels: int | None = 256
    kappa: float = 1.0
    eta_cog: float = 0.5

    def viewing(self, acquisition):
        return ViewingGeometry(
            pixel_mm_object=acquisition.pixel_mm_object,
            display_pitch_mm=self.display_pitch_mm,
            zoom=self.zoom,
            distance_mm=self.distance_mm,
            luminance_cdm2=self.luminance_cdm2,
            field_deg=self.field_deg,
        )


@dataclasses.dataclass(frozen=True)
class Task:
    """Detection task: a nodule of given size and contrast."""

    diameter_mm: float
    contrast_hu: float

    def spectrum(self, f, slice_thickness_mm):
        return nodule_task_spectrum(
            f, self.diameter_mm, self.contrast_hu, slice_thickness_mm
        )


@dataclasses.dataclass(frozen=True)
class Evaluation:
    """Result of one condition: scalars plus the spectra they came from."""

    f: np.ndarray
    chain: ChainSpectra
    w_task: np.ndarray
    density: np.ndarray
    dprime_human: float
    dprime_ideal: float
    r_perceptual: float
    f_sat: dict
    neural_noise_share: float
    quantisation_noise_share: float

    def scalars(self):
        """The JSON-serialisable part, without the spectra."""
        out = {
            "dprime_human": self.dprime_human,
            "dprime_ideal": self.dprime_ideal,
            "r_perceptual": self.r_perceptual,
            "neural_noise_share": self.neural_noise_share,
            "quantisation_noise_share": self.quantisation_noise_share,
        }
        for fraction, value in self.f_sat.items():
            out[f"f_sat_{int(round(fraction * 100))}_lpmm"] = value
        return out


def frequency_grid(acquisition, n_freq=2048):
    """Object-frequency grid up to Nyquist.

    The radial measure 2 pi f suppresses f -> 0, so the grid starts one step
    above zero, which also keeps N_effective strictly positive there.
    """
    nyquist = acquisition.nyquist_lpmm
    return np.linspace(nyquist / n_freq, nyquist, n_freq)


def build_chain(f, acquisition, reading):
    """H_effective / N_effective for one condition."""
    f50 = acquisition.f50
    return assemble_chain(
        f,
        ct_ttf(f, f50, acquisition.kernel_sharpness),
        ct_nps(
            f,
            f50,
            acquisition.kernel_sharpness,
            acquisition.ramp_exponent,
            acquisition.noise_scale,
        ),
        reading.viewing(acquisition),
        window_width_hu=reading.window_width_hu,
        n_grey_levels=reading.n_grey_levels,
        neural_noise_kappa=reading.kappa,
    )


def evaluate(f, task, acquisition, reading, fractions=(0.95,)):
    """Evaluate one condition in the v0.4 primary form."""
    chain = build_chain(f, acquisition, reading)
    w_task = task.spectrum(f, acquisition.slice_thickness_mm)
    unit = np.ones_like(f)

    density = contribution_density(
        f, w_task, chain.h_eff, unit, chain.n_eff,
        eta_cog=reading.eta_cog, radial=True,
    )
    d2_human = dprime_squared(
        f, w_task, chain.h_eff, unit, chain.n_eff,
        eta_cog=reading.eta_cog, radial=True,
    )
    d2_ideal = ideal_dprime_squared(
        f, w_task, chain.n_image, transfer=chain.h_scanner, radial=True
    )
    total_noise = radial_band_integral(f, chain.n_eff)

    return Evaluation(
        f=f,
        chain=chain,
        w_task=w_task,
        density=density,
        dprime_human=float(np.sqrt(d2_human)),
        dprime_ideal=float(np.sqrt(d2_ideal)),
        r_perceptual=float(np.sqrt(d2_human / d2_ideal)),
        f_sat={
            fraction: f_sat(f, density, fraction=fraction)
            for fraction in fractions
        },
        neural_noise_share=float(
            radial_band_integral(f, chain.n_neural) / total_noise
        ),
        quantisation_noise_share=float(
            radial_band_integral(f, chain.n_quantisation * chain.h_eye**2)
            / total_noise
        ),
    )
