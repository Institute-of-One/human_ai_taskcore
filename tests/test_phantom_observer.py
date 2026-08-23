"""Determinism and analytic anchors for phantom and observer modules."""

import numpy as np
import pytest
from scipy.special import jn_zeros

from ptx.detectability import dprime_squared
from ptx.observer import (
    cho_dprime_squared,
    dog_channel_peak_factor,
    dog_channels,
    dog_channels_spanning,
    ideal_dprime_squared,
    npwe_dprime_squared,
)
from ptx.phantom_lung import (
    disk_spectrum,
    insert_gaussian_nodule,
    insert_spherical_nodule,
    lung_texture_hu,
    nodule_task_spectrum,
    partial_volume_contrast_factor,
    power_law_texture,
    rasterize_vessels,
    vessel_tree_segments,
    vessel_weight_map,
)


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


class TestLungTexture:
    def test_hu_calibration(self):
        x = lung_texture_hu((128, 128), voxel_mm=0.4, seed=3)
        assert x.mean() == pytest.approx(-850.0, abs=1e-6)
        assert x.std() == pytest.approx(40.0, rel=1e-6)

    def test_deterministic(self):
        kwargs = dict(shape=(64, 64), voxel_mm=0.4, seed=11)
        assert np.array_equal(lung_texture_hu(**kwargs), lung_texture_hu(**kwargs))

    def test_anisotropy_smooths_the_stretched_axis(self):
        # a frequency multiplier above 1 removes high frequencies along that
        # axis, so neighbouring voxels differ less along it
        aniso = lung_texture_hu(
            (128, 128), voxel_mm=0.4, seed=5, anisotropy=(4.0, 1.0)
        )
        rough_axis0 = np.diff(aniso, axis=0).std()
        rough_axis1 = np.diff(aniso, axis=1).std()
        assert rough_axis0 < rough_axis1

    def test_three_dimensional_grid(self):
        x = lung_texture_hu((16, 16, 8), voxel_mm=(0.4, 0.4, 1.0), seed=1)
        assert x.shape == (16, 16, 8)

    def test_guards(self):
        with pytest.raises(ValueError):
            lung_texture_hu((8, 8), voxel_mm=0.0, seed=1)
        with pytest.raises(ValueError):
            lung_texture_hu((8, 8), voxel_mm=0.4, seed=1, beta=-1.0)


class TestSphericalNodule:
    def test_center_reaches_full_contrast(self):
        vol = np.zeros((41, 41))
        out = insert_spherical_nodule(
            vol, center_mm=(4.0, 4.0), diameter_mm=3.0, contrast_hu=100.0,
            voxel_mm=0.2,
        )
        assert out[20, 20] == pytest.approx(100.0)
        assert vol[20, 20] == 0.0

    def test_integrated_contrast_matches_disk_area(self):
        voxel = 0.05
        n = 201
        vol = np.zeros((n, n))
        out = insert_spherical_nodule(
            vol, center_mm=(5.0, 5.0), diameter_mm=4.0, contrast_hu=1.0,
            voxel_mm=voxel,
        )
        integral = out.sum() * voxel**2
        assert integral == pytest.approx(np.pi * 4.0**2 / 4.0, rel=0.01)

    def test_guard(self):
        with pytest.raises(ValueError):
            insert_spherical_nodule(
                np.zeros((4, 4)), (1.0, 1.0), 0.0, 1.0, 0.5
            )


class TestVesselTree:
    def _tree(self, generations=4, radius=2.0, seed=1):
        return vessel_tree_segments(
            origin_mm=(2.0, 10.0), direction=(1.0, 0.0), length_mm=8.0,
            radius_mm=radius, generations=generations, seed=seed,
        )

    def test_segment_count_is_a_full_binary_tree(self):
        assert len(self._tree(generations=4)) == 2**4 - 1

    def test_murray_law_radii(self):
        # symmetric bifurcation with n = 3: r_child = r_parent 2^(-1/3)
        segments = self._tree(generations=3)
        by_generation = {}
        for seg in segments:
            by_generation.setdefault(seg.generation, set()).add(seg.radius_mm)
        for gen in range(1, 3):
            parent = next(iter(by_generation[gen - 1]))
            child = next(iter(by_generation[gen]))
            assert child == pytest.approx(parent * 2.0 ** (-1.0 / 3.0))

    def test_deterministic(self):
        assert self._tree(seed=7) == self._tree(seed=7)
        assert self._tree(seed=7) != self._tree(seed=8)

    def test_weight_map_is_an_occupancy_fraction(self):
        w = vessel_weight_map((64, 64), self._tree(), voxel_mm=0.4)
        assert w.min() >= 0.0 and w.max() <= 1.0
        assert w.max() == pytest.approx(1.0)

    def test_thicker_vessels_occupy_more(self):
        thin = vessel_weight_map((64, 64), self._tree(radius=1.0), voxel_mm=0.4)
        thick = vessel_weight_map((64, 64), self._tree(radius=2.0), voxel_mm=0.4)
        assert thick.sum() > thin.sum()

    def test_rasterisation_replaces_parenchyma(self):
        vol = np.full((64, 64), -850.0)
        out = rasterize_vessels(vol, self._tree(), voxel_mm=0.4, hu_value=50.0)
        assert out.max() == pytest.approx(50.0)
        assert out.min() == pytest.approx(-850.0)
        assert vol.max() == -850.0  # input untouched

    def test_guards(self):
        with pytest.raises(ValueError):
            self._tree(generations=0)
        with pytest.raises(ValueError):
            vessel_tree_segments(
                origin_mm=(0.0, 0.0), direction=(0.0, 0.0), length_mm=1.0,
                radius_mm=1.0, generations=1, seed=0,
            )


