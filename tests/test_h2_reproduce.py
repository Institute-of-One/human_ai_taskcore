"""Per-study reproduction configs, and the gate that keeps H2 a pool result."""

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
        config = STUDY_REPRODUCTIONS["leng2013"]
        with pytest.raises(PoolNotReady) as caught:
            config.build()
        assert "leng2013" in str(caught.value)

    def test_a_study_that_has_been_read_builds(self):
        for study_id in ("yu2013", "paul2007"):
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
        outstanding = outstanding_parameters()
        assert set(outstanding) == {"leng2013"}
        for pending in outstanding.values():
            assert pending

    def test_unreported_parameters_are_declared_where_they_apply(self):
        # these take the declared defaults and get published as assumed, which
        # is only honest if the list of them is written down
        for study_id in ("yu2013", "paul2007"):
            assert STUDY_REPRODUCTIONS[study_id].unreported


class TestPoolGate:
    def test_an_incomplete_pool_refuses_to_be_analysed(self):
        registry = load_registry("data/h2_studies.json")
        with pytest.raises(PoolNotReady) as caught:
            gate_pool(registry)
        assert "pool" in str(caught.value)

    def test_the_gate_names_the_generality_requirement(self):
        # the requirement most likely to go unmet quietly
        registry = Registry("1.3", "2026-08-24")
        with pytest.raises(PoolNotReady) as caught:
            gate_pool(registry)
        assert "non-CT" in str(caught.value)
