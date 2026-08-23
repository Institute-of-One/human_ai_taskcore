"""Literature-anchor tests for ptx.chain (design principle no. 3)."""

import numpy as np
import pytest

from ptx.chain import (
    CT_KERNEL_F50_LPMM,
    ViewingGeometry,
    assemble_chain,
    barten_csf,
    barten_csf_peak,
    barten_integration_area_deg2,
    barten_visual_noise_density,
    ct_nps,
    ct_nps_scale_for_variance,
    ct_nps_variance,
    ct_ttf,
    cycles_per_mm_to_cycles_per_degree,
    display_pixel_mtf,
    display_quantisation_noise_power,
    eye_mtf,
    gsdf_jnd_contrast,
    gsdf_luminance,
    neural_noise_power,
    pupil_diameter_mm,
    quantum_noise_scaling,
    radial_band_integral,
)
from ptx.detectability import dprime_squared


class TestGSDF:
    def test_anchor_j1_is_005_cdm2(self):
        # DICOM PS3.14: at j=1 every log term vanishes -> L = 10^a = 0.05
        assert gsdf_luminance(1.0) == pytest.approx(0.05, rel=1e-3)

    def test_anchor_j1023_near_4000_cdm2(self):
        # PS3.14 defines the GSDF over ~0.05..~4000 cd/m^2
        assert 3500.0 < gsdf_luminance(1023.0) < 4100.0

    def test_strictly_monotonic(self):
        j = np.arange(1.0, 1024.0)
        L = gsdf_luminance(j)
        assert np.all(np.diff(L) > 0)

    def test_jnd_contrast_in_published_band(self):
        # PS3.14 behaviour: per-JND Weber contrast ~9% at the dark end
        # (0.05 cd/m^2), monotonically falling below 1% photopically
        j = np.arange(1.0, 1023.0)
        c = gsdf_jnd_contrast(j)
        assert np.all(c > 0.002) and np.all(c < 0.11)
        assert c[0] > 0.05          # scotopic end is coarse
        assert c[-1] < 0.01         # photopic end is fine
        assert np.all(np.diff(c) < 1e-4)  # essentially monotone decreasing

    def test_domain_guard(self):
        with pytest.raises(ValueError):
            gsdf_luminance(0.5)


class TestDisplayMTF:
    def test_dc_is_unity_and_first_zero_at_inverse_pitch(self):
        assert display_pixel_mtf(0.0, 0.2) == pytest.approx(1.0)
        assert display_pixel_mtf(5.0, 0.2) == pytest.approx(0.0, abs=1e-12)

    def test_monotone_decrease_to_first_zero(self):
        f = np.linspace(0.0, 4.999, 200)
        m = display_pixel_mtf(f, 0.2)
        assert np.all(np.diff(m) < 1e-12)


class TestEye:
    def test_pupil_shrinks_with_luminance(self):
        # Barten 1999 eq. 2.5: ~5mm in the dark to ~2mm photopic
        d_dark = pupil_diameter_mm(0.01)
        d_bright = pupil_diameter_mm(1000.0)
        assert d_dark > d_bright
        assert 2.0 < d_bright < 3.5
        assert 4.5 < d_dark < 8.5

    def test_eye_mtf_unity_at_dc_and_decreasing(self):
        u = np.linspace(0.0, 60.0, 300)
        m = eye_mtf(u, pupil_mm=3.0)
        assert m[0] == pytest.approx(1.0)
        assert np.all(np.diff(m) < 0)