class TestTaskSpectrum:
    def test_dc_value_is_contrast_times_area(self):
        assert disk_spectrum(0.0, 4.0, 100.0) == pytest.approx(
            100.0 * np.pi * 4.0**2 / 4.0
        )

    def test_first_zero_at_first_bessel_root(self):
        # 2 J1(pi d f)/(pi d f) vanishes at pi d f = j_{1,1} = 3.8317
        diameter = 4.0
        f_zero = jn_zeros(1, 1)[0] / (np.pi * diameter)
        assert f_zero == pytest.approx(1.2197 / diameter, rel=1e-3)
        assert disk_spectrum(f_zero, diameter) == pytest.approx(0.0, abs=1e-12)

    def test_matches_the_rasterised_disk(self):
        # independent check of the analytic task function against a Fourier
        # transform of the phantom raster it is meant to describe
        voxel, n, diameter = 0.05, 256, 4.0
        centre = (n // 2) * voxel
        raster = insert_spherical_nodule(
            np.zeros((n, n)), (centre, centre), diameter, 1.0, voxel
        )
        spectrum = np.abs(np.fft.fft2(raster)) * voxel**2
        f = np.fft.fftfreq(n, d=voxel)
        analytic = np.abs(disk_spectrum(f[1:9], diameter))
        assert np.allclose(spectrum[1:9, 0], analytic, rtol=0.02)

    def test_partial_volume_branches_meet(self):
        d = 5.0
        assert partial_volume_contrast_factor(d, d) == pytest.approx(2.0 / 3.0)
        assert partial_volume_contrast_factor(d, 1e-6) == pytest.approx(
            1.0, abs=1e-9
        )
        assert partial_volume_contrast_factor(d, 10.0) == pytest.approx(
            2.0 * d / 30.0
        )

    def test_thick_slices_dilute_the_task(self):
        f = np.linspace(0.0, 0.5, 10)
        thin = nodule_task_spectrum(f, 4.0, 500.0, 0.5)
        thick = nodule_task_spectrum(f, 4.0, 500.0, 5.0)
        assert np.all(np.abs(thick) < np.abs(thin))


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

    def test_radial_measure_adds_the_two_dimensional_jacobian(self):
        f = np.linspace(0.0, 1.0, 2001)
        s = np.exp(-f)
        n = np.ones_like(f)
        flat = npwe_dprime_squared(f, s, n)
        radial = npwe_dprime_squared(f, s, n, radial=True)
        assert radial != pytest.approx(flat)
        assert radial > 0


class TestIdealObserver:
    def test_matches_the_detectability_integral(self):
        f = np.linspace(0.01, 1.0, 501)
        s, h, n = np.exp(-f), np.exp(-0.5 * f), 1.0 + f
        expected = dprime_squared(f, s, h, np.ones_like(f), n, radial=True)
        assert ideal_dprime_squared(f, s, n, transfer=h, radial=True) == (
            pytest.approx(expected, rel=1e-12)
        )


class TestChannels:
    def test_shape_and_bandpass_form(self):
        f = np.linspace(0.0, 1.0, 100)
        c = dog_channels(f, sigma0=0.05, n_channels=6)
        assert c.shape == (6, f.size)
        assert np.allclose(c[:, 0], 0.0)   # difference of Gaussians kills DC
        assert np.all(c >= -1e-12)

    def test_channel_peaks_increase_with_index(self):
        f = np.linspace(0.0, 2.0, 4000)
        c = dog_channels(f, sigma0=0.05, n_channels=5)
        peaks = f[np.argmax(c, axis=1)]
        assert np.all(np.diff(peaks) > 0)

    def test_spanning_set_tops_out_at_the_band_edge(self):
        f = np.linspace(0.0, 2.0, 8000)
        c = dog_channels_spanning(f, f_max=1.28, n_channels=8)
        assert f[np.argmax(c[-1])] == pytest.approx(1.28, rel=0.01)

    def test_peak_factor_matches_the_numerical_maximum(self):
        f = np.linspace(0.0, 5.0, 200000)
        c = dog_channels(f, sigma0=1.0, n_channels=1, q=1.67)
        assert f[np.argmax(c[0])] == pytest.approx(
            dog_channel_peak_factor(1.67), rel=1e-3
        )

    def test_spanning_set_covers_a_requested_band(self):
        f = np.linspace(0.0, 2.0, 8000)
        c = dog_channels_spanning(f, f_max=1.28, n_channels=8, f_min=0.04)
        peaks = f[np.argmax(c, axis=1)]
        assert peaks[0] == pytest.approx(0.04, rel=0.05)
        assert peaks[-1] == pytest.approx(1.28, rel=0.01)
        assert np.all(np.diff(peaks) > 0)

    def test_guards(self):
        f = np.linspace(0.0, 1.0, 10)
        with pytest.raises(ValueError):
            dog_channels(f, sigma0=0.0)
        with pytest.raises(ValueError):
            dog_channels(f, sigma0=0.1, alpha=1.0)
        with pytest.raises(ValueError):
            dog_channels_spanning(f, f_max=1.0, f_min=2.0)


class TestCHO:
    def _spectra(self):
        f = np.linspace(0.01, 1.28, 1001)
        signal = disk_spectrum(f, 6.0, 500.0)
        noise = 1.0 + 40.0 * f
        return f, signal, noise

    def test_prewhitening_channel_recovers_the_ideal_observer(self):
        # a single channel equal to S/N is the prewhitening template, for
        # which t^T K^-1 t collapses exactly onto Int S^2/N
        f, s, n = self._spectra()
        ideal = ideal_dprime_squared(f, s, n, radial=True)
        cho = cho_dprime_squared(f, s, n, (s / n)[None, :], radial=True)
        assert cho == pytest.approx(ideal, rel=1e-9)

    def test_never_beats_the_ideal_observer(self):
        f, s, n = self._spectra()
        ideal = ideal_dprime_squared(f, s, n, radial=True)
        channels = dog_channels_spanning(f, 1.28, n_channels=10)
        assert cho_dprime_squared(f, s, n, channels, radial=True) <= ideal * (
            1.0 + 1e-9
        )

    def test_more_channels_never_hurt(self):
        f, s, n = self._spectra()
        channels = dog_channels_spanning(f, 1.28, n_channels=10)
        fewer = cho_dprime_squared(f, s, n, channels[:5], radial=True)
        more = cho_dprime_squared(f, s, n, channels[:8], radial=True)
        assert more >= fewer * (1.0 - 1e-9)

    def test_channel_noise_lowers_performance(self):
        f, s, n = self._spectra()
        channels = dog_channels_spanning(f, 1.28, n_channels=8)
        clean = cho_dprime_squared(f, s, n, channels, radial=True)
        noisy = cho_dprime_squared(
            f, s, n, channels, channel_noise_fraction=0.5, radial=True
        )
        assert noisy < clean

    def test_channels_must_cover_the_task_band(self):
        # a channel set starting above the task's main lobe misses the signal
        # and inverts the size ordering; spanning the band down to a quarter of
        # the first zero restores it
        f = np.linspace(0.01, 1.28, 1001)
        noise = 1.0 + 40.0 * f
        scores = {}
        for diameter in (4.0, 8.0):
            signal = disk_spectrum(f, diameter, 500.0)
            first_zero = 1.2197 / diameter
            scores[diameter] = {
                "matched": cho_dprime_squared(
                    f, signal, noise,
                    dog_channels_spanning(
                        f, 1.28, 6, f_min=0.25 * first_zero
                    ),
                    radial=True,
                ),
                "high_only": cho_dprime_squared(
                    f, signal, noise,
                    dog_channels_spanning(f, 1.28, 6),
                    radial=True,
                ),
            }
        assert scores[8.0]["matched"] > scores[4.0]["matched"]
        assert scores[8.0]["high_only"] < scores[4.0]["high_only"]

    def test_visual_filter_only_binds_a_channelized_observer(self):
        # filtering signal and noise alike cannot change a prewhitening
        # observer, but it does change a CHO, which is why the CSF has to be
        # passed to the CHO explicitly
        f, s, n = self._spectra()
        visual = np.exp(-f / 0.4)
        channels = dog_channels_spanning(f, 1.28, 8, f_min=0.05)
        assert ideal_dprime_squared(
            f, s * visual, n * visual**2, radial=True
        ) == pytest.approx(ideal_dprime_squared(f, s, n, radial=True), rel=1e-9)
        filtered = cho_dprime_squared(
            f, s, n, channels, visual_filter=visual, radial=True
        )
        assert filtered != pytest.approx(
            cho_dprime_squared(f, s, n, channels, radial=True), rel=1e-6
        )

    def test_transfer_function_is_applied_to_the_signal(self):
        f, s, n = self._spectra()
        channels = dog_channels_spanning(f, 1.28, n_channels=6)
        blurred = cho_dprime_squared(
            f, s, n, channels, transfer=np.exp(-f), radial=True
        )
        assert blurred < cho_dprime_squared(f, s, n, channels, radial=True)

    def test_guards(self):
        f, s, n = self._spectra()
        with pytest.raises(ValueError):
            cho_dprime_squared(f, s, n, np.ones((3, 7)))
        with pytest.raises(ValueError):
            cho_dprime_squared(f, s, -n, np.ones((1, f.size)))
