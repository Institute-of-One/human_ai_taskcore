"""H3 case study: does U-HRCT resolution reach the reader? (section 4, H3)

Two chains differing only in what the scanner delivers — a conventional
reconstruction and a U-HRCT-class one with finer pixels and a sharper TTF —
are read under the same conditions, and the question is how much of the extra
band above the conventional Nyquist contributes to d'^2_human.

Two choices decide whether the comparison is fair:

- The map axis is the *anatomical* magnification M (display mm per object mm),
  not the pixel zoom. At equal zoom the finer image appears twice as large, so
  a zoom-matched comparison would be comparing different apparent sizes. The
  per-chain zoom is reported alongside.
- Both chains share one projection-noise scale, fixed from the conventional
  reference condition. Equal dose fixes the projection noise; the finer chain
  then pays for its resolution in pixel variance, which is the real trade-off.

    python -m ptx.case_uhrct --out results/case_uhrct.json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import platform
from pathlib import Path

import numpy as np

from . import __version__
from .chain import CT_KERNEL_F50_LPMM, ct_nps_scale_for_variance
from .condition import Acquisition, Reading, Task, evaluate, frequency_grid
from .phase1 import _rounded

__all__ = [
    "ChainSpec",
    "CaseConfig",
    "run_case_uhrct",
    "sufficient_magnification",
    "main",
]


@dataclasses.dataclass(frozen=True)
class ChainSpec:
    """One scanner generation.

    ``f50_lpmm`` and ``pixel_mm_object`` stand in for published TTF and
    reconstruction values; they are configuration, not results, and the
    citations behind the numbers are pinned in the manuscript's Methods
    (see paper/NOTES.md).
    """

    name: str
    f50_lpmm: float
    pixel_mm_object: float

    @property
    def nyquist_lpmm(self):
        return 0.5 / self.pixel_mm_object


@dataclasses.dataclass(frozen=True)
class CaseConfig:
    conventional: ChainSpec = ChainSpec("conventional", 0.50, 200.0 / 512.0)
    uhrct: ChainSpec = ChainSpec("u-hrct", 1.20, 200.0 / 1024.0)

    # sub-millimetre tasks are the ones whose spectra reach above the
    # conventional Nyquist at all; without them the added band cannot be
    # tested, only the task function's own roll-off
    diameters_mm: tuple = (0.5, 1.0, 2.0, 4.0, 8.0)
    contrast_hu: float = 250.0
    slice_thickness_mm: float = 0.5
    dose_relative: float = 1.0

    magnifications: tuple = (
        0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0,
    )
    distances_mm: tuple = (300.0, 400.0, 500.0, 700.0, 1000.0)

    display_pitch_mm: float = 0.2
    luminance_cdm2: float = 100.0
    window_width_hu: float = 1500.0
    n_grey_levels: int = 256
    kappa: float = 1.0
    eta_cog: float = 0.5

    kernel_sharpness: float = 2.0
    ramp_exponent: float = 1.0
    reference_sd_hu: float = 50.0
    reference_slice_mm: float = 1.0
    n_freq: int = 2048
    sufficiency_fraction: float = 0.95

    def __post_init__(self):
        if self.uhrct.nyquist_lpmm <= self.conventional.nyquist_lpmm:
            raise ValueError("the U-HRCT chain must sample more finely")
        if len(self.magnifications) < 2 or len(self.distances_mm) < 1:
            raise ValueError("need a magnification axis to scan")


def _acquisition(cfg, spec, noise_scale):
    return Acquisition(
        kernel="standard",
        dose_relative=cfg.dose_relative,
        slice_thickness_mm=cfg.slice_thickness_mm,
        pixel_mm_object=spec.pixel_mm_object,
        kernel_sharpness=cfg.kernel_sharpness,
        ramp_exponent=cfg.ramp_exponent,
        reference_sd_hu=cfg.reference_sd_hu,
        reference_slice_mm=cfg.reference_slice_mm,
        f50_lpmm=spec.f50_lpmm,
        noise_scale_at_reference=noise_scale,
    )


def _reading(cfg, spec, magnification, distance_mm):
    # zoom is display pixels per image pixel; M = zoom * pitch / pixel
    zoom = magnification * spec.pixel_mm_object / cfg.display_pitch_mm
    return Reading(
        zoom=zoom,
        distance_mm=distance_mm,
        luminance_cdm2=cfg.luminance_cdm2,
        display_pitch_mm=cfg.display_pitch_mm,
        window_width_hu=cfg.window_width_hu,
        n_grey_levels=cfg.n_grey_levels,
        kappa=cfg.kappa,
        eta_cog=cfg.eta_cog,
    )


def _tail_fraction(f, density, f_cut):
    """Share of the d'^2 integral coming from f > f_cut."""
    total = float(np.trapezoid(density, f))
    if total <= 0:
        return 0.0
    above = f > f_cut
    if not np.any(above):
        return 0.0
    # include the crossing point so the tail is not truncated at a grid edge
    idx = max(int(np.argmax(above)) - 1, 0)
    tail = float(np.trapezoid(density[idx:], f[idx:]))
    return max(tail / total, 0.0)


