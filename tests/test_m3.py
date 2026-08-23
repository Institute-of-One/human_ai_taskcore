"""M3: interval propagation (section 5.4) and the U-HRCT case study (H3)."""

import dataclasses

import numpy as np
import pytest

from ptx.case_uhrct import (
    CaseConfig,
    ChainSpec,
    run_case_uhrct,
    sufficient_magnification,
)
from ptx.condition import (
    Acquisition,
    Reading,
    Task,
    build_chain,
    evaluate,
    frequency_grid,
)
from ptx.uncertainty import (
    Intervals,
    UncertaintyConfig,
    band,
    latin_hypercube,
    propagate_dose_series,
    run_uncertainty,
    sample_readings,
)


@pytest.fixture(scope="module")
def small_uncertainty():
    cfg = UncertaintyConfig(
        diameters_mm=(4.0,),
        contrasts_hu=(250.0, 880.0),
        kernels=("standard",),
        doses_relative=(0.25, 1.0, 4.0),
        n_samples=32,
        n_freq=512,
    )
    return cfg, run_uncertainty(cfg)


@pytest.fixture(scope="module")
def small_case():
    cfg = CaseConfig(
        diameters_mm=(0.5, 4.0),
        magnifications=(0.25, 0.5, 1.0, 2.0, 4.0),
        distances_mm=(500.0,),
        n_freq=512,
    )
    return cfg, run_case_uhrct(cfg)


class TestSampling:
    def test_latin_hypercube_is_stratified(self):
        cube = latin_hypercube(50, 4, seed=1)
        assert cube.shape == (50, 4)
        assert np.all((cube > 0.0) & (cube < 1.0))
        for column in cube.T:
            # exactly one sample per stratum in every dimension
            strata = np.floor(column * 50).astype(int)
            assert sorted(strata) == list(range(50))

    def test_same_seed_same_cube(self):
        assert np.array_equal(
            latin_hypercube(20, 3, seed=7), latin_hypercube(20, 3, seed=7)
        )
        assert not np.array_equal(
            latin_hypercube(20, 3, seed=7), latin_hypercube(20, 3, seed=8)
        )

    def test_samples_stay_inside_the_declared_intervals(self):
        intervals = Intervals()
        readings = sample_readings(intervals, 64, seed=3)
        assert len(readings) == 64
        for name in intervals.names:
            low, high = getattr(intervals, name)
            values = np.array([getattr(r, name) for r in readings])
            assert np.all((values >= low) & (values <= high))
            # and cover the interval rather than clustering
            assert values.min() < low + 0.1 * (high - low)
            assert values.max() > high - 0.1 * (high - low)

    def test_intervals_reject_reversed_bounds(self):
        with pytest.raises(ValueError):
            Intervals(kappa=(2.0, 0.5))

    def test_band_orders_its_bounds(self):
        values = np.linspace(0.0, 1.0, 1001)
        b = band(values, coverage=0.95)
        assert b["lower"] < b["median"] < b["upper"]
        assert b["lower"] == pytest.approx(0.025, abs=1e-3)
        assert b["upper"] == pytest.approx(0.975, abs=1e-3)


