"""Phase 1 experiment: does d'_human saturate? (protocol section 7)

Runs the full condition grid of section 7 through the closed-form chain of
section 5, and writes a results.json that downstream figures and manuscript
text read from (design principle no. 2 — no hand-typed numbers).

The headline numbers use the v0.4 primary form, in which the visual system
enters through N_effective (Barten's own internal noise). The superseded v0.3
form, with the CSF as a numerator weight, is evaluated alongside it and
reported as ``*_csf_weight``: it is the ideal limit of the appendix, and the
kernel invariance it exhibits is kept as a validation result rather than
discarded.

Everything is analytic and deterministic: no random draws enter Phase 1, so
the same configuration reproduces the same file byte for byte.

    python -m ptx.phase1 --out results/phase1.json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import platform
from itertools import product
from pathlib import Path

import numpy as np
from scipy import stats

from . import __version__
from .chain import CT_KERNEL_F50_LPMM
from .condition import (
    Acquisition,
    Reading,
    Task,
    build_chain,
    evaluate,
    frequency_grid,
)
from .detectability import dprime_squared, g_useful
from .observer import (
    cho_dprime_squared,
    dog_channels_spanning,
    npwe_dprime_squared,
)
from .phantom_lung import disk_first_zero_lpmm

__all__ = ["Phase1Config", "run_phase1", "main"]


@dataclasses.dataclass(frozen=True)
class Phase1Config:
    """Condition grid and fixed reading conditions of protocol section 7.

    Contrast levels stand for a ground-glass and a solid nodule against
    parenchyma at -850 HU. Dose is relative to the routine level, so the
    absolute mAs never enters the model.
    """

    diameters_mm: tuple = (4.0, 6.0, 8.0)
    contrasts_hu: tuple = (250.0, 880.0)
    doses_relative: tuple = (0.25, 0.5, 1.0, 2.0, 4.0)
    slice_thicknesses_mm: tuple = (0.5, 1.0, 3.0)
    kernels: tuple = ("smooth", "standard", "sharp")
    zooms: tuple = (1.0, 2.0)

    # reconstruction and reading conditions
    pixel_mm_object: float = 200.0 / 512.0   # 200 mm targeted FOV, 512 matrix
    display_pitch_mm: float = 0.2
    viewing_distance_mm: float = 500.0
    luminance_cdm2: float = 100.0
    field_deg: float = 10.0
    window_width_hu: float = 1500.0
    n_grey_levels: int = 256

    # noise model
    kernel_sharpness: float = 2.0
    ramp_exponent: float = 1.0
    reference_kernel: str = "standard"
    reference_sd_hu: float = 50.0
    reference_slice_mm: float = 1.0
    # 1.0 = Barten's standard observer as published; M3 propagates the range
    neural_noise_kappa: float = 1.0

    # observer and integration
    eta_cog: float = 0.5
    n_freq: int = 2048
    n_channels: int = 10
    channel_noise_fraction: float = 0.0
    # lowest CHO channel peak, as a fraction of the first zero of the task
    # spectrum, so the channel set always covers the task's main lobe
    channel_low_frequency_fraction: float = 0.25
    fractions: tuple = (0.90, 0.95, 0.99)

    def __post_init__(self):
        unknown = set(self.kernels) - set(CT_KERNEL_F50_LPMM)
        if unknown:
            raise ValueError(f"unknown kernels: {sorted(unknown)}")
        if self.reference_kernel not in CT_KERNEL_F50_LPMM:
            raise ValueError("unknown reference kernel")
        if self.n_freq < 16 or self.n_channels < 1:
            raise ValueError("n_freq and n_channels must be usable")


def _condition_key(condition):
    return (
        condition["diameter_mm"],
        condition["contrast_hu"],
        condition["slice_thickness_mm"],
        condition["kernel"],
        condition["zoom"],
    )


def _acquisition(cfg, kernel, dose, thickness):
    return Acquisition(
        kernel=kernel,
        dose_relative=dose,
        slice_thickness_mm=thickness,
        pixel_mm_object=cfg.pixel_mm_object,
        kernel_sharpness=cfg.kernel_sharpness,
        ramp_exponent=cfg.ramp_exponent,
        reference_kernel=cfg.reference_kernel,
        reference_sd_hu=cfg.reference_sd_hu,
        reference_slice_mm=cfg.reference_slice_mm,
    )


def _reading(cfg, zoom):
    return Reading(
        zoom=zoom,
        distance_mm=cfg.viewing_distance_mm,
        luminance_cdm2=cfg.luminance_cdm2,
        field_deg=cfg.field_deg,
        display_pitch_mm=cfg.display_pitch_mm,
        window_width_hu=cfg.window_width_hu,
        n_grey_levels=cfg.n_grey_levels,
        kappa=cfg.neural_noise_kappa,
        eta_cog=cfg.eta_cog,
    )


def run_phase1(config=None):
    """Evaluate the Phase 1 grid and return the results dictionary."""
    cfg = config or Phase1Config()

    reference = _acquisition(cfg, cfg.reference_kernel, 1.0, cfg.reference_slice_mm)
    nyquist = reference.nyquist_lpmm
    f = frequency_grid(reference, cfg.n_freq)
    channels_by_diameter = {
        d: dog_channels_spanning(
            f,
            nyquist,
            cfg.n_channels,
            f_min=cfg.channel_low_frequency_fraction
            * disk_first_zero_lpmm(d),
        )
        for d in cfg.diameters_mm
    }

    conditions = []
    for diameter, contrast, dose, thickness, kernel, zoom in product(
        cfg.diameters_mm,
        cfg.contrasts_hu,
        cfg.doses_relative,
        cfg.slice_thicknesses_mm,
        cfg.kernels,
        cfg.zooms,
    ):
        acquisition = _acquisition(cfg, kernel, dose, thickness)
        reading = _reading(cfg, zoom)
        task = Task(diameter_mm=diameter, contrast_hu=contrast)
        result = evaluate(f, task, acquisition, reading, cfg.fractions)
        chain = result.chain

        # superseded v0.3 form, kept as the ideal limit of the appendix
        d2_csf_weight = dprime_squared(
            f, result.w_task, chain.h_eff, chain.csf_weight, chain.n_eff,
            eta_cog=cfg.eta_cog, radial=True,
        )
        displayed_signal = result.w_task * chain.h_eff
        d2_npwe = npwe_dprime_squared(
            f, displayed_signal, chain.n_eff, eye_filter=chain.csf_weight,
            radial=True,
        )
        d2_cho = cho_dprime_squared(
            f, displayed_signal, chain.n_eff, channels_by_diameter[diameter],
            visual_filter=chain.csf_weight,
            channel_noise_fraction=cfg.channel_noise_fraction, radial=True,
        )

        record = {
            "diameter_mm": diameter,
            "contrast_hu": contrast,
            "dose_relative": dose,
            "slice_thickness_mm": thickness,
            "kernel": kernel,
            "kernel_f50_lpmm": acquisition.f50,
            "zoom": zoom,
            "nyquist_lpmm": nyquist,
            "dprime_human_csf_weight": float(np.sqrt(d2_csf_weight)),
            "dprime_npwe": float(np.sqrt(d2_npwe)),
            "dprime_cho": float(np.sqrt(d2_cho)),
        }
        record.update(result.scalars())
        conditions.append(record)

    series = _dose_series(conditions)
    summary = _summary(conditions, series, nyquist)
    summary["invertible_filter_invariance"] = _invariance_validation(cfg, f)
    return {
        "metadata": _metadata(cfg, nyquist),
        "conditions": conditions,
        "dose_series": series,
        "summary": summary,
    }


def _invariance_validation(cfg, f):
    """Invertible-filter invariance, kept as a validation result.

    With both noise floors switched off the reconstruction kernel filters
    signal and noise by the same factor, so it must drop out of the
    detectability integral exactly — in either the primary or the superseded
    numerator-weight form. The residual spread is a numerical accuracy
    statement about the implementation, and it is what makes the *physical*
    kernel sensitivity reported above interpretable: the latter is entirely
    the footprint of the neural noise that bypasses the kernel.
    """
    reading = dataclasses.replace(
        _reading(cfg, cfg.zooms[0]), n_grey_levels=None, kappa=0.0
    )
    task = Task(
        diameter_mm=cfg.diameters_mm[0], contrast_hu=cfg.contrasts_hu[0]
    )
    w_task = task.spectrum(f, cfg.slice_thicknesses_mm[0])
    unit = np.ones_like(f)
    primary, weighted = [], []
    for kernel in cfg.kernels:
        chain = build_chain(
            f,
            _acquisition(cfg, kernel, 1.0, cfg.reference_slice_mm),
            reading,
        )
        primary.append(
            dprime_squared(f, w_task, chain.h_eff, unit, chain.n_eff, radial=True)
        )
        weighted.append(
            dprime_squared(
                f, w_task, chain.h_eff, chain.csf_weight, chain.n_eff,
                radial=True,
            )
        )
    return {
        "kernels": list(cfg.kernels),
        "floors": "off (no quantisation, kappa = 0)",
        "max_relative_dprime2_spread_primary_form": _relative_spread(primary),
        "max_relative_dprime2_spread_csf_weight_form": _relative_spread(
            weighted
        ),
    }


def _relative_spread(values):
    values = np.asarray(values, dtype=float)
    peak = float(np.max(values))
    if peak <= 0:
        return 0.0
    return float((peak - float(np.min(values))) / peak)


def _metadata(cfg, nyquist):
    return {
        "protocol": "IORN-009A v0.4, section 7 (Phase 1)",
        "detectability_form": (
            "primary: visual sensitivity in N_effective (v0.4 section 5.2); "
            "dprime_human_csf_weight is the superseded v0.3 numerator-weight "
            "form, retained as the ideal limit of the appendix"
        ),
        "ptx_version": __version__,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "config": dataclasses.asdict(cfg),
        "nyquist_lpmm": nyquist,
        "n_conditions": (
            len(cfg.diameters_mm)
            * len(cfg.contrasts_hu)
            * len(cfg.doses_relative)
            * len(cfg.slice_thicknesses_mm)
            * len(cfg.kernels)
            * len(cfg.zooms)
        ),
    }


def _dose_series(conditions):
    """G_useful = d(d')/dD for every series that varies only in dose."""
    grouped = {}
    for record in conditions:
        grouped.setdefault(_condition_key(record), []).append(record)

    series = []
    for key, records in grouped.items():
        records = sorted(records, key=lambda r: r["dose_relative"])
        doses = [r["dose_relative"] for r in records]
        if len(doses) < 2:
            continue  # a single dose level has no gain per unit dose
        dprimes = [r["dprime_human"] for r in records]
        slopes = g_useful(dprimes, doses).tolist()
        series.append(
            {
                "diameter_mm": key[0],
                "contrast_hu": key[1],
                "slice_thickness_mm": key[2],
                "kernel": key[3],
                "zoom": key[4],
                "doses_relative": doses,
                "dprime_human": dprimes,
                "g_useful": slopes,
                "g_useful_monotone_decreasing": bool(
                    all(np.diff(slopes) < 0)
                ),
            }
        )
    return series


def _summary(conditions, series, nyquist):
    f_sat_95 = np.array([r["f_sat_95_lpmm"] for r in conditions])
    r_perceptual = np.array([r["r_perceptual"] for r in conditions])
    npwe = np.array([r["dprime_npwe"] for r in conditions])
    cho = np.array([r["dprime_cho"] for r in conditions])
    human = np.array([r["dprime_human"] for r in conditions])

    saturating = [s["g_useful_monotone_decreasing"] for s in series]
    saturating_fraction = float(np.mean(saturating)) if saturating else None

    return {
        "f_sat_95_lpmm": _spread(f_sat_95),
        "f_sat_95_over_nyquist": _spread(f_sat_95 / nyquist),
        "r_perceptual": _spread(r_perceptual),
        "dose_series_saturating_fraction": saturating_fraction,
        "n_dose_series": len(series),
        "neural_noise_share": _spread(
            np.array([r["neural_noise_share"] for r in conditions])
        ),
        "quantisation_noise_share": _spread(
            np.array([r["quantisation_noise_share"] for r in conditions])
        ),
        "kernel_sensitivity": _kernel_spread(conditions, "dprime_human"),
        "kernel_invariance_csf_weight_form": _kernel_spread(
            conditions, "dprime_human_csf_weight"
        ),
        "observer_agreement": {
            "spearman_npwe_cho": float(stats.spearmanr(npwe, cho).statistic),
            "spearman_human_npwe": float(
                stats.spearmanr(human, npwe).statistic
            ),
            "spearman_human_cho": float(stats.spearmanr(human, cho).statistic),
        },
    }


def _spread(values):
    return {
        "min": float(np.min(values)),
        "median": float(np.median(values)),
        "max": float(np.max(values)),
    }


def _kernel_spread(conditions, field):
    """Relative spread of ``field`` across kernels, other axes fixed.

    In a quantum-limited FBP chain the reconstruction kernel filters signal and
    noise identically, so an observer that applies one common weight to both
    cannot see it at all. Under the superseded numerator-weight form the
    spread is therefore a validation quantity — the numerical footprint of
    invertible-filter invariance — while under the primary form, where the
    neural noise bypasses the kernel, it is a genuine physical sensitivity.
    """
    grouped = {}
    for record in conditions:
        key = (
            record["diameter_mm"],
            record["contrast_hu"],
            record["dose_relative"],
            record["slice_thickness_mm"],
            record["zoom"],
        )
        grouped.setdefault(key, []).append(record[field])

    spreads = [
        _relative_spread(values)
        for values in grouped.values()
        if len(values) > 1
    ]
    return {
        "max_relative_dprime_spread": float(max(spreads)) if spreads else 0.0,
        "median_relative_dprime_spread": (
            float(np.median(spreads)) if spreads else 0.0
        ),
    }


def _rounded(obj, ndigits=10):
    """Round every float so the JSON is stable across platforms."""
    if isinstance(obj, dict):
        return {k: _rounded(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_rounded(v, ndigits) for v in obj]
    if isinstance(obj, float):
        return round(obj, ndigits)
    return obj


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/phase1.json"),
        help="output path for the results.json (default: results/phase1.json)",
    )
    args = parser.parse_args(argv)

    results = run_phase1()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(_rounded(results), handle, indent=2, sort_keys=True)
        handle.write("\n")

    summary = results["summary"]
    saturating = summary["dose_series_saturating_fraction"]
    print(f"wrote {args.out} ({results['metadata']['n_conditions']} conditions)")
    print(
        "f_sat(95%) [lp/mm]: "
        f"{summary['f_sat_95_lpmm']['min']:.3f} .. "
        f"{summary['f_sat_95_lpmm']['max']:.3f} "
        f"(median {summary['f_sat_95_lpmm']['median']:.3f}, "
        f"Nyquist {results['metadata']['nyquist_lpmm']:.3f})"
    )
    print(
        "R_perceptual median: "
        f"{summary['r_perceptual']['median']:.4f}; "
        "dose series with decreasing G_useful: "
        + ("n/a" if saturating is None else f"{saturating * 100:.0f}%")
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