def sufficient_magnification(magnifications, dprimes, fraction=0.95):
    """Smallest magnification reaching ``fraction`` of the asymptotic d'.

    H3's design quantity: d' rises towards an asymptote rather than peaking,
    so what a reading protocol needs is the magnification beyond which nothing
    further arrives, not an optimum.
    """
    magnifications = np.asarray(magnifications, dtype=float)
    dprimes = np.asarray(dprimes, dtype=float)
    if magnifications.shape != dprimes.shape:
        raise ValueError("magnification and d' arrays must match")
    order = np.argsort(magnifications)
    magnifications, dprimes = magnifications[order], dprimes[order]
    target = fraction * float(dprimes[-1])
    reached = np.nonzero(dprimes >= target)[0]
    return float(magnifications[reached[0]])


def run_case_uhrct(config=None):
    """Evaluate the (M, D) map for both chains."""
    cfg = config or CaseConfig()

    # one projection-noise level for both chains, from the conventional
    # reference condition at its own Nyquist
    noise_scale = ct_nps_scale_for_variance(
        cfg.reference_sd_hu**2,
        cfg.conventional.nyquist_lpmm,
        CT_KERNEL_F50_LPMM["standard"],
        cfg.kernel_sharpness,
        cfg.ramp_exponent,
    )
    f_cut = cfg.conventional.nyquist_lpmm

    chains = {}
    for spec in (cfg.conventional, cfg.uhrct):
        acquisition = _acquisition(cfg, spec, noise_scale)
        f = frequency_grid(acquisition, cfg.n_freq)
        chains[spec.name] = (spec, acquisition, f)

    points = []
    for diameter in cfg.diameters_mm:
        task = Task(diameter_mm=diameter, contrast_hu=cfg.contrast_hu)
        for distance in cfg.distances_mm:
            for magnification in cfg.magnifications:
                record = {
                    "diameter_mm": diameter,
                    "distance_mm": distance,
                    "magnification": magnification,
                }
                for name, (spec, acquisition, f) in chains.items():
                    reading = _reading(cfg, spec, magnification, distance)
                    result = evaluate(
                        f, task, acquisition, reading, (0.95,)
                    )
                    record[name] = {
                        "zoom": reading.zoom,
                        "dprime_human": result.dprime_human,
                        "f_sat_95_lpmm": result.f_sat[0.95],
                        "r_perceptual": result.r_perceptual,
                        "neural_noise_share": result.neural_noise_share,
                        "added_band_share": _tail_fraction(
                            f, result.density, f_cut
                        ),
                    }
                record["dprime_ratio_uhrct_over_conventional"] = (
                    record["u-hrct"]["dprime_human"]
                    / record["conventional"]["dprime_human"]
                )
                points.append(record)

    sufficiency = _sufficiency(cfg, points)
    return {
        "metadata": {
            "protocol": "IORN-009A v0.4, section 4 (H3) and section 7",
            "map_axis": (
                "anatomical magnification M = display mm per object mm; the "
                "per-chain pixel zoom is reported with each point"
            ),
            "noise_convention": (
                "one projection-noise scale for both chains (equal dose), "
                "fixed from the conventional reference condition"
            ),
            "ptx_version": __version__,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "config": dataclasses.asdict(cfg),
            "added_band_cutoff_lpmm": f_cut,
            "n_points": len(points),
        },
        "points": points,
        "sufficiency": sufficiency,
        "summary": _summary(cfg, points, sufficiency),
    }


def _sufficiency(cfg, points):
    """M* per (chain, task, distance), plus a monotonicity check."""
    grouped = {}
    for record in points:
        key = (record["diameter_mm"], record["distance_mm"])
        grouped.setdefault(key, []).append(record)

    pixel_by_chain = {
        "conventional": cfg.conventional.pixel_mm_object,
        "u-hrct": cfg.uhrct.pixel_mm_object,
    }
    rows = []
    for (diameter, distance), records in grouped.items():
        records = sorted(records, key=lambda r: r["magnification"])
        mags = [r["magnification"] for r in records]
        row = {"diameter_mm": diameter, "distance_mm": distance}
        for name, pixel_mm in pixel_by_chain.items():
            dprimes = [r[name]["dprime_human"] for r in records]
            m_star = sufficient_magnification(
                mags, dprimes, cfg.sufficiency_fraction
            )
            row[name] = {
                "m_star": m_star,
                "zoom_star": m_star * pixel_mm / cfg.display_pitch_mm,
                "dprime_monotone_in_magnification": bool(
                    all(np.diff(dprimes) > 0)
                ),
                "dprime_asymptotic_gain": float(dprimes[-1] / dprimes[0]),
            }
        rows.append(row)
    return rows


