"""Analytic sanity anchors for ptx.detectability."""

import numpy as np
import pytest

from ptx.detectability import (
    contribution_density,
    dprime_squared,
    f_sat,
    g_useful,
    r_perceptual,
)


def _flat_grid():
    f = np.linspace(0.0, 1.0, 1001)
    ones = np.ones_like(f)
    return f, ones


class TestDprime:
    def test_unit_integral(self):
        f, ones = _flat_grid()
        assert dprime_squared(f, ones, ones, ones, ones) == pytest.approx(1.0, rel=1e-6)

    def test_noise_scaling_halves(self):
        f, ones = _flat_grid()
        d2 = dprime_squared(f, ones, ones, ones, 2.0 * ones)
        assert d2 == pytest.approx(0.5, rel=1e-6)

    def test_eta_cog_linear(self):
        f, ones = _flat_grid()
        d2 = dprime_squared(f, ones, ones, ones, ones, eta_cog=0.3)
        assert d2 == pytest.approx(0.3, rel=1e-6)


class TestFsat:
    def test_flat_density_gives_fraction(self):
        f, ones = _flat_grid()
        assert f_sat(f, ones, fraction=0.95) == pytest.approx(0.95, rel=1e-4)

    def test_bandlimited_density_saturates_at_cutoff(self):
        f, ones = _flat_grid()
        dens = np.where(f <= 0.5, 1.0, 0.0)
        assert f_sat(f, dens, fraction=0.95) <= 0.5 + 1e-6

    def test_fraction_guard(self):
        f, ones = _flat_grid()
        with pytest.raises(ValueError):
            f_sat(f, ones, fraction=1.5)


class TestDerived:
    def test_r_perceptual(self):
        assert r_perceptual(1.0, 2.0) == pytest.approx(0.5)

    def test_g_useful_slopes(self):
        g = g_useful([1.0, 2.0, 2.5], [1.0, 2.0, 3.0])
        assert g == pytest.approx([1.0, 0.5])

    def test_density_positive_noise_guard(self):
        f, ones = _flat_grid()
        with pytest.raises(ValueError):
            contribution_density(f, ones, ones, ones, 0.0 * ones)
