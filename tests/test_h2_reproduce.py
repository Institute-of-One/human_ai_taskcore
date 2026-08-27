"""Per-study reproduction configs, and the gate that keeps H2 a pool result."""

import dataclasses

import pytest

from ptx.external import Registry, load_registry
from ptx.h2_reproduce import (
    STUDY_REPRODUCTIONS,
    PoolNotReady,
    gate_pool,
    outstanding_parameters,
)


class TestConfigs:
    def test_every_admitted_study_has_a_config(self):
        assert set(STUDY_REPRODUCTIONS) == {"yu2013", "paul2007", "leng2013"}

    def test_the_dose_axis_is_a_ratio_of_reported_exposures(self):
        for config in STUDY_REPRODUCTIONS.values():
            assert config.dose_reference_label in config.dose_axis
            assert config.dose_axis[config.dose_reference_label] == 1.0

    def test_unread_parameters_are_refused_rather_than_defaulted(self):
        # a default standing in for a value the paper states would put an
        # invented number into the validation
        from ptx.h2_reproduce import StudyReproduction

        config = StudyReproduction(
            study_id="pending_example",
            source="test",
            task_diameters_mm=(3.0,),
            task_contrast_hu=-15.0,
            dose_axis={"1": 1.0},
            dose_reference_label="1",
            pending_from_pdf=("pixel_mm_object",),
        )
        with pytest.raises(PoolNotReady) as caught:
            config.build()
        assert "pending_example" in str(caught.value)

    def test_a_study_that_has_been_read_builds(self):
        for study_id in ("yu2013", "paul2007", "leng2013"):
            acquisition, reading = STUDY_REPRODUCTIONS[study_id].build()
            assert acquisition.slice_thickness_mm > 0
            assert reading.window_width_hu > 0

    def test_the_read_parameters_match_the_paper(self):
        acquisition, reading = STUDY_REPRODUCTIONS["yu2013"].build()
        # B40 kernel at MTF 50% = 3.97 cm^-1, 5 mm slices, and a 128-pixel ROI
        # spanning 6.2 cm
        assert acquisition.f50 == pytest.approx(0.397)
        assert acquisition.slice_thickness_mm == 5.0
        assert acquisition.pixel_mm_object == pytest.approx(0.484375)
        assert reading.distance_mm == 400.0
        assert reading.window_width_hu == 400.0

    def test_what_has_to_be_read_is_enumerated(self):
        # every admitted PDF has been read; outstanding is the empty set
        assert outstanding_parameters() == {}

    def test_leng2013_matches_the_pdf(self):
        acquisition, reading = STUDY_REPRODUCTIONS["leng2013"].build()
        assert acquisition.slice_thickness_mm == 5.0
        assert acquisition.pixel_mm_object == 0.5
        assert reading.distance_mm == 550.0
        assert reading.window_width_hu == 400.0

    def test_unreported_parameters_are_declared_where_they_apply(self):
        # these take the declared defaults and get published as assumed, which
        # is only honest if the list of them is written down
        for study_id in ("yu2013", "paul2007", "leng2013"):
            assert STUDY_REPRODUCTIONS[study_id].unreported


class TestPoolGate:
    def test_an_incomplete_pool_refuses_to_be_analysed(self):
        """Constructed rather than read from the file.

        This test used to assert that the real registry was incomplete, which held
        while the pool was being built and stopped holding the moment it was
        finished -- so the test was measuring the state of the work rather than the
        behaviour of the gate. Dropping a study from the real pool exercises the
        gate and keeps doing so after the pool is complete.
        """
        registry = load_registry("data/h2_studies.json")
        short = dataclasses.replace(registry, studies=registry.studies[:1])
        with pytest.raises(PoolNotReady) as caught:
            gate_pool(short)
        assert "pool" in str(caught.value)

    def test_the_complete_pool_is_admitted(self):
        registry = load_registry("data/h2_studies.json")
        studies = gate_pool(registry)
        assert len(studies) == len(registry.studies)

    def test_the_gate_names_the_generality_requirement(self):
        # the requirement most likely to go unmet quietly
        registry = Registry("1.3", "2026-08-24")
        with pytest.raises(PoolNotReady) as caught:
            gate_pool(registry)
        assert "non-CT" in str(caught.value)


class TestAnalysisRun:
    """The recorded H2 result must stay the one the pre-registration produces."""

    def _result(self):
        import json
        from pathlib import Path

        path = Path("results/h2.json")
        if not path.is_file():
            pytest.skip("run python -m ptx.h2_analysis")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_the_recorded_result_is_reproducible(self):
        from ptx.h2_analysis import analyse

        recorded = self._result()
        fresh = analyse()
        for study_id, value in recorded["per_study"].items():
            assert fresh["per_study"][study_id]["spearman_rho"] == pytest.approx(
                value["spearman_rho"]
            )
        for name, value in recorded["pools"].items():
            if value.get("pooled_rho") is None:
                continue
            assert fresh["pools"][name]["pooled_rho"] == pytest.approx(
                value["pooled_rho"]
            )

    def test_the_failing_study_is_still_in_the_pool(self):
        """paul2007 is the one study below threshold. The pre-registration says a
        discordant study is reported and not dropped, and this is what makes that
        checkable rather than a promise."""
        recorded = self._result()
        assert "paul2007" in recorded["per_study"]
        assert recorded["per_study"]["paul2007"]["meets_threshold"] is False
        assert "paul2007" in recorded["pools"]["v1_2"]["studies"]

    def test_all_three_frozen_readings_agree_in_direction(self):
        """v1.1 section D: a widening of C2 must be shown not to have manufactured
        the conclusion."""
        pools = self._result()["pools"]
        verdicts = {
            name: pools[name]["h2_rejected"]
            for name in ("v1_0_strict", "v1_1", "v1_2")
            if pools[name].get("pooled_rho") is not None
        }
        assert len(set(verdicts.values())) == 1, verdicts

    def test_the_stratification_carries_no_verdict(self):
        """v1.3 section A.2 keeps stratification out of the success condition, so no
        stratum may carry a pass or fail field."""
        strata = self._result()["stratification_by_task_congruence"]["strata"]
        for value in strata.values():
            assert "meets_threshold" not in value
            assert "h2_rejected" not in value