def _by_diameter(cfg, points, unit_magnification):
    """Added band next to the absolute d' it would be added to.

    Reported together on purpose: the extra band is worth the most, in
    relative terms, exactly where the task is least detectable, and a summary
    that showed only the relative gain would invite over-claiming.
    """
    reference_distance = min(
        cfg.distances_mm, key=lambda d: abs(d - 500.0)
    )
    rows = []
    for diameter in cfg.diameters_mm:
        matching = [r for r in points if r["diameter_mm"] == diameter]
        reference = [
            r
            for r in matching
            if r["magnification"] == unit_magnification
            and r["distance_mm"] == reference_distance
        ][0]
        rows.append(
            {
                "diameter_mm": diameter,
                "added_band_share_max": float(
                    max(r["u-hrct"]["added_band_share"] for r in matching)
                ),
                "dprime_uhrct_at_reference": reference["u-hrct"][
                    "dprime_human"
                ],
                "dprime_conventional_at_reference": reference["conventional"][
                    "dprime_human"
                ],
                "dprime_ratio_at_reference": reference[
                    "dprime_ratio_uhrct_over_conventional"
                ],
                "f_sat_95_lpmm_at_reference": {
                    "conventional": reference["conventional"][
                        "f_sat_95_lpmm"
                    ],
                    "u-hrct": reference["u-hrct"]["f_sat_95_lpmm"],
                },
            }
        )
    return {
        "reference_reading": {
            "magnification": unit_magnification,
            "distance_mm": reference_distance,
        },
        "rows": rows,
    }


def _summary(cfg, points, sufficiency):
    added = np.array([r["u-hrct"]["added_band_share"] for r in points])
    ratio = np.array(
        [r["dprime_ratio_uhrct_over_conventional"] for r in points]
    )
    nearest_unity = min(cfg.magnifications, key=lambda m: abs(m - 1.0))
    unity = [r for r in points if r["magnification"] == nearest_unity]
    return {
        "unit_magnification_evaluated_at": nearest_unity,
        "by_diameter": _by_diameter(cfg, points, nearest_unity),
        "added_band_share_uhrct": {
            "min": float(added.min()),
            "median": float(np.median(added)),
            "max": float(added.max()),
        },
        "added_band_share_at_unit_magnification": {
            "median": float(
                np.median([r["u-hrct"]["added_band_share"] for r in unity])
            ),
            "max": float(
                np.max([r["u-hrct"]["added_band_share"] for r in unity])
            ),
        },
        "dprime_ratio_uhrct_over_conventional": {
            "min": float(ratio.min()),
            "median": float(np.median(ratio)),
            "max": float(ratio.max()),
        },
        "m_star": {
            name: {
                "min": float(min(values)),
                "median": float(np.median(values)),
                "max": float(max(values)),
            }
            for name, values in (
                (
                    name,
                    [row[name]["m_star"] for row in sufficiency],
                )
                for name in ("conventional", "u-hrct")
            )
        },
        "dprime_monotone_in_magnification": bool(
            all(
                row[name]["dprime_monotone_in_magnification"]
                for row in sufficiency
                for name in ("conventional", "u-hrct")
            )
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results/case_uhrct.json"),
        help="output path (default: results/case_uhrct.json)",
    )
    args = parser.parse_args(argv)

    results = run_case_uhrct()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(_rounded(results), handle, indent=2, sort_keys=True)
        handle.write("\n")

    meta, summary = results["metadata"], results["summary"]
    print(f"wrote {args.out} ({meta['n_points']} map points)")
    print(
        "added band (> "
        f"{meta['added_band_cutoff_lpmm']:.2f} lp/mm) share of d'^2, U-HRCT: "
        f"median {summary['added_band_share_uhrct']['median'] * 100:.2f}%, "
        f"max {summary['added_band_share_uhrct']['max'] * 100:.2f}%"
    )
    print(
        "M* (95% of asymptotic d'): conventional median "
        f"{summary['m_star']['conventional']['median']:.2f}, U-HRCT median "
        f"{summary['m_star']['u-hrct']['median']:.2f}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
