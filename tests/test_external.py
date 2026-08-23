"""H2 pre-registration: the frozen criteria and the analysis they license.

These tests exist to keep the criteria from drifting once real studies are in
front of us: every rule in docs/IORN-009A_H2_preregistration_v1.0.md that can
be checked mechanically is checked here.
"""

import dataclasses
import json

import numpy as np
import pytest
from scipy import stats

from ptx.external import (
    MIN_CONDITIONS_PER_STUDY,
    SCHEMA_VERSION,
    SPEARMAN_SUCCESS,
    ModelPredictor,
    ObservedCondition,
    Registry,
    ScreenedStudy,
    StudyRecord,
    auc_to_dprime,
    load_registry,
    metric_to_dprime,
    pc_2afc_to_dprime,
    pooled_calibration,
    rank_agreement,
    validate_registry,
    validate_study,
)


def _conditions(n=4, offset=0.0):
    return tuple(
        ObservedCondition(
            label=f"c{i}",
            metric_value=0.60 + 0.05 * i + offset,
            parameters={
                "diameter_mm": 6.0,
                "contrast_hu": 250.0,
                "dose_relative": 0.5 * (i + 1),
            },
            assumed_parameters={"distance_mm": 500.0},
        )
        for i in range(n)
    )


def _study(**overrides):
    defaults = dict(
        study_id="example2020",
        citation="Example et al. 2020, placeholder record for tests only",
        modality="ct",
        task="lung nodule detection",
        condition_axes=("dose", "reconstruction"),
        metric="auc",
        acquisition="table",
        reports_display_conditions=False,
        reports_reading_conditions=False,
        generality_check=False,
        n_readers=5,
        conditions=_conditions(),
    )
    defaults.update(overrides)
    return StudyRecord(**defaults)


class TestMetricConversion:
    def test_auc_matches_the_binormal_identity(self):
        # AUC = Phi(d'/sqrt(2)): d' = 1 corresponds to AUC = 0.7602
        assert auc_to_dprime(0.7602499) == pytest.approx(1.0, rel=1e-5)
        assert auc_to_dprime(0.5 + 1e-9) == pytest.approx(0.0, abs=1e-6)
        assert np.all(np.diff(auc_to_dprime([0.6, 0.7, 0.8, 0.9])) > 0)

    def test_two_afc_uses_the_same_relation(self):
        assert pc_2afc_to_dprime(0.7602499) == pytest.approx(1.0, rel=1e-5)

    def test_conversion_preserves_order(self):
        # the primary analysis is rank based, so it must not depend on this
        values = [0.62, 0.71, 0.68, 0.85]
        assert list(np.argsort(metric_to_dprime("auc", values))) == list(
            np.argsort(values)
        )

    def test_out_of_range_values_are_rejected(self):
        with pytest.raises(ValueError):
            auc_to_dprime(1.0)
        with pytest.raises(ValueError):
            pc_2afc_to_dprime(0.4)
        with pytest.raises(ValueError):
            metric_to_dprime("pc_4afc", 0.7)