class TestBartenCSF:
    def test_peak_location_photopic(self):
        # canonical: photopic CSF peaks at ~2-6 cpd
        u = np.linspace(0.1, 40.0, 2000)
        s = barten_csf(u, luminance_cdm2=100.0, field_deg=10.0)
        u_peak = u[int(np.argmax(s))]
        assert 2.0 < u_peak < 6.0

    def test_peak_magnitude_order(self):
        # peak sensitivity O(100) for the standard observer at 100 cd/m^2
        u = np.linspace(0.1, 40.0, 2000)
        s = barten_csf(u, luminance_cdm2=100.0, field_deg=10.0)
        assert 50.0 < s.max() < 1000.0

    def test_highfreq_rolloff(self):
        u = np.linspace(0.1, 40.0, 2000)
        s = barten_csf(u, luminance_cdm2=100.0, field_deg=10.0)
        assert s[-1] < 0.1 * s.max()

    def test_sensitivity_drops_at_low_luminance(self):
        u = np.linspace(0.5, 30.0, 500)
        s_hi = barten_csf(u, luminance_cdm2=100.0)
        s_lo = barten_csf(u, luminance_cdm2=0.1)
        assert s_lo.max() < s_hi.max()


    def test_optics_factorises_without_double_counting(self):
        # barten_csf(include_optics=False) is defined so that multiplying by
        # the ocular MTF returns the published CSF; a chain carrying eye_mtf
        # in H_effective must use the neural form
        u = np.linspace(0.1, 40.0, 500)
        pupil = pupil_diameter_mm(100.0, field_deg=10.0)
        neural = barten_csf(u, 100.0, 10.0, include_optics=False)
        full = barten_csf(u, 100.0, 10.0)
        assert np.allclose(neural * eye_mtf(u, pupil), full, rtol=1e-12)

    def test_neural_csf_exceeds_full_csf(self):
        u = np.linspace(1.0, 40.0, 200)
        assert np.all(
            barten_csf(u, include_optics=False) >= barten_csf(u) - 1e-12
        )

    def test_peak_matches_scanned_maximum(self):
        peak = barten_csf_peak(100.0, 10.0, True)
        u = np.linspace(0.01, 60.0, 20000)
        assert peak == pytest.approx(barten_csf(u, 100.0, 10.0).max(), rel=1e-3)


class TestVisualNoise:
    def test_noise_density_is_the_csf_turned_inside_out(self):
        # Phi(u) = A_int(u) / (2 k^2 S_neural(u)^2) — the v0.4 primary form and
        # the superseded numerator-weight form are one model, so this identity
        # must hold to machine precision for every luminance and field size
        u = np.linspace(0.1, 40.0, 400)
        for luminance, field in ((100.0, 10.0), (5.0, 20.0), (400.0, 4.0)):
            phi = barten_visual_noise_density(u, luminance, field)
            neural = barten_csf(u, luminance, field, include_optics=False)
            implied = barten_integration_area_deg2(u, field) / (
                2.0 * 3.0**2 * neural**2
            )
            assert np.allclose(phi, implied, rtol=1e-12)

    def test_integration_area_is_capped_by_barten_limits(self):
        # never more than Xmax = 12 deg across nor Nmax = 15 cycles
        assert barten_integration_area_deg2(0.0, 1e6) == pytest.approx(144.0)
        assert barten_integration_area_deg2(100.0, 1e6) == pytest.approx(
            (15.0 / 100.0) ** 2, rel=1e-3
        )
        assert barten_integration_area_deg2(0.0, 4.0) < 4.0**2

    def test_noise_density_falls_with_luminance_and_rises_at_low_frequency(self):
        u = np.linspace(0.5, 30.0, 200)
        bright = barten_visual_noise_density(u, 400.0, 10.0)
        dim = barten_visual_noise_density(u, 1.0, 10.0)
        assert np.all(dim > bright)
        assert barten_visual_noise_density(0.2) > barten_visual_noise_density(10.0)


class TestGeometry:
    def test_cpmm_to_cpd_roundtrip(self):
        # at 500 mm viewing distance 1 deg ~ 8.73 mm on the display
        u = cycles_per_mm_to_cycles_per_degree(1.0, 500.0)
        assert u == pytest.approx(500.0 * np.tan(np.deg2rad(1.0)), rel=1e-12)

    def test_radial_integral_of_constant_is_disk_area(self):
        # 2 pi Int_0^R c f df = pi c R^2
        f = np.linspace(0.0, 2.0, 4001)
        assert radial_band_integral(f, np.full_like(f, 3.0)) == pytest.approx(
            np.pi * 3.0 * 4.0, rel=1e-6
        )


