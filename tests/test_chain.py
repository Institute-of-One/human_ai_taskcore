"""Literature-anchor tests for ptx.chain (design principle no. 3)."""

import numpy as np
import pytest

from ptx.chain import (
    barten_csf,
    cycles_per_mm_to_cycles_per_degree,
    display_pixel_mtf,
    eye_mtf,
    gsdf_jnd_contrast,
    gsdf_luminance,
    pupil_diameter_mm,
)


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


class TestGeometry:
    def test_cpmm_to_cpd_roundtrip(self):
        # at 500 mm viewing distance 1 deg ~ 8.73 mm on the display
        u = cycles_per_mm_to_cycles_per_degree(1.0, 500.0)
        assert u == pytest.approx(500.0 * np.tan(np.deg2rad(1.0)), rel=1e-12)
