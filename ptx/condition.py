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
    """Acquisition and reconstruction condition.

    Two ways in. The CT path builds the transfer and noise from a reconstruction
    kernel, as the whole of phase 1 does; ``f50_lpmm`` overrides the kernel table,
    which is how the U-HRCT case study feeds published TTF values in without
    inventing a kernel name.

    The measured path takes tabulated MTF and NPS directly, for a system that is
    not a CT reconstruction. The formulation is stated for any linear system
    characterisable by MTF and NPS (protocol section 2.1), and until this path
    existed the code did not support that claim: every route in went through a CT
    kernel name. H2 pre-registration v2.0 section 7 requires it, because the
    second-round pool admits non-CT studies.

    Nothing downstream changes. ``build_chain`` asks this object for an MTF and an
    NPS on the working grid and hands them to the same ``assemble_chain``; the
    detectability formulation is untouched, and the CT path returns exactly what
    it returned before.

    ``slice_thickness_mm`` may be ``None``, meaning a projection: the task then
    carries no partial-volume loss, which is what a lesion imaged without slice
    selection has.
    """

    kernel: str = "standard"
    dose_relative: float = 1.0
    slice_thickness_mm: float | None = 1.0
    pixel_mm_object: float = 200.0 / 512.0
    kernel_sharpness: float = 2.0
    ramp_exponent: float = 1.0
    reference_kernel: str = "standard"
    reference_sd_hu: float = 50.0
    reference_slice_mm: float = 1.0
    f50_lpmm: float | None = None
    noise_scale_at_reference: float | None = None
    #: Tabulated ((frequency_lpmm, value), ...) pairs. Tuples rather than arrays so
    #: the condition stays frozen, comparable and JSON-serialisable: every result
    #: file records the configuration that produced it.
    mtf_points: tuple[tuple[float, float], ...] | None = None
    nps_points: tuple[tuple[float, float], ...] | None = None
    #: Where each curve came from. The pre-registration requires both to be
    #: non-empty for an admitted non-CT study, because a measured curve with no
    #: stated origin is an invented one.
    mtf_source: str = ""
    nps_source: str = ""

    def __post_init__(self):
        if self.measured:
            self._check_measured()
        else:
            if self.f50_lpmm is None and self.kernel not in CT_KERNEL_F50_LPMM:
                raise ValueError(f"unknown kernel: {self.kernel!r}")
            if self.reference_kernel not in CT_KERNEL_F50_LPMM:
                raise ValueError("unknown reference kernel")
            if self.slice_thickness_mm is None:
                raise ValueError(
                    "the CT path needs a slice thickness; pass measured MTF and NPS "
                    "for a projection"
                )
        if self.pixel_mm_object <= 0 or self.dose_relative <= 0:
            raise ValueError("pixel size and dose must be positive")
        if self.slice_thickness_mm is not None and self.slice_thickness_mm <= 0:
            raise ValueError("slice thickness must be positive when given")

    @property
    def measured(self) -> bool:
        return self.mtf_points is not None or self.nps_points is not None

    def _check_measured(self):
        if self.mtf_points is None or self.nps_points is None:
            raise ValueError(
                "a measured acquisition needs both an MTF and an NPS: one without "
                "the other would take the other from a CT kernel"
            )
        if not (self.mtf_source.strip() and self.nps_source.strip()):
            raise ValueError(
                "mtf_source and nps_source must say where the curves came from"
            )
        for name, points in (("mtf", self.mtf_points), ("nps", self.nps_points)):
            freqs = [float(x) for x, _ in points]
            values = [float(y) for _, y in points]
            if len(points) < 2:
                raise ValueError(f"{name} needs at least two points")
            if any(b <= a for a, b in zip(freqs, freqs[1:])):
                raise ValueError(f"{name} frequencies must increase strictly")
            if freqs[0] < 0:
                raise ValueError(f"{name} frequencies must be non-negative")
            if any(v < 0 for v in values):
                raise ValueError(f"{name} values must be non-negative")
        if self.mtf_points[0][0] > 0.0:
            raise ValueError(
                "the MTF must be given from zero frequency, where it is normalised "
                "to one; extrapolating to the origin would invent its low-frequency "
                "behaviour"
            )
        if abs(float(self.mtf_points[0][1]) - 1.0) > 1e-6:
            raise ValueError("the MTF must be normalised to 1 at zero frequency")

    def _interpolate(self, f, points, name):
        """Linear in frequency, held flat outside the tabulated range.

        Held rather than extrapolated: a measured curve says nothing above its
        last point, and a linear extrapolation of an MTF crosses zero and goes
        negative, which would silently invent a sign change.
        """
        f = np.asarray(f, dtype=float)
        xs = np.array([x for x, _ in points], dtype=float)
        ys = np.array([y for _, y in points], dtype=float)
        if f.max() > xs[-1] * (1.0 + 1e-9):
            raise ValueError(
                f"the working grid reaches {f.max():.3f} lp/mm and the {name} is "
                f"tabulated only to {xs[-1]:.3f} lp/mm; extend the table or narrow "
                "the grid rather than extrapolating"
            )
        return np.interp(f, xs, ys, left=ys[0], right=ys[-1])

    def mtf(self, f):
        """System transfer on the working grid."""
        if self.measured:
            return self._interpolate(f, self.mtf_points, "MTF")
        return ct_ttf(f, self.f50, self.kernel_sharpness)

    def nps(self, f):
        """Image noise power on the working grid, scaled by relative dose.

        The measured curve is taken at the dose its source reports, so the dose
        axis is applied here in the same inverse-proportional form the CT path
        uses. Doing it anywhere else would make a study's dose axis mean
        something different from phase 1's.
        """
        if self.measured:
            return self._interpolate(f, self.nps_points, "NPS") / float(
                self.dose_relative
            )
        return ct_nps(
            f,
            self.f50,
            self.kernel_sharpness,
            self.ramp_exponent,
            self.noise_scale,
        )

    @property
    def f50(self):
        if self.f50_lpmm is not None:
            return float(self.f50_lpmm)
        if self.measured:
            # Read off the tabulated curve rather than stored, so it cannot
            # disagree with the MTF the chain actually uses. Reported only; the
            # measured path never routes through it.
            xs = np.array([x for x, _ in self.mtf_points], dtype=float)
            ys = np.array([y for _, y in self.mtf_points], dtype=float)
            below = np.nonzero(ys < 0.5)[0]
            if not below.size:
                return float(xs[-1])
            i = below[0]
            x0, y0, x1, y1 = xs[i - 1], ys[i - 1], xs[i], ys[i]
            return float(x0 + (0.5 - y0) * (x1 - x0) / (y1 - y0))
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
    """H_effective / N_effective for one condition.

    The acquisition supplies its own transfer and noise, by kernel or by measured
    table. Everything after this line is the same for both.
    """
    return assemble_chain(
        f,
        acquisition.mtf(f),
        acquisition.nps(f),
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