class TestCTAcquisition:
    def test_ttf_anchors_at_dc_and_f50(self):
        assert ct_ttf(0.0, 0.5) == pytest.approx(1.0)
        assert ct_ttf(0.5, 0.5) == pytest.approx(0.5, rel=1e-12)

    def test_ttf_monotone_decreasing(self):
        f = np.linspace(0.0, 2.0, 500)
        assert np.all(np.diff(ct_ttf(f, 0.5)) < 0)

    def test_sharper_kernel_transfers_more_at_high_frequency(self):
        f = np.linspace(0.0, 1.2, 200)
        smooth = ct_ttf(f, CT_KERNEL_F50_LPMM["smooth"])
        sharp = ct_ttf(f, CT_KERNEL_F50_LPMM["sharp"])
        assert np.all(sharp[1:] > smooth[1:])

    def test_nps_vanishes_at_dc_with_ramp(self):
        assert ct_nps(0.0, 0.5) == pytest.approx(0.0)

    def test_white_field_when_ramp_and_kernel_are_flat(self):
        f = np.linspace(0.0, 1.0, 50)
        nps = ct_nps(f, 1e6, ramp_exponent=0.0, scale=2.0)
        assert np.allclose(nps, 2.0, rtol=1e-6)

    def test_variance_identity_round_trip(self):
        # int NPS d^2f == pixel variance, the standard NPS normalisation
        scale = ct_nps_scale_for_variance(50.0**2, 1.28, 0.5)
        var = ct_nps_variance(1.28, 0.5, scale=scale)
        assert var == pytest.approx(2500.0, rel=1e-6)

    def test_sharper_kernel_costs_noise(self):
        smooth = ct_nps_variance(1.28, CT_KERNEL_F50_LPMM["smooth"], scale=1.0)
        sharp = ct_nps_variance(1.28, CT_KERNEL_F50_LPMM["sharp"], scale=1.0)
        assert sharp > smooth

    def test_quantum_scaling_halves_with_dose_and_thickness(self):
        assert quantum_noise_scaling(2.0, 1.0) == pytest.approx(0.5)
        assert quantum_noise_scaling(1.0, 2.0) == pytest.approx(0.5)
        assert quantum_noise_scaling(1.0, 1.0) == pytest.approx(1.0)

    def test_guards(self):
        with pytest.raises(ValueError):
            ct_ttf(1.0, 0.0)
        with pytest.raises(ValueError):
            quantum_noise_scaling(0.0, 1.0)


class TestViewingGeometry:
    def _viewing(self, zoom=1.0):
        return ViewingGeometry(
            pixel_mm_object=0.4, display_pitch_mm=0.2, zoom=zoom,
            distance_mm=500.0,
        )

    def test_magnification_and_nyquist(self):
        v = self._viewing()
        assert v.magnification == pytest.approx(0.5)
        assert v.nyquist_object_lpmm == pytest.approx(1.25)

    def test_zoom_lowers_display_frequency(self):
        f = 1.0
        assert self._viewing(2.0).display_frequency(f) < self._viewing(
            1.0
        ).display_frequency(f)

    def test_angular_frequency_matches_manual_chain(self):
        v = self._viewing()
        expected = cycles_per_mm_to_cycles_per_degree(
            1.0 / v.magnification, 500.0
        )
        assert v.angular_frequency(1.0) == pytest.approx(expected)

    def test_object_scale_is_the_single_frequency_conversion(self):
        v = self._viewing()
        f = np.array([0.1, 0.5, 1.0])
        assert np.allclose(v.angular_frequency(f), f * v.object_mm_per_degree)

    def test_zoom_shrinks_the_object_seen_per_degree(self):
        assert self._viewing(2.0).object_mm_per_degree == pytest.approx(
            self._viewing(1.0).object_mm_per_degree / 2.0
        )

    def test_guard(self):
        with pytest.raises(ValueError):
            ViewingGeometry(pixel_mm_object=0.0)


class TestNoiseFloors:
    def test_quantisation_step_variance(self):
        v = ViewingGeometry(pixel_mm_object=0.4, zoom=1.0)
        step = 1500.0 / 256.0
        expected = step**2 / 12.0 * 0.4**2
        assert display_quantisation_noise_power(1500.0, 256, v) == pytest.approx(
            expected
        )

    def test_zoom_lowers_the_quantisation_floor(self):
        wide = ViewingGeometry(pixel_mm_object=0.4, zoom=1.0)
        zoomed = ViewingGeometry(pixel_mm_object=0.4, zoom=2.0)
        assert display_quantisation_noise_power(
            1500.0, 256, zoomed
        ) == pytest.approx(
            display_quantisation_noise_power(1500.0, 256, wide) / 4.0
        )

    def test_neural_noise_is_quadratic_in_kappa_and_window(self):
        f = np.linspace(0.01, 1.0, 100)
        v = ViewingGeometry(pixel_mm_object=0.4)
        base = neural_noise_power(f, v, 1500.0, 1.0)
        assert np.allclose(neural_noise_power(f, v, 1500.0, 2.0), 4.0 * base)
        assert np.allclose(neural_noise_power(f, v, 3000.0, 1.0), 4.0 * base)

    def test_neural_noise_becomes_scale_free_at_low_frequency(self):
        # at low angular frequency Barten's neural term goes as 1/u^2, and the
        # object-referred conversion carries a^2, so the two cancel: below the
        # lateral-inhibition corner the floor no longer depends on zoom. This
        # is why magnification cannot buy much (protocol v0.4, H3)
        f = np.linspace(0.005, 0.05, 50)
        wide = neural_noise_power(f, ViewingGeometry(0.4, zoom=1.0), 1500.0)
        zoomed = neural_noise_power(f, ViewingGeometry(0.4, zoom=8.0), 1500.0)
        assert np.allclose(zoomed, wide, rtol=0.05)

    def test_zero_kappa_is_no_floor(self):
        f = np.linspace(0.01, 1.0, 10)
        v = ViewingGeometry(pixel_mm_object=0.4)
        assert np.all(neural_noise_power(f, v, 1500.0, 0.0) == 0.0)

    def test_guards(self):
        f = np.linspace(0.01, 1.0, 10)
        v = ViewingGeometry(pixel_mm_object=0.4)
        with pytest.raises(ValueError):
            neural_noise_power(f, v, 1500.0, -1.0)
        with pytest.raises(ValueError):
            neural_noise_power(f, v, 0.0)


