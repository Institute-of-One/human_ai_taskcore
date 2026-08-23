"""Figures and every number the manuscript quotes (design principle no. 2).

The manuscript is written as ``paper/manuscript_template.md`` with ``{{key}}``
placeholders and rendered to ``paper/manuscript.md`` by this script, so a
number can only reach the text by coming from a results file. Each key also
carries its provenance — which file and which path it was read from, or that
this script derived it — and both land in ``paper/numbers.json`` for review.

    python paper/make_figures.py

Figures are recomputed through ptx, which is deterministic, so re-running
reproduces them byte for byte.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from ptx.condition import (  # noqa: E402
    Acquisition,
    Reading,
    Task,
    evaluate,
    frequency_grid,
)

RESULTS = {
    "phase1": Path("results/phase1.json"),
    "uncertainty": Path("results/uncertainty.json"),
    "case_uhrct": Path("results/case_uhrct.json"),
}
PLACEHOLDER = re.compile(r"\{\{([a-z0-9_]+)\}\}")

STYLE = {
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "legend.frameon": False,
}


def _dig(payload, path):
    node = payload
    for part in path.split("."):
        node = node[int(part)] if part.isdigit() else node[part]
    return node


class Numbers:
    """Named, formatted quantities with the source they came from."""

    def __init__(self, sources):
        self.sources = sources
        self.values = {}
        self.provenance = {}

    def read(self, key, source, path, fmt="{:.3f}", scale=1.0):
        value = _dig(self.sources[source], path) * scale
        self.values[key] = fmt.format(value)
        self.provenance[key] = f"{RESULTS[source].as_posix()}:{path}"
        return value

    def derive(self, key, value, fmt="{:.3f}", note=""):
        self.values[key] = fmt.format(value) if not isinstance(value, str) else value
        self.provenance[key] = f"derived by paper/make_figures.py ({note})"
        return value

    def payload(self):
        return {"values": self.values, "provenance": self.provenance}


def collect_numbers(sources):
    numbers = Numbers(sources)
    phase1, uncertainty, case = (
        sources["phase1"],
        sources["uncertainty"],
        sources["case_uhrct"],
    )

    numbers.derive(
        "n_conditions",
        str(phase1["metadata"]["n_conditions"]),
        note="results/phase1.json:metadata.n_conditions",
    )
    nyquist = numbers.read(
        "nyquist_lpmm", "phase1", "metadata.nyquist_lpmm", "{:.2f}"
    )
    f_sat_median = numbers.read(
        "f_sat_median_lpmm", "phase1", "summary.f_sat_95_lpmm.median"
    )
    numbers.read("f_sat_min_lpmm", "phase1", "summary.f_sat_95_lpmm.min")
    numbers.read("f_sat_max_lpmm", "phase1", "summary.f_sat_95_lpmm.max")
    numbers.derive(
        "f_sat_median_percent_of_nyquist",
        100.0 * f_sat_median / nyquist,
        "{:.0f}",
        note="median f_sat over Nyquist",
    )
    numbers.read(
        "r_perceptual_median", "phase1", "summary.r_perceptual.median", "{:.3f}"
    )
    numbers.read(
        "neural_share_median",
        "phase1",
        "summary.neural_noise_share.median",
        "{:.0f}",
        scale=100.0,
    )
    numbers.read(
        "quantisation_share_max",
        "phase1",
        "summary.quantisation_noise_share.max",
        "{:.3f}",
        scale=100.0,
    )
    numbers.derive(
        "n_dose_series",
        str(phase1["summary"]["n_dose_series"]),
        note="results/phase1.json:summary.n_dose_series",
    )
    numbers.read(
        "saturating_fraction_phase1",
        "phase1",
        "summary.dose_series_saturating_fraction",
        "{:.0f}",
        scale=100.0,
    )
    numbers.read(
        "invariance_primary",
        "phase1",
        "summary.invertible_filter_invariance."
        "max_relative_dprime2_spread_primary_form",
        "{:.1e}",
    )
    numbers.read(
        "kernel_sensitivity_median",
        "phase1",
        "summary.kernel_sensitivity.median_relative_dprime_spread",
        "{:.1f}",
        scale=100.0,
    )
    numbers.read(
        "spearman_npwe_cho",
        "phase1",
        "summary.observer_agreement.spearman_npwe_cho",
        "{:.2f}",
    )

    numbers.derive(
        "n_propagation_samples",
        str(uncertainty["metadata"]["config"]["n_samples"]),
        note="results/uncertainty.json:metadata.config.n_samples",
    )
    numbers.derive(
        "n_propagation_evaluations",
        f"{uncertainty['metadata']['n_evaluations']:,}",
        note="results/uncertainty.json:metadata.n_evaluations",
    )
    numbers.read(
        "saturating_fraction_bands",
        "uncertainty",
        "summary.saturating_fraction",
        "{:.0f}",
        scale=100.0,
    )
    band_median = numbers.read(
        "f_sat_band_width_median",
        "uncertainty",
        "summary.f_sat_band_width_lpmm.median",
    )
    band_centre = numbers.read(
        "f_sat_band_centre_median",
        "uncertainty",
        "summary.f_sat_median_over_series.median",
    )
    numbers.derive(
        "f_sat_band_width_percent",
        100.0 * band_median / band_centre,
        "{:.0f}",
        note="median band width over median f_sat",
    )
    numbers.read(
        "r_perceptual_band_low",
        "uncertainty",
        "summary.r_perceptual_band.lowest_lower",
    )
    numbers.read(
        "r_perceptual_band_high",
        "uncertainty",
        "summary.r_perceptual_band.highest_upper",
    )

    numbers.read(
        "added_band_cutoff_lpmm",
        "case_uhrct",
        "metadata.added_band_cutoff_lpmm",
        "{:.2f}",
    )
    numbers.read(
        "added_band_median_percent",
        "case_uhrct",
        "summary.added_band_share_uhrct.median",
        "{:.2f}",
        scale=100.0,
    )
    numbers.read(
        "added_band_max_percent",
        "case_uhrct",
        "summary.added_band_share_uhrct.max",
        "{:.1f}",
        scale=100.0,
    )
    numbers.read(
        "m_star_conventional_median",
        "case_uhrct",
        "summary.m_star.conventional.median",
        "{:.2f}",
    )
    numbers.read(
        "m_star_uhrct_median", "case_uhrct", "summary.m_star.u-hrct.median", "{:.2f}"
    )
    rows = {
        row["diameter_mm"]: row
        for row in case["summary"]["by_diameter"]["rows"]
    }
    smallest, largest = min(rows), max(rows)
    numbers.derive("smallest_task_mm", f"{smallest:g}", note="case study task set")
    numbers.derive("largest_task_mm", f"{largest:g}", note="case study task set")
    for name, diameter in (("small", smallest), ("large", largest)):
        row = rows[diameter]
        numbers.derive(
            f"{name}_task_added_band_percent",
            100.0 * row["added_band_share_max"],
            "{:.1f}",
            note=f"case study, {diameter:g} mm task",
        )
        numbers.derive(
            f"{name}_task_dprime_uhrct",
            row["dprime_uhrct_at_reference"],
            "{:.2f}",
            note=f"case study, {diameter:g} mm task at the reference reading",
        )
        numbers.derive(
            f"{name}_task_dprime_gain_percent",
            100.0 * (row["dprime_ratio_at_reference"] - 1.0),
            "{:.1f}",
            note=f"case study, {diameter:g} mm task at the reference reading",
        )
    return numbers


def figure_contribution_density(path):
    """Where in frequency the detectable information sits, and f_sat."""
    acquisition = Acquisition(slice_thickness_mm=1.0)
    f = frequency_grid(acquisition, 2048)
    task = Task(6.0, 250.0)

    # the density is plotted normalised and on a linear axis: the task
    # spectrum's nulls dominate a log axis and hide the point, which is where
    # the mass of the integral lies
    fig, ax = plt.subplots(figsize=(4.6, 3.0), layout="constrained")
    cumulative_axis = ax.twinx()
    for dose, colour in zip((0.25, 1.0, 4.0), ("#9ecae1", "#3182bd", "#08306b")):
        result = evaluate(
            f,
            task,
            Acquisition(dose_relative=dose, slice_thickness_mm=1.0),
            Reading(),
            (0.95,),
        )
        density = result.density / result.density.max()
        cumulative = np.cumsum(result.density) / np.sum(result.density)
        ax.plot(f, density, color=colour, lw=1.2, label=f"{dose:g}x dose")
        cumulative_axis.plot(f, cumulative, color=colour, lw=1.0, ls="--")
        cumulative_axis.plot(
            result.f_sat[0.95], 0.95, color=colour, marker="v", ms=5
        )
    cumulative_axis.axhline(0.95, color="0.4", lw=0.8, ls=":")
    ax.axvline(
        acquisition.nyquist_lpmm, color="0.3", ls="--", lw=1.0, label="Nyquist"
    )
    ax.set_xlabel("spatial frequency [lp/mm]")
    ax.set_ylabel(r"contribution density to $d'^2$ (normalised)")
    ax.set_xlim(0, acquisition.nyquist_lpmm * 1.02)
    ax.set_ylim(0, 1.05)
    cumulative_axis.set_ylabel(
        r"cumulative share (dashed); $\blacktriangledown$ = $f_{\mathrm{sat}}$"
    )
    cumulative_axis.set_ylim(0, 1.05)
    cumulative_axis.grid(False)
    ax.legend(loc="center right")
    fig.savefig(path)
    plt.close(fig)


def figure_f_sat_distribution(path, phase1):
    """How far below Nyquist the delivered band sits, over the whole grid."""
    nyquist = phase1["metadata"]["nyquist_lpmm"]
    ratios = np.array(
        [c["f_sat_95_lpmm"] / nyquist for c in phase1["conditions"]]
    )

    fig, ax = plt.subplots(figsize=(4.2, 2.8), layout="constrained")
    ax.hist(ratios, bins=24, color="#3182bd", edgecolor="white")
    ax.axvline(
        float(np.median(ratios)), color="#08306b", lw=1.5,
        label=f"median {np.median(ratios):.2f}",
    )
    ax.set_xlabel(r"$f_{\mathrm{sat}}(95\%)$ / Nyquist")
    ax.set_ylabel(f"conditions (of {len(ratios)})")
    ax.set_xlim(0, 1)
    ax.legend(loc="upper right")
    fig.savefig(path)
    plt.close(fig)


def figure_g_useful_bands(path, uncertainty):
    """H1: the gain per unit dose decays, and the band says so."""
    series = [
        s
        for s in uncertainty["series"]
        if s["kernel"] == "standard" and s["contrast_hu"] == 250.0
    ]
    fig, axes = plt.subplots(
        1, len(series), figsize=(2.2 * len(series), 2.7), sharey=True,
        layout="constrained",
    )
    axes = np.atleast_1d(axes)
    for ax, record in zip(axes, series):
        doses = np.array(record["doses_relative"])
        midpoints = 0.5 * (doses[:-1] + doses[1:])
        lower = [b["lower"] for b in record["g_useful"]]
        median = [b["median"] for b in record["g_useful"]]
        upper = [b["upper"] for b in record["g_useful"]]
        ax.fill_between(midpoints, lower, upper, color="#9ecae1", alpha=0.6)
        ax.plot(midpoints, median, color="#08306b", marker="o", ms=3)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xticks(midpoints)
        ax.set_xticklabels([f"{m:g}" for m in midpoints])
        ax.minorticks_off()
        ax.set_title(f"{record['diameter_mm']:g} mm", fontsize=9)
        ax.set_xlabel("relative dose")
    axes[0].set_ylabel(r"$G_{\mathrm{useful}} = \Delta d' / \Delta D$")
    fig.savefig(path)
    plt.close(fig)


def figure_added_band_map(path, case):
    """H3: the extra band arrives only once the image is enlarged."""
    diameters = sorted({p["diameter_mm"] for p in case["points"]})[:2]
    cutoff = case["metadata"]["added_band_cutoff_lpmm"]
    # one colour scale per panel: the two tasks differ by an order of
    # magnitude, and a shared scale would flatten the smaller one into noise
    fig, axes = plt.subplots(
        1, len(diameters), figsize=(3.6 * len(diameters), 2.9),
        layout="constrained", sharey=True,
    )
    axes = np.atleast_1d(axes)
    for index, (ax, diameter) in enumerate(zip(axes, diameters)):
        points = [p for p in case["points"] if p["diameter_mm"] == diameter]
        mags = sorted({p["magnification"] for p in points})
        distances = sorted({p["distance_mm"] for p in points})
        grid = np.array(
            [
                [
                    100.0
                    * next(
                        p["u-hrct"]["added_band_share"]
                        for p in points
                        if p["magnification"] == m and p["distance_mm"] == d
                    )
                    for m in mags
                ]
                for d in distances
            ]
        )
        mesh = ax.pcolormesh(
            mags, distances, grid, shading="nearest", cmap="viridis"
        )
        m_star = [
            next(
                row["u-hrct"]["m_star"]
                for row in case["sufficiency"]
                if row["diameter_mm"] == diameter
                and row["distance_mm"] == distance
            )
            for distance in distances
        ]
        ax.step(
            m_star, distances, where="mid", color="white", lw=1.4,
            label=r"$M^{*}$ (U-HRCT)",
        )
        ax.set_xscale("log")
        ax.set_xticks([0.25, 1.0, 4.0])
        ax.set_xticklabels(["0.25", "1", "4"])
        ax.set_xlabel("anatomical magnification M")
        ax.set_title(f"{diameter:g} mm task", fontsize=9)
        ax.grid(False)
        colourbar = fig.colorbar(mesh, ax=ax)
        if index == len(diameters) - 1:
            colourbar.set_label(
                f"share of $d'^2$ above {cutoff:.2f} lp/mm [%]"
            )
    axes[0].set_ylabel("viewing distance [mm]")
    axes[0].legend(loc="lower right", labelcolor="white")
    fig.savefig(path)
    plt.close(fig)


def figure_added_band_vs_task(path, case):
    """The finding that decides how H3 may be phrased."""
    rows = case["summary"]["by_diameter"]["rows"]
    diameters = [row["diameter_mm"] for row in rows]
    shares = [100.0 * row["added_band_share_max"] for row in rows]
    dprimes = [row["dprime_uhrct_at_reference"] for row in rows]

    fig, ax = plt.subplots(figsize=(4.2, 2.9), layout="constrained")
    positions = np.arange(len(diameters))
    ax.bar(positions, shares, color="#3182bd", width=0.6)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{d:g}" for d in diameters])
    ax.set_xlabel("task diameter [mm]")
    ax.set_ylabel("added band share of $d'^2$ [%]", color="#08306b")

    twin = ax.twinx()
    twin.plot(positions, dprimes, color="#c1121f", marker="o", ms=4)
    twin.axhline(1.0, color="#c1121f", lw=0.8, ls=":")
    twin.annotate(
        r"$d'=1$", (positions[-1], 1.0), color="#c1121f", fontsize=8,
        xytext=(-4, 3), textcoords="offset points", ha="right",
    )
    twin.set_yscale("log")
    twin.set_ylabel(r"$d'$ (U-HRCT, reference reading)", color="#c1121f")
    twin.grid(False)
    fig.savefig(path)
    plt.close(fig)


def render_manuscript(template_path, numbers, out_path):
    """Substitute every placeholder, refusing to leave one unresolved."""
    template = template_path.read_text(encoding="utf-8")
    missing = sorted(
        {
            key
            for key in PLACEHOLDER.findall(template)
            if key not in numbers.values
        }
    )
    if missing:
        raise KeyError(f"template asks for numbers that do not exist: {missing}")
    unused = sorted(set(numbers.values) - set(PLACEHOLDER.findall(template)))
    rendered = PLACEHOLDER.sub(lambda m: numbers.values[m.group(1)], template)
    out_path.write_text(rendered, encoding="utf-8", newline="\n")
    return unused


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--paper-dir", type=Path, default=Path("paper"))
    args = parser.parse_args(argv)

    sources = {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name, path in RESULTS.items()
    }
    numbers = collect_numbers(sources)

    figures = args.paper_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(STYLE):
        figure_contribution_density(figures / "fig1_contribution_density.png")
        figure_f_sat_distribution(
            figures / "fig2_f_sat_distribution.png", sources["phase1"]
        )
        figure_g_useful_bands(
            figures / "fig3_g_useful_bands.png", sources["uncertainty"]
        )
        figure_added_band_map(
            figures / "fig4_added_band_map.png", sources["case_uhrct"]
        )
        figure_added_band_vs_task(
            figures / "fig5_added_band_vs_task.png", sources["case_uhrct"]
        )

    (args.paper_dir / "numbers.json").write_text(
        json.dumps(numbers.payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    unused = render_manuscript(
        args.paper_dir / "manuscript_template.md",
        numbers,
        args.paper_dir / "manuscript.md",
    )

    print(f"wrote 5 figures to {figures}")
    print(
        f"wrote {args.paper_dir / 'numbers.json'} "
        f"({len(numbers.values)} quantities)"
    )
    print(f"rendered {args.paper_dir / 'manuscript.md'}")
    if unused:
        print(f"not yet cited in the manuscript: {', '.join(unused)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