class TestPropagation:
    def test_f_sat_does_not_depend_on_cognitive_efficiency(self):
        # eta_cog scales the whole density, so it cannot move the frequency at
        # which a fixed fraction of it has accumulated. This is what lets the
        # f_sat band be read as a purely perceptual quantity
        acquisition = Acquisition()
        f = frequency_grid(acquisition, 512)
        task = Task(6.0, 250.0)
        values = [
            evaluate(f, task, acquisition, Reading(eta_cog=eta)).f_sat[0.95]
            for eta in (0.2, 0.5, 0.9)
        ]
        assert values[0] == pytest.approx(values[1], rel=1e-12)
        assert values[1] == pytest.approx(values[2], rel=1e-12)

    def test_dose_raises_dprime_for_every_sample(self, small_uncertainty):
        # sample pairing: each reading condition is carried across the whole
        # dose axis, so the per-sample curve must be monotone even though the
        # bands overlap
        _, results = small_uncertainty
        for series in results["series"]:
            medians = [b["median"] for b in series["dprime_human"]]
            assert all(np.diff(medians) > 0)

    def test_g_useful_declines_and_the_band_says_so(self, small_uncertainty):
        _, results = small_uncertainty
        for series in results["series"]:
            gains = [b["median"] for b in series["g_useful"]]
            assert all(np.diff(gains) < 0)
            assert all(g > 0 for g in gains)  # sign carries no information
            assert series["g_useful_decline"]["lower"] > 0.0
            assert series["saturating"]

    def test_r_perceptual_band_respects_the_efficiency_ceiling(
        self, small_uncertainty
    ):
        cfg, results = small_uncertainty
        ceiling = np.sqrt(cfg.intervals.eta_cog[1])
        for series in results["series"]:
            assert series["r_perceptual"]["upper"] <= ceiling + 1e-12

    def test_wider_intervals_widen_the_band(self):
        acquisitions = [
            Acquisition(dose_relative=dose) for dose in (0.5, 1.0, 2.0)
        ]
        f = frequency_grid(acquisitions[0], 512)
        task = Task(4.0, 250.0)
        narrow = propagate_dose_series(
            f, task, acquisitions,
            sample_readings(Intervals(kappa=(0.9, 1.1)), 24, seed=5),
        )
        wide = propagate_dose_series(
            f, task, acquisitions,
            sample_readings(Intervals(kappa=(0.25, 4.0)), 24, seed=5),
        )
        narrow_width = (
            narrow["f_sat_lpmm"]["upper"] - narrow["f_sat_lpmm"]["lower"]
        )
        wide_width = wide["f_sat_lpmm"]["upper"] - wide["f_sat_lpmm"]["lower"]
        assert wide_width > narrow_width

    def test_louder_internal_noise_costs_dprime_but_raises_f_sat(self):
        # Barten's neural noise is low-frequency dominated (lateral inhibition
        # makes Phi ~ 1/u^2 below u0), so raising kappa suppresses the low
        # frequencies hardest. Detectability falls, yet the band carrying the
        # surviving 95% moves *up*: f_sat measures where the delivered
        # information sits, not how much of it there is
        acquisition = Acquisition()
        f = frequency_grid(acquisition, 512)
        task = Task(4.0, 250.0)
        quiet = evaluate(f, task, acquisition, Reading(kappa=0.5))
        loud = evaluate(f, task, acquisition, Reading(kappa=2.0))
        assert loud.dprime_human < quiet.dprime_human
        assert loud.f_sat[0.95] > quiet.f_sat[0.95]

    def test_the_neural_floor_is_low_frequency_dominated(self):
        acquisition = Acquisition()
        f = frequency_grid(acquisition, 512)
        chain = build_chain(f, acquisition, Reading())
        # strictly decreasing over the lower decade, flattening at the top
        low = chain.n_neural[: f.size // 8]
        assert np.all(np.diff(low) < 0)
        assert chain.n_neural[0] > 100.0 * chain.n_neural[-1]

    def test_determinism(self, small_uncertainty):
        cfg, results = small_uncertainty
        again = run_uncertainty(cfg)
        assert again["series"] == results["series"]
        assert again["summary"] == results["summary"]

    def test_config_guards(self):
        with pytest.raises(ValueError):
            UncertaintyConfig(n_samples=1)
        with pytest.raises(ValueError):
            UncertaintyConfig(doses_relative=(1.0,))
        with pytest.raises(ValueError):
            latin_hypercube(1, 2, seed=0)


class TestEqualDoseConvention:
    def test_shared_noise_scale_makes_finer_pixels_noisier(self):
        # equal dose fixes the projection noise, so the same scale over a wider
        # band means more pixel variance; deriving the scale per chain from a
        # pixel-variance target would hide exactly the cost being weighed
        coarse = Acquisition(pixel_mm_object=200.0 / 512.0)
        fine = dataclasses.replace(
            coarse,
            pixel_mm_object=200.0 / 1024.0,
            noise_scale_at_reference=coarse.noise_scale,
        )
        assert fine.noise_scale == pytest.approx(coarse.noise_scale)

        from ptx.chain import ct_nps_variance

        def variance(acquisition):
            return ct_nps_variance(
                acquisition.nyquist_lpmm,
                acquisition.f50,
                acquisition.kernel_sharpness,
                acquisition.ramp_exponent,
                acquisition.noise_scale,
            )

        assert variance(fine) > variance(coarse)

    def test_explicit_scale_still_tracks_dose(self):
        base = Acquisition(noise_scale_at_reference=1.0)
        quarter = dataclasses.replace(base, dose_relative=0.25)
        assert quarter.noise_scale == pytest.approx(4.0 * base.noise_scale)


class TestCaseUHRCT:
    def test_sufficient_magnification_finds_the_knee(self):
        mags = np.array([0.5, 1.0, 2.0, 4.0])
        dprimes = np.array([0.5, 0.9, 0.99, 1.0])
        assert sufficient_magnification(mags, dprimes, 0.95) == 2.0
        assert sufficient_magnification(mags, dprimes, 0.8) == 1.0
        with pytest.raises(ValueError):
            sufficient_magnification(mags, dprimes[:2])

    def test_dprime_is_monotone_and_saturating_in_magnification(
        self, small_case
    ):
        # H3 as adopted in v0.4: a sufficient magnification exists, an optimum
        # does not
        _, results = small_case
        assert results["summary"]["dprime_monotone_in_magnification"]
        for row in results["sufficiency"]:
            for chain in ("conventional", "u-hrct"):
                assert row[chain]["m_star"] < max(
                    p["magnification"] for p in results["points"]
                )

    def test_the_added_band_needs_magnification_to_arrive(self, small_case):
        # at low magnification the display and ocular MTF remove the extra
        # band, so finer sampling buys nothing until the image is enlarged;
        # past that the share saturates like d' does
        _, results = small_case
        by_mag = {}
        for point in results["points"]:
            if point["diameter_mm"] != 0.5:
                continue
            by_mag[point["magnification"]] = point["u-hrct"][
                "added_band_share"
            ]
        assert by_mag[0.25] < 1e-5
        assert by_mag[1.0] > by_mag[0.5] > 100.0 * by_mag[0.25]
        assert by_mag[4.0] == pytest.approx(by_mag[2.0], rel=0.05)

    def test_finer_sampling_only_helps_tasks_that_reach_that_band(
        self, small_case
    ):
        _, results = small_case
        rows = {
            row["diameter_mm"]: row
            for row in results["summary"]["by_diameter"]["rows"]
        }
        assert rows[0.5]["added_band_share_max"] > 10.0 * rows[4.0][
            "added_band_share_max"
        ]
        assert (
            rows[0.5]["dprime_ratio_at_reference"]
            > rows[4.0]["dprime_ratio_at_reference"]
        )
        # and where the extra band matters most, nothing is detectable anyway
        assert rows[0.5]["dprime_uhrct_at_reference"] < 1.0
        assert rows[4.0]["dprime_uhrct_at_reference"] > 1.0

    def test_uhrct_recovers_frequencies_the_conventional_chain_cannot(
        self, small_case
    ):
        cfg, results = small_case
        conventional_nyquist = cfg.conventional.nyquist_lpmm
        best = max(
            (
                p
                for p in results["points"]
                if p["diameter_mm"] == 0.5
            ),
            key=lambda p: p["u-hrct"]["f_sat_95_lpmm"],
        )
        assert best["u-hrct"]["f_sat_95_lpmm"] > conventional_nyquist
        assert best["conventional"]["f_sat_95_lpmm"] < conventional_nyquist

    def test_determinism(self, small_case):
        cfg, results = small_case
        again = run_case_uhrct(cfg)
        assert again["points"] == results["points"]
        assert again["summary"] == results["summary"]

    def test_config_guards(self):
        with pytest.raises(ValueError):
            CaseConfig(uhrct=ChainSpec("too-coarse", 1.2, 1.0))
        with pytest.raises(ValueError):
            CaseConfig(magnifications=(1.0,))


class TestConditionApi:
    def test_chain_uses_the_declared_f50_override(self):
        acquisition = Acquisition(f50_lpmm=1.2)
        f = frequency_grid(acquisition, 256)
        chain = build_chain(f, acquisition, Reading())
        # H_scanner is 0.5 at the declared f50 by construction
        assert np.interp(1.2, f, chain.h_scanner) == pytest.approx(0.5, rel=1e-3)

    def test_unknown_kernel_is_rejected(self):
        with pytest.raises(ValueError):
            Acquisition(kernel="ultra")

    def test_scalars_are_json_friendly(self):
        acquisition = Acquisition()
        f = frequency_grid(acquisition, 256)
        scalars = evaluate(
            f, Task(4.0, 250.0), acquisition, Reading(), (0.90, 0.95)
        ).scalars()
        assert set(scalars) == {
            "dprime_human",
            "dprime_ideal",
            "r_perceptual",
            "neural_noise_share",
            "quantisation_noise_share",
            "f_sat_90_lpmm",
            "f_sat_95_lpmm",
        }
        assert all(isinstance(v, float) for v in scalars.values())