class TestFrozenCriteria:
    def test_a_well_formed_study_passes(self):
        assert validate_study(_study()) == []

    def test_out_of_scope_modality_fails_c1(self):
        problems = validate_study(_study(modality="mri"))
        assert any(p.startswith("C1") for p in problems)

    def test_one_condition_axis_fails_c2(self):
        problems = validate_study(_study(condition_axes=("dose",)))
        assert any(p.startswith("C2") for p in problems)

    def test_too_few_condition_points_fails_c3(self):
        problems = validate_study(_study(conditions=_conditions(3)))
        assert any(p.startswith("C3") for p in problems)

    def test_unreported_conditions_demand_declared_assumptions(self):
        # C4 never excludes a study, but the substituted values must be visible
        bare = tuple(
            dataclasses.replace(c, assumed_parameters={})
            for c in _conditions()
        )
        problems = validate_study(_study(conditions=bare))
        assert any(p.startswith("C4") for p in problems)
        assert validate_study(
            _study(
                conditions=bare,
                reports_display_conditions=True,
                reports_reading_conditions=True,
            )
        ) == []

    def test_m_afc_beyond_two_alternatives_fails_c5(self):
        problems = validate_study(_study(metric="pc_4afc"))
        assert any(p.startswith("C5") for p in problems)

    def test_digitisation_beyond_five_percent_fails_c6(self):
        problems = validate_study(
            _study(
                acquisition="digitised_figure",
                digitisation_repeat_max_deviation=0.08,
            )
        )
        assert any(p.startswith("C6") for p in problems)
        assert (
            validate_study(
                _study(
                    acquisition="digitised_figure",
                    digitisation_repeat_max_deviation=0.03,
                )
            )
            == []
        )

    def test_table_sourced_data_cannot_claim_a_digitisation_error(self):
        problems = validate_study(
            _study(digitisation_repeat_max_deviation=0.01)
        )
        assert any(p.startswith("C6") for p in problems)

    def test_the_generality_check_cannot_be_a_ct_study(self):
        problems = validate_study(_study(generality_check=True))
        assert any("non-CT" in p for p in problems)
        assert (
            validate_study(
                _study(modality="chest_radiography", generality_check=True)
            )
            == []
        )


class TestPoolRequirements:
    def test_an_empty_registry_reports_every_unmet_pool_requirement(self):
        problems = validate_registry(
            Registry(schema_version=SCHEMA_VERSION, frozen="2026-08-23")
        )
        assert len(problems["pool"]) == 3

    def test_a_ct_only_pool_loses_the_generality_claim(self):
        studies = tuple(
            _study(study_id=f"s{i}", conditions=_conditions(5))
            for i in range(3)
        )
        problems = validate_registry(
            Registry(SCHEMA_VERSION, "2026-08-23", studies=studies)
        )
        assert len(problems["pool"]) == 1
        assert "non-CT" in problems["pool"][0]

    def test_a_complete_pool_validates(self):
        studies = (
            _study(study_id="ct1", conditions=_conditions(5)),
            _study(study_id="ct2", conditions=_conditions(5)),
            _study(
                study_id="cxr1",
                modality="chest_radiography",
                generality_check=True,
                conditions=_conditions(5),
            ),
        )
        assert validate_registry(
            Registry(SCHEMA_VERSION, "2026-08-23", studies=studies)
        ) == {}

    def test_exclusions_need_a_stated_reason(self):
        registry = Registry(
            SCHEMA_VERSION,
            "2026-08-23",
            screened=(
                ScreenedStudy("x2019", "Example", "C3", "   "),
            ),
        )
        assert "x2019" in validate_registry(registry)

    def test_schema_version_mismatch_is_caught(self):
        problems = validate_registry(Registry("0.9", "2026-08-23"))
        assert "schema" in problems


class TestRegistryFile:
    def test_the_registry_is_frozen_empty_before_the_search(self):
        registry = load_registry("data/h2_studies.json")
        assert registry.schema_version == SCHEMA_VERSION
        assert registry.studies == ()
        assert registry.screened == ()

    def test_the_registry_file_round_trips(self):
        payload = json.loads(
            open("data/h2_studies.json", encoding="utf-8").read()
        )
        assert set(payload) == {
            "schema_version",
            "frozen",
            "note",
            "studies",
            "screened",
        }


