"""Determinism and analytic anchors for phantom and observer modules."""

import numpy as np
import pytest

from ptx.detectability import dprime_squared
from ptx.observer import cho_dprime_squared, npwe_dprime_squared
from ptx.phantom_lung import insert_gaussian_nodule, power_law_texture


class TestPhantom:
    def test_deterministic_same_seed(self):
        a = power_law_texture((64, 64), beta=3.0, seed=42)
        b = power_law_texture((64, 64), beta=3.0, seed=42)
        assert np.array_equal(a, b)

    def test_different_seed_differs(self):
        a = power_law_texture((64, 64), beta=3.0, seed=42)
        b = power_law_texture((64, 64), beta=3.0, seed=43)
        assert not np.array_equal(a, b)

    def test_spectral_slope_close_to_beta(self):
        beta = 3.0
        x = power_law_texture((256, 256), beta=beta, seed=7)
        ps = np.abs(np.fft.fftn(x)) ** 2
        fx, fy = np.meshgrid(
            np.fft.fftfreq(256), np.fft.fftfreq(256), indexing="ij"
        )
        f = np.sqrt(fx**2 + fy**2).ravel()
        p = ps.ravel()
        mask = (f > 0.02) & (f < 0.3)
        slope = np.polyfit(np.log(f[mask]), np.log(p[mask]), 1)[0]
        assert slope == pytest.approx(-beta, abs=0.5)

    def test_nodule_raises_center_value(self):
        vol = np.zeros((32, 32))
        out = insert_gaussian_nodule(vol, center=(16, 16), diameter_px=6, contrast=10.0)
        assert out[16, 16] == pytest.approx(10.0, rel=1e-6)
        assert vol[16, 16] == 0.0  # input untouched


class TestNPWE:
    def test_reduces_to_ideal_with_unit_eye_filter(self):
        f = np.linspace(0.0, 1.0, 501)
        s = np.exp(-f)          # arbitrary signal spectrum
        n = np.full_like(f, 2.0)  # white noise
        ideal = dprime_squared(f, s, np.ones_like(f), np.ones_like(f), n)
        npwe = npwe_dprime_squared(f, s, n, eye_filter=None)
        assert npwe == pytest.approx(ideal, rel=1e-9)

    def test_eye_filter_never_raises_dprime_in_white_noise(self):
        f = np.linspace(0.0, 1.0, 501)
        s = np.exp(-f)
        n = np.ones_like(f)
        e = np.exp(-2.0 * f)    # low-pass eye
        assert npwe_dprime_squared(f, s, n, e) <= npwe_dprime_squared(f, s, n)

    def test_cho_is_declared_future_work(self):
        with pytest.raises(NotImplementedError):
            cho_dprime_squared()
