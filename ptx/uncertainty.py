"""Interval propagation over the range parameters (protocol section 5.4).

The framework deliberately refuses to point-estimate the observer: eta_cog and
the neural-noise scale kappa are literature ranges, and the reading geometry
(viewing distance, luminance, magnification) varies between readers. This
module propagates all of them together and reports 95% bands, which are the
unit the manuscript states results in.

It also implements H1's operational rejection rule (protocol section 4). Note
what is and is not falsifiable here: G_useful cannot change sign, because more
dose always means less image noise, so testing "is G_useful positive" would be
vacuous. The saturation signature is that G_useful *declines*, so the rule is
applied to the decline

    dG = G_useful(lowest dose step) - G_useful(highest dose step)

and a condition counts as saturating when the lower bound of dG's 95% band is
positive. H1 is rejected if that fails to hold, i.e. if the band straddles
zero for the bulk of the conditions.

    python -m ptx.uncertainty --out results/uncertainty.json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import platform
from itertools import product
from pathlib import Path

import numpy as np

from . import __version__
from .condition import Acquisition, Reading, Task, evaluate, frequency_grid
from .detectability import g_useful
from .phase1 import _rounded

__all__ = [
    "Intervals",
    "UncertaintyConfig",
    "latin_hypercube",
    "sample_readings",
    "band",
    "propagate_condition",
    "propagate_dose_series",
    "run_uncertainty",
    "main",
]


@dataclasses.dataclass(frozen=True)
class Intervals:
    """Ranges propagated as (low, high). Never point estimates.

    ``eta_cog``: human detection efficiency for a known signal in noise.
    ``kappa``: dimensionless scale on Barten's published internal noise, so
    kappa = 1 is the standard observer and the interval expresses how much
    trust the absolute noise level carries.
    ``zoom`` is under the reader's control rather than uncertain, but it is
    propagated the same way so that the bands describe a population of
    readings rather than one idealised setup; H3 instead scans it explicitly.

    The numeric defaults are representative; the citations backing each one
    are pinned in the manuscript's Methods (see paper/NOTES.md).
    """

    eta_cog: tuple = (0.3, 0.7)
    kappa: tuple = (0.5, 2.0)
    distance_mm: tuple = (400.0, 700.0)
    luminance_cdm2: tuple = (50.0, 200.0)
    zoom: tuple = (1.0, 2.0)

    def __post_init__(self):
        for name in ("eta_cog", "kappa", "distance_mm", "luminance_cdm2", "zoom"):
            low, high = getattr(self, name)
            if not (0 < low <= high):
                raise ValueError(f"{name} must be a positive (low, high)")

    @property
    def names(self):
        return ("eta_cog", "kappa", "distance_mm", "luminance_cdm2", "zoom")


def latin_hypercube(n_samples, n_dim, seed):
    """Latin hypercube on the unit cube, stratified and seed-determined.

    One sample per stratum per dimension, so a modest number of samples still
    covers each interval evenly — the point is coverage of the parameter box,
    not a probability model we do not have.
    """
    if n_samples < 2 or n_dim < 1:
        raise ValueError("need at least 2 samples and 1 dimension")
    rng = np.random.default_rng(seed)
    strata = (np.arange(n_samples) + rng.random((n_dim, n_samples))) / n_samples
    for row in strata:
        rng.shuffle(row)
    return strata.T


def sample_readings(intervals, n_samples, seed, base=None):
    """Map a Latin hypercube onto :class:`~ptx.condition.Reading` objects."""
    base = base or Reading()
    cube = latin_hypercube(n_samples, len(intervals.names), seed)
    readings = []
    for row in cube:
        values = {}
        for name, u in zip(intervals.names, row):
            low, high = getattr(intervals, name)
            values[name] = float(low + u * (high - low))
        readings.append(dataclasses.replace(base, **values))
    return readings


def band(values, coverage=0.95):
    """Central ``coverage`` interval plus the median."""
    values = np.asarray(values, dtype=float)
    tail = 100.0 * (1.0 - coverage) / 2.0
    return {
        "lower": float(np.percentile(values, tail)),
        "median": float(np.median(values)),
        "upper": float(np.percentile(values, 100.0 - tail)),
        "coverage": coverage,
    }


def propagate_condition(f, task, acquisition, readings, fraction=0.95):
    """Evaluate one physical condition over a sample of reading conditions."""
    dprime, f_sat_values, r_perceptual, neural_share = [], [], [], []
    for reading in readings:
        result = evaluate(f, task, acquisition, reading, (fraction,))
        dprime.append(result.dprime_human)
        f_sat_values.append(result.f_sat[fraction])
        r_perceptual.append(result.r_perceptual)
        neural_share.append(result.neural_noise_share)
    return {
        "dprime_human": np.array(dprime),
        "f_sat_lpmm": np.array(f_sat_values),
        "r_perceptual": np.array(r_perceptual),
        "neural_noise_share": np.array(neural_share),
    }


def propagate_dose_series(f, task, acquisitions, readings, fraction=0.95):
    """Bands for one dose series, sample-paired across the dose axis.

    Each reading condition is carried through every dose level, so a sample's
    G_useful curve is one coherent draw rather than a mix of observers. That
    pairing is what makes the band on the decline meaningful.
    """
    acquisitions = sorted(acquisitions, key=lambda a: a.dose_relative)
    doses = np.array([a.dose_relative for a in acquisitions], dtype=float)
    if doses.size < 2:
        raise ValueError("a dose series needs at least two dose levels")

    per_dose = [
        propagate_condition(f, task, acquisition, readings, fraction)
        for acquisition in acquisitions
    ]
    dprime = np.stack([p["dprime_human"] for p in per_dose], axis=1)
    gains = np.stack([g_useful(row, doses) for row in dprime], axis=0)
    decline = gains[:, 0] - gains[:, -1]

    return {
        "doses_relative": doses.tolist(),
        "dprime_human": [band(dprime[:, i]) for i in range(doses.size)],
        "g_useful": [band(gains[:, i]) for i in range(gains.shape[1])],
        "g_useful_decline": band(decline),
        "saturating": bool(band(decline)["lower"] > 0.0),
        "f_sat_lpmm": band(per_dose[-1]["f_sat_lpmm"]),
        "r_perceptual": band(per_dose[-1]["r_perceptual"]),
        "neural_noise_share": band(per_dose[-1]["neural_noise_share"]),
    }


@dataclasses.dataclass(frozen=True)
class UncertaintyConfig:
    """Which conditions to propagate, and how densely."""

    diameters_mm: tuple = (4.0, 6.0, 8.0)
    contrasts_hu: tuple = (250.0, 880.0)
    kernels: tuple = ("smooth", "standard", "sharp")
    doses_relative: tuple = (0.25, 0.5, 1.0, 2.0, 4.0)
    slice_thickness_mm: float = 1.0
    pixel_mm_object: float = 200.0 / 512.0
    intervals: Intervals = dataclasses.field(default_factory=Intervals)
    n_samples: int = 256
    seed: int = 20260823
    n_freq: int = 1024
    fraction: float = 0.95

    def __post_init__(self):
        if self.n_samples < 2:
            raise ValueError("need at least 2 samples")
        if len(self.doses_relative) < 2:
            raise ValueError("H1 needs at least two dose levels")


def run_uncertainty(config=None):
    """Propagate the section 5.4 intervals over the section 7 conditions."""
    cfg = config or UncertaintyConfig()
    readings = sample_readings(cfg.intervals, cfg.n_samples, cfg.seed)
    reference = Acquisition(
        kernel="standard",
        slice_thickness_mm=cfg.slice_thickness_mm,
        pixel_mm_object=cfg.pixel_mm_object,
    )
    f = frequency_grid(reference, cfg.n_freq)

    series = []
    for diameter, contrast, kernel in product(
        cfg.diameters_mm, cfg.contrasts_hu, cfg.kernels
    ):
        acquisitions = [
            Acquisition(
                kernel=kernel,
                dose_relative=dose,
                slice_thickness_mm=cfg.slice_thickness_mm,
                pixel_mm_object=cfg.pixel_mm_object,
            )
            for dose in cfg.doses_relative
        ]
        record = {
            "diameter_mm": diameter,
            "contrast_hu": contrast,
            "kernel": kernel,
        }
        record.update(
            propagate_dose_series(
                f,
                Task(diameter_mm=diameter, contrast_hu=contrast),
                acquisitions,
                readings,
                cfg.fraction,
            )
        )
        series.append(record)

    return {
        "metadata": {
            "protocol": "IORN-009A v0.4, section 5.4 (interval propagation)",
            "h1_rule": (
                "a condition saturates when the lower bound of the 95% band "
                "on G_useful's decline is positive; G_useful itself cannot "
                "change sign, so its sign carries no information"
            ),
            "ptx_version": __version__,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "config": dataclasses.asdict(cfg),
            "nyquist_lpmm": reference.nyquist_lpmm,
            "n_series": len(series),
            "n_evaluations": len(series)
            * len(cfg.doses_relative)
            * cfg.n_samples,
        },
        "series": series,
        "summary": _summary(series),
    }


def _summary(series):
    saturating = [s["saturating"] for s in series]
    f_sat_medians = np.array([s["f_sat_lpmm"]["median"] for s in series])
    widths = np.array(
        [
            s["f_sat_lpmm"]["upper"] - s["f_sat_lpmm"]["lower"]
            for s in series
        ]
    )
    return {
        "n_series": len(series),
        "saturating_fraction": float(np.mean(saturating)),
        "f_sat_median_over_series": {
            "min": float(f_sat_medians.min()),
            "median": float(np.median(f_sat_medians)),
            "max": float(f_sat_medians.max()),
        },
        "f_sat_band_width_lpmm": {
            "min": float(widths.min()),
            "median": float(np.median(widths)),
            "max": float(widths.max()),
        },
        "r_perceptual_band": {
            "lowest_lower": float(
                min(s["r_perceptual"]["lower"] for s in series)
            ),
            "highest_upper": float(
                max(s["r_perceptual"]["upper"] for s in series)
            ),
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/uncertainty.json"),
        help="output path (default: results/uncertainty.json)",
    )
    args = parser.parse_args(argv)

    results = run_uncertainty()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(_rounded(results), handle, indent=2, sort_keys=True)
        handle.write("\n")

    meta, summary = results["metadata"], results["summary"]
    print(
        f"wrote {args.out} ({meta['n_series']} series, "
        f"{meta['n_evaluations']} evaluations)"
    )
    print(
        "saturating series (95% band lower bound on the G_useful decline > 0): "
        f"{summary['saturating_fraction'] * 100:.0f}%"
    )
    print(
        "f_sat(95%) median over series: "
        f"{summary['f_sat_median_over_series']['median']:.3f} lp/mm; "
        "band width "
        f"{summary['f_sat_band_width_lpmm']['median']:.3f} lp/mm (median)"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