class TestAnalysis:
    def test_rank_agreement_is_scale_free(self):
        predicted = np.array([1.0, 2.0, 3.0, 4.0])
        observed = np.array([0.61, 0.70, 0.75, 0.82])
        agreement = rank_agreement(predicted, observed)
        assert agreement["spearman"] == pytest.approx(1.0)
        assert agreement["meets_success_criterion"]
        # any monotone transform of either side leaves it unchanged
        assert rank_agreement(
            np.exp(predicted), metric_to_dprime("auc", observed)
        )["spearman"] == pytest.approx(1.0)

    def test_reversed_ordering_fails_the_criterion(self):
        agreement = rank_agreement([1.0, 2.0, 3.0, 4.0], [4.0, 3.0, 2.0, 1.0])
        assert agreement["spearman"] == pytest.approx(-1.0)
        assert not agreement["meets_success_criterion"]

    def test_too_few_points_is_refused_rather_than_reported(self):
        with pytest.raises(ValueError):
            rank_agreement([1.0, 2.0], [1.0, 2.0])
        assert MIN_CONDITIONS_PER_STUDY == 4

    def test_pooling_standardises_within_study(self):
        # two studies on wildly different scales, both perfectly ordered
        pooled = pooled_calibration(
            [
                ([1.0, 2.0, 3.0, 4.0], [0.6, 0.7, 0.8, 0.9]),
                ([100.0, 200.0, 300.0, 400.0], [2.0, 4.0, 6.0, 8.0]),
            ]
        )
        assert pooled["pooled_spearman"] == pytest.approx(1.0)
        assert pooled["n_studies"] == 2
        assert pooled["n_points"] == 8
        assert pooled["studies_meeting_criterion"] == 2
        assert pooled["h2_supported"]

    def test_h2_is_not_supported_when_most_studies_miss(self):
        pooled = pooled_calibration(
            [
                ([1.0, 2.0, 3.0, 4.0], [0.9, 0.6, 0.8, 0.7]),
                ([1.0, 2.0, 3.0, 4.0], [0.8, 0.9, 0.6, 0.7]),
                ([1.0, 2.0, 3.0, 4.0], [0.6, 0.7, 0.8, 0.9]),
            ]
        )
        assert pooled["studies_meeting_criterion"] == 1
        assert not pooled["h2_supported"]
        assert pooled["per_study_spearman"]["min"] < SPEARMAN_SUCCESS

    def test_pooling_needs_something_to_pool(self):
        with pytest.raises(ValueError):
            pooled_calibration([])


class TestModelPredictor:
    def test_predictions_follow_dose(self):
        predictor = ModelPredictor(n_freq=512)
        study = _study()
        predicted = predictor.predict_study(study)
        assert np.all(np.diff(predicted) > 0)
        assert len(predictor.assumptions) == len(study.conditions)

    def test_every_assumed_parameter_is_recorded(self):
        predictor = ModelPredictor(n_freq=256)
        predictor({"diameter_mm": 6.0, "contrast_hu": 250.0, "label": "bare"})
        assumed = predictor.assumptions[0]["assumed"]
        assert "distance_mm" in assumed
        assert "magnification" in assumed
        assert "dose_relative" in assumed

    def test_reported_parameters_are_not_recorded_as_assumed(self):
        predictor = ModelPredictor(n_freq=256)
        predictor(
            {
                "diameter_mm": 6.0,
                "contrast_hu": 250.0,
                "distance_mm": 600.0,
                "magnification": 2.0,
                "label": "reported",
            }
        )
        assumed = predictor.assumptions[0]["assumed"]
        assert "distance_mm" not in assumed
        assert "magnification" not in assumed

    def test_the_task_cannot_be_assumed(self):
        predictor = ModelPredictor(n_freq=256)
        with pytest.raises(ValueError):
            predictor({"dose_relative": 1.0})

    def test_magnification_is_converted_to_pixel_zoom(self):
        # a study reports apparent size; the chain needs display pixels per
        # image pixel, and the two differ by pixel pitch over display pitch
        predictor = ModelPredictor(n_freq=256)
        coarse = predictor(
            {
                "diameter_mm": 6.0,
                "contrast_hu": 250.0,
                "magnification": 1.0,
                "pixel_mm_object": 0.4,
            }
        )
        fine = predictor(
            {
                "diameter_mm": 6.0,
                "contrast_hu": 250.0,
                "magnification": 1.0,
                "pixel_mm_object": 0.2,
            }
        )
        # same apparent size, finer sampling: the finer chain cannot be worse
        assert fine > coarse

    def test_rank_agreement_runs_end_to_end_on_a_study_record(self):
        study = _study()
        predicted = ModelPredictor(n_freq=512).predict_study(study)
        observed = study.observed_dprime
        assert observed.shape == predicted.shape
        assert rank_agreement(predicted, observed)["spearman"] == pytest.approx(
            float(stats.spearmanr(predicted, observed).statistic)
        )
