"""The measured MTF/NPS input path, and the promise that adding it changed nothing.

Pre-registration v2.0 section 7 allows a non-CT system to enter the chain by its
measured transfer and noise, because the second-round pool admits studies that
have no reconstruction kernel. It also requires that the CT path keep producing
exactly what it produced before: the first-round result is frozen and must stay
reproducible from this code.

So the first test here is not about the new path at all. It pins the old one.
"""

from __future__ import annotations

import numpy as np
import pytest

from ptx.condition import Acquisition, Reading, Task, build_chain, evaluate, frequency_grid


def _grid():
    return frequency_grid(Acquisition())


class TestTheCtPathIsUnchanged:
    """Re-running phase 1 after this change reproduced results/phase1.json byte for
    byte, metadata included. That is the real check and it is too slow to run here,
    so these pin the same property on one condition and on the assembled chain."""

    def test_the_chain_is_identical_to_the_kernel_route(self):
        from ptx.chain import ct_nps, ct_ttf

        acquisition = Acquisition(kernel="standard", dose_relative=0.5)
        f = _grid()
        assert np.array_equal(
            acquisition.mtf(f), ct_ttf(f, acquisition.f50, acquisition.kernel_sharpness)
        )
        assert np.array_equal(
            acquisition.nps(f),
            ct_nps(
                f,
                acquisition.f50,
                acquisition.kernel_sharpness,
                acquisition.ramp_exponent,
                acquisition.noise_scale,
            ),
        )

    def test_a_reference_condition_still_evaluates_to_the_same_numbers(self):
        """A regression pin. If a later change to the input path moves these, the
        frozen first-round result is no longer reproducible from this code."""
        result = evaluate(
            _grid(),
            Task(diameter_mm=3.0, contrast_hu=-50.0),
            Acquisition(kernel="standard", dose_relative=1.0, slice_thickness_mm=1.0),
            Reading(),
        )
        assert result.dprime_human == pytest.approx(1.2381995943737591, rel=1e-9)
        assert result.r_perceptual == pytest.approx(0.3714860086809106, rel=1e-9)

    def test_the_kernel_route_still_refuses_an_unknown_kernel(self):
        with pytest.raises(ValueError, match="unknown kernel"):
            Acquisition(kernel="not-a-kernel")


def _measured(**overrides):
    """A plausible projection system: MTF falling to zero by 5 lp/mm, white noise."""
    mtf = tuple((f, float(np.exp(-((f / 2.5) ** 2)))) for f in np.linspace(0, 6.0, 25))
    nps = tuple((f, 1.0e-4) for f in np.linspace(0, 6.0, 25))
    kwargs = dict(
        mtf_points=mtf,
        nps_points=nps,
        mtf_source="detector MTF, table 2 of the cited system characterisation",
        nps_source="detector NPS at the stated exposure, figure 4 of the same",
        pixel_mm_object=0.1,
        slice_thickness_mm=None,
        dose_relative=1.0,
    )
    kwargs.update(overrides)
    return Acquisition(**kwargs)


class TestTheMeasuredPath:
    def test_a_projection_system_evaluates_end_to_end(self):
        acquisition = _measured()
        f = frequency_grid(acquisition)
        result = evaluate(f, Task(diameter_mm=1.0, contrast_hu=-100.0), acquisition, Reading())
        assert np.isfinite(result.dprime_human) and result.dprime_human > 0
        assert 0.0 < result.r_perceptual <= 1.0

    def test_a_projection_carries_no_partial_volume_loss(self):
        """slice_thickness_mm=None is what a lesion imaged without slice selection
        has, and it must reach the task rather than being silently defaulted."""
        acquisition = _measured()
        assert acquisition.slice_thickness_mm is None
        f = frequency_grid(acquisition)
        task = Task(diameter_mm=1.0, contrast_hu=-100.0)
        assert np.array_equal(task.spectrum(f, acquisition.slice_thickness_mm),
                              task.spectrum(f, None))

    def test_the_chain_uses_the_tabulated_curves(self):
        acquisition = _measured()
        f = frequency_grid(acquisition)
        # Compared against the interpolation of the table itself, not against the
        # analytic curve the table was sampled from: the property under test is
        # that the chain reads the table, and a tolerance wide enough to absorb
        # interpolation error would also absorb reading the wrong curve.
        xs = np.array([x for x, _ in acquisition.mtf_points])
        ys = np.array([y for _, y in acquisition.mtf_points])
        assert np.array_equal(acquisition.mtf(f), np.interp(f, xs, ys, left=ys[0], right=ys[-1]))
        assert np.allclose(acquisition.nps(f), 1.0e-4)

    def test_dose_scales_the_measured_noise_the_way_it_scales_the_ct_noise(self):
        full, half = _measured(dose_relative=1.0), _measured(dose_relative=0.5)
        f = frequency_grid(full)
        assert np.allclose(half.nps(f), 2.0 * full.nps(f))

    def test_f50_is_read_off_the_curve_rather_than_stored(self):
        """A stored f50 could disagree with the MTF the chain actually uses."""
        assert _measured().f50 == pytest.approx(2.5 * np.sqrt(np.log(2.0)), rel=1e-3)


class TestTheMeasuredPathRefusesWhatItCannotJustify:
    def test_one_curve_without_the_other_is_refused(self):
        """Taking the missing half from a CT kernel would mix a measured system
        with a reconstruction it does not have."""
        with pytest.raises(ValueError, match="needs both"):
            Acquisition(mtf_points=((0.0, 1.0), (1.0, 0.5)), mtf_source="x", nps_source="y")

    def test_a_curve_with_no_stated_origin_is_refused(self):
        with pytest.raises(ValueError, match="where the curves came from"):
            _measured(mtf_source="   ")

    def test_an_mtf_not_normalised_at_zero_is_refused(self):
        with pytest.raises(ValueError, match="normalised to 1"):
            _measured(mtf_points=((0.0, 0.9), (1.0, 0.5), (2.0, 0.2)))

    def test_an_mtf_that_does_not_start_at_zero_frequency_is_refused(self):
        """Extrapolating to the origin would invent the low-frequency behaviour,
        which is where most of a detection task's energy sits."""
        with pytest.raises(ValueError, match="from zero frequency"):
            _measured(mtf_points=((0.5, 1.0), (1.0, 0.5), (2.0, 0.2)))

    def test_frequencies_must_increase(self):
        with pytest.raises(ValueError, match="increase strictly"):
            _measured(nps_points=((0.0, 1.0), (2.0, 1.0), (1.0, 1.0)))

    def test_a_grid_beyond_the_table_is_refused_rather_than_extrapolated(self):
        """The silent failure this replaces: a linear extrapolation of an MTF
        crosses zero and goes negative, inventing a sign change no system has."""
        acquisition = _measured()
        with pytest.raises(ValueError, match="tabulated only to"):
            acquisition.mtf(np.linspace(0.0, 9.0, 32))

    def test_the_ct_path_still_requires_a_slice_thickness(self):
        with pytest.raises(ValueError, match="needs a slice thickness"):
            Acquisition(slice_thickness_mm=None)
