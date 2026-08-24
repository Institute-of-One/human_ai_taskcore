"""C6 digitisation check: saturation split and the Paul 2007 reduction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path("data/h2_digitisation").resolve()))

import compare_passes as cmp


class TestYuC6:
    def test_passes_on_unsaturated_points(self):
        result = cmp.compare_yu()
        assert result["verdict"] == "PASS"
        assert result["n_matched"] == 42
        assert result["max_deviation_unsaturated_percent"] <= 5.0
        assert result["digitisation_repeat_max_deviation"] <= 0.05

    def test_saturated_and_unsaturated_are_reported_apart(self):
        result = cmp.compare_yu()
        assert result["n_unsaturated"] + result["n_saturated"] == result["n_matched"]
        assert result["n_saturated"] > 0
        # the ceiling cluster is allowed a larger reading scatter; it must
        # not be folded into the verdict statistic
        assert result["max_deviation_saturated_percent"] >= 0.0


class TestSaturationFlag:
    def test_threshold_is_99_5_percent(self):
        assert cmp.is_saturated(99.4) is False
        assert cmp.is_saturated(99.5) is True
        assert cmp.is_saturated(0.994) is False
        assert cmp.is_saturated(0.995) is True
        assert cmp.as_fraction(88.3) == 0.883


class TestPaulReduction:
    def test_c6_passes_on_the_reduced_set(self):
        result = cmp.compare_paul()
        assert result["verdict"] == "PASS_REDUCED"
        assert result["n_kept"] >= 4
        assert result["max_deviation_unsaturated_percent"] <= 5.0

    def test_the_paper_count_below_1_mgy_is_the_truth(self):
        result = cmp.compare_paul()
        assert result["n_below_1_mgy_paper"] == 9
        assert result["n_below_1_mgy_kept"] == 7

    def test_uncertain_flags_are_all_dropped(self):
        decisions = cmp.adjudicate_uncertain()
        assert len(decisions) == 8
        assert all(item["decision"] == "drop" for item in decisions)
        assert sum(1 for item in decisions if item["panel"] == "b") == 3
        assert sum(1 for item in decisions if item["panel"] == "d") == 5

    def test_kept_set_has_no_uncertain_flags(self):
        kept, dropped = cmp.paul_reduction()
        assert all(not cmp.is_uncertain(row) for row in kept)
        assert all(cmp.is_uncertain(row) for row in dropped)
