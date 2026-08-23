"""Phase 1 runner: determinism and the hypothesis checks of section 7."""

import json

import numpy as np
import pytest

from ptx.phase1 import Phase1Config, run_phase1


@pytest.fixture(scope="module")
def small_run():
    """A reduced grid that keeps every axis of the protocol design."""
    cfg = Phase1Config(
        diameters_mm=(4.0, 8.0),
        contrasts_hu=(880.0,),
        doses_relative=(0.5, 1.0, 2.0, 4.0),
        slice_thicknesses_mm=(1.0,),
        kernels=("smooth", "sharp"),
        zooms=(1.0, 2.0),
        n_freq=256,
        n_channels=6,
    )
    return cfg, run_phase1(cfg)


class TestDeterminism:
    def test_same_config_gives_identical_json(self, small_run):
        cfg, first = small_run
        second = run_phase1(cfg)
        assert json.dumps(first, sort_keys=True) == json.dumps(
            second, sort_keys=True
        )

    def test_metadata_records_the_configuration(self, small_run):
        cfg, results = small_run
        meta = results["metadata"]
        assert meta["n_conditions"] == len(results["conditions"]) == 32
        assert meta["config"]["eta_cog"] == cfg.eta_cog


class TestSaturation:
    def test_f_sat_sits_below_the_sampling_nyquist(self, small_run):
        _, results = small_run
        nyquist = results["metadata"]["nyquist_lpmm"]
        for record in results["conditions"]:
            assert 0.0 < record["f_sat_95_lpmm"] < nyquist

    def test_f_sat_thresholds_are_ordered(self, small_run):
        _, results = small_run
        for record in results["conditions"]:
            assert (
                record["f_sat_90_lpmm"]
                <= record["f_sat_95_lpmm"]
                <= record["f_sat_99_lpmm"]
            )

    def test_g_useful_diminishes_in_every_dose_series(self, small_run):
        # H1: d' grows as sqrt(dose) in the quantum-limited regime, so the
        # gain per unit dose must fall monotonically
        _, results = small_run
        assert results["summary"]["dose_series_saturating_fraction"] == 1.0
        for series in results["dose_series"]:
            assert np.all(np.diff(series["g_useful"]) < 0)
            assert np.all(np.array(series["g_useful"]) > 0)

    def test_magnification_raises_the_perceptual_ceiling(self, small_run):
        # H3, constructive side: doubling the magnification maps the visual
        # passband onto twice the object frequency, so f_sat scales with zoom.
        # d'_human is *not* asserted to rise with it — the task band can move
        # below the CSF peak, which is the optimal-magnification effect the
        # zoom sweep is there to expose.
        _, results = small_run
        grouped = {}
        for record in results["conditions"]:
            key = (
                record["diameter_mm"],
                record["contrast_hu"],
                record["dose_relative"],
                record["slice_thickness_mm"],
                record["kernel"],
            )
            grouped.setdefault(key, {})[record["zoom"]] = record
        assert grouped
        for pair in grouped.values():
            ratio = pair[2.0]["f_sat_95_lpmm"] / pair[1.0]["f_sat_95_lpmm"]
            assert 1.0 < ratio <= 2.0 + 1e-9

    def test_magnification_gain_in_dprime_is_marginal(self, small_run):
        # H3 as adopted in v0.4: d' rises with magnification but towards an
        # asymptote, because below the lateral-inhibition corner the
        # object-referred neural floor stops depending on zoom. No interior
        # optimum appears in the linear formulation
        _, results = small_run
        grouped = {}
        for record in results["conditions"]:
            key = (
                record["diameter_mm"],
                record["contrast_hu"],
                record["dose_relative"],
                record["slice_thickness_mm"],
                record["kernel"],
            )
            grouped.setdefault(key, {})[record["zoom"]] = record
        for pair in grouped.values():
            gain = pair[2.0]["dprime_human"] / pair[1.0]["dprime_human"]
            assert 1.0 < gain < 1.3


class TestObserverConsistency:
    def test_perceptual_ratio_stays_a_ratio(self, small_run):
        _, results = small_run
        for record in results["conditions"]:
            assert 0.0 < record["r_perceptual"] < 1.0

    def test_larger_lesions_are_easier(self, small_run):
        _, results = small_run
        grouped = {}
        for record in results["conditions"]:
            key = (
                record["contrast_hu"],
                record["dose_relative"],
                record["slice_thickness_mm"],
                record["kernel"],
                record["zoom"],
            )
            grouped.setdefault(key, {})[record["diameter_mm"]] = record
        for pair in grouped.values():
            assert pair[8.0]["dprime_human"] > pair[4.0]["dprime_human"]

    def test_npwe_and_cho_rank_conditions_alike(self, small_run):
        # the two observer families agree on the condition ordering without
        # agreeing on the level: the Hotelling observer whitens inside its
        # channel subspace and so shrugs off the CSF that the non-prewhitening
        # template is stuck with. Keeping both is the model-choice sensitivity
        # analysis the protocol asks for, not a redundancy
        _, results = small_run
        agreement = results["summary"]["observer_agreement"]
        assert agreement["spearman_npwe_cho"] > 0.85
        assert agreement["spearman_human_npwe"] > 0.85
        assert agreement["spearman_human_cho"] > 0.85

    def test_sharpness_matters_only_through_the_neural_floor(self, small_run):
        # with the floors switched off the kernel filters signal and noise
        # alike and cancels to machine precision, in either formulation; the
        # physical sensitivity reported for the primary form is therefore
        # entirely attributable to the neural noise that bypasses it
        _, results = small_run
        invariance = results["summary"]["invertible_filter_invariance"]
        assert (
            invariance["max_relative_dprime2_spread_primary_form"] < 1e-12
        )
        assert (
            invariance["max_relative_dprime2_spread_csf_weight_form"] < 1e-12
        )
        assert (
            results["summary"]["kernel_sensitivity"][
                "median_relative_dprime_spread"
            ]
            > 0.01
        )

    def test_neural_noise_dominates_the_budget_at_routine_dose(self, small_run):
        # the display quantisation floor is retained for completeness but is
        # orders of magnitude below the neural floor, so it is not the
        # saturation mechanism
        _, results = small_run
        summary = results["summary"]
        assert summary["neural_noise_share"]["median"] > 0.3
        assert summary["quantisation_noise_share"]["max"] < 0.01


class TestConfigGuards:
    def test_unknown_kernel_is_rejected(self):
        with pytest.raises(ValueError):
            Phase1Config(kernels=("nonexistent",))

    def test_unusable_grid_is_rejected(self):
        with pytest.raises(ValueError):
            Phase1Config(n_freq=4)