class TestChainAssembly:
    def _chain(self, f, f50, **kwargs):
        scale = ct_nps_scale_for_variance(2500.0, 1.28, 0.5)
        kwargs.setdefault("neural_noise_kappa", 0.0)
        return assemble_chain(
            f,
            ct_ttf(f, f50),
            ct_nps(f, f50, scale=scale),
            ViewingGeometry(pixel_mm_object=200.0 / 512.0),
            window_width_hu=1500.0,
            **kwargs,
        )

    def test_effective_transfer_is_the_stage_product(self):
        f = np.linspace(0.01, 1.28, 100)
        chain = self._chain(f, 0.5)
        assert np.allclose(
            chain.h_eff, chain.h_scanner * chain.h_display * chain.h_eye
        )

    def test_normalised_csf_weight_is_bounded_by_one(self):
        f = np.linspace(0.01, 1.28, 500)
        chain = self._chain(f, 0.5)
        assert chain.csf_weight.max() <= 1.0 + 1e-12

    def test_floors_only_raise_the_effective_noise(self):
        f = np.linspace(0.01, 1.28, 200)
        bare = self._chain(f, 0.5)
        floored = self._chain(f, 0.5, n_grey_levels=256, neural_noise_kappa=1.0)
        assert np.all(floored.n_eff > bare.n_eff)
        assert np.allclose(bare.n_eff, bare.displayed_image_noise)

    def test_kernel_cancels_without_noise_floors(self):
        # a quantum-limited FBP chain filters signal and noise with the same
        # lumped factor, so the kernel drops out of the detectability integral
        # exactly. This invertible-filter invariance is the validation anchor
        # of the implementation, and it holds in both the primary form and the
        # superseded numerator-weight form
        f = np.linspace(0.01, 1.28, 1000)
        w = np.exp(-f)
        smooth, sharp = self._chain(f, 0.30), self._chain(f, 0.75)
        for weight in (np.ones_like(f), smooth.csf_weight):
            assert dprime_squared(
                f, w, smooth.h_eff, weight, smooth.n_eff, radial=True
            ) == pytest.approx(
                dprime_squared(
                    f, w, sharp.h_eff, weight, sharp.n_eff, radial=True
                ),
                rel=1e-9,
            )

    def test_neural_floor_breaks_the_kernel_cancellation(self):
        # the neural noise bypasses every transfer factor, so it is the term
        # that makes reconstruction sharpness matter to a human observer
        f = np.linspace(0.01, 1.28, 1000)
        w = np.exp(-f)
        unit = np.ones_like(f)
        d2 = [
            dprime_squared(f, w, c.h_eff, unit, c.n_eff, radial=True)
            for c in (
                self._chain(f, 0.30, neural_noise_kappa=1.0),
                self._chain(f, 0.75, neural_noise_kappa=1.0),
            )
        ]
        assert d2[1] > d2[0] * (1.0 + 1e-6)

    def test_grid_mismatch_guard(self):
        f = np.linspace(0.01, 1.0, 10)
        with pytest.raises(ValueError):
            assemble_chain(
                f, np.ones(5), np.ones(10),
                ViewingGeometry(pixel_mm_object=0.4), window_width_hu=1500.0,
            )
