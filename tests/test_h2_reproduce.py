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
    def test_both_admitted_studies_have_a_config(self):
        assert set(STUDY_REPRODUCTIONS) == {"yu2013", "leng2013"}

    def test_the_dose_axis_is_a_ratio_of_reported_exposures(self):
        for config in STUDY_REPRODUCTIONS.values():
            assert config.dose_reference_label in config.dose_axis
            assert config.dose_axis[config.dose_reference_label] == 1.0

    def test_unread_parameters_are_refused_rather_than_defaulted(self):
        # a default standing in for a value the paper states would put an
        # invented number into the validation
        for study_id, config in STUDY_REPRODUCTIONS.items():
            with pytest.raises(PoolNotReady) as caught:
                config.build()
            assert study_id in str(caught.value)

    def test_what_has_to_be_read_is_enumerated(self):
        outstanding = outstanding_parameters()
        assert set(outstanding) == set(STUDY_REPRODUCTIONS)
        for pending in outstanding.values():
            assert pending


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
