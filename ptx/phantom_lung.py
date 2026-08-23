"""Deterministic lung phantom and the nodule task function (section 6).

Everything here is seeded and byte-reproducible (design principle no. 1):

- ``power_law_texture``      isotropic 1/f^beta field in pixel units
- ``lung_texture_hu``        HU-calibrated, anisotropic parenchyma texture
- ``vessel_tree_segments``   bifurcating vessel tree (Murray's law radii)
- ``rasterize_vessels``      partial-volume rasterisation of the tree
- ``insert_spherical_nodule`` sphere with a partial-volume edge
- ``nodule_task_spectrum``   analytic W_task(f) of the detection task

The task function is analytic rather than measured from the raster so that the
frequency-domain detectability integral stays independent of the phantom grid;
``tests/`` cross-checks the two against each other.
"""

from __future__ import annotations

import dataclasses

import numpy as np
from scipy.special import j1, jn_zeros

__all__ = [
    "power_law_texture",
    "lung_texture_hu",
    "insert_gaussian_nodule",
    "insert_spherical_nodule",
    "VesselSegment",
    "vessel_tree_segments",
    "vessel_weight_map",
    "rasterize_vessels",
    "disk_spectrum",
    "disk_first_zero_lpmm",
    "partial_volume_contrast_factor",
    "nodule_task_spectrum",
]

# First zero of 2 J1(x)/x divided by pi: the disk spectrum vanishes at
# f = DISK_FIRST_ZERO_FACTOR / diameter.
DISK_FIRST_ZERO_FACTOR = float(jn_zeros(1, 1)[0] / np.pi)

# Representative attenuation values for normal lung at soft-tissue window
# settings; used as defaults only, every caller may override them.
LUNG_PARENCHYMA_HU = -850.0
LUNG_TEXTURE_SD_HU = 40.0
VESSEL_HU = 50.0


def _as_voxel_vector(voxel_mm, ndim):
    v = np.atleast_1d(np.asarray(voxel_mm, dtype=float))
    if v.size == 1:
        v = np.repeat(v, ndim)
    if v.size != ndim or np.any(v <= 0):
        raise ValueError("voxel_mm must be positive, scalar or per-axis")
    return v


def power_law_texture(shape, beta, seed, mean=0.0, sd=1.0):
    """Deterministic 2-D/3-D random field with power spectrum ~ 1/f^beta."""
    if beta < 0:
        raise ValueError("beta must be non-negative")
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(shape)
    spec = np.fft.fftn(white)
    grids = np.meshgrid(
        *[np.fft.fftfreq(n) for n in shape], indexing="ij"
    )
    f = np.sqrt(sum(g**2 for g in grids))
    f[tuple(0 for _ in shape)] = np.inf  # kill DC scaling
    amp = f ** (-beta / 2.0)
    amp[~np.isfinite(amp)] = 0.0
    field = np.real(np.fft.ifftn(spec * amp))
    field -= field.mean()
    s = field.std()
    if s > 0:
        field *= sd / s
    return field + mean


def lung_texture_hu(
    shape,
    voxel_mm,
    seed,
    beta=3.0,
    mean_hu=LUNG_PARENCHYMA_HU,
    sd_hu=LUNG_TEXTURE_SD_HU,
    anisotropy=None,
):
    """HU-calibrated parenchyma texture on a physical voxel grid.

    The power law is evaluated on *physical* frequency (cycles/mm), so the
    texture is resolution-independent: halving the voxel size refines the
    sampling without changing the underlying field statistics.

    ``anisotropy`` multiplies the frequency of each axis; a value above 1
    stretches structures along that axis, which is how the through-plane
    smoothing of thick slices is represented.
    """
    if beta < 0:
        raise ValueError("beta must be non-negative")
    if sd_hu < 0:
        raise ValueError("sd_hu must be non-negative")
    shape = tuple(int(n) for n in shape)
    v = _as_voxel_vector(voxel_mm, len(shape))
    a = (
        np.ones(len(shape))
        if anisotropy is None
        else _as_voxel_vector(anisotropy, len(shape))
    )

    rng = np.random.default_rng(seed)
    white = rng.standard_normal(shape)
    grids = np.meshgrid(
        *[np.fft.fftfreq(n, d=vi) * ai for n, vi, ai in zip(shape, v, a)],
        indexing="ij",
    )
    f = np.sqrt(sum(g**2 for g in grids))
    f[tuple(0 for _ in shape)] = np.inf
    amp = f ** (-beta / 2.0)
    amp[~np.isfinite(amp)] = 0.0
    field = np.real(np.fft.ifftn(np.fft.fftn(white) * amp))
    field -= field.mean()
    s = field.std()
    if s > 0:
        field *= sd_hu / s
    return field + mean_hu


def insert_gaussian_nodule(volume, center, diameter_px, contrast):
    """Add a Gaussian blob nodule (FWHM = diameter) in place-safe copy."""
    vol = np.array(volume, dtype=float, copy=True)
    sigma = diameter_px / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    grids = np.meshgrid(
        *[np.arange(n, dtype=float) for n in vol.shape], indexing="ij"
    )
    r2 = sum((g - c) ** 2 for g, c in zip(grids, center))
    vol += contrast * np.exp(-r2 / (2.0 * sigma**2))
    return vol


def insert_spherical_nodule(
    volume, center_mm, diameter_mm, contrast_hu, voxel_mm
):
    """Add a uniform sphere with a one-voxel partial-volume edge.

    The edge ramp makes the raster a fair sample of the analytic disk/sphere
    that ``nodule_task_spectrum`` describes, instead of a hard-thresholded
    staircase whose spectrum carries aliasing.
    """
    if diameter_mm <= 0:
        raise ValueError("diameter must be positive")
    vol = np.array(volume, dtype=float, copy=True)
    v = _as_voxel_vector(voxel_mm, vol.ndim)
    center = np.atleast_1d(np.asarray(center_mm, dtype=float))
    if center.size != vol.ndim:
        raise ValueError("center_mm must have one entry per axis")
    grids = np.meshgrid(
        *[np.arange(n, dtype=float) * vi for n, vi in zip(vol.shape, v)],
        indexing="ij",
    )
    dist = np.sqrt(sum((g - c) ** 2 for g, c in zip(grids, center)))
    edge = float(np.min(v))
    weight = np.clip((diameter_mm / 2.0 - dist) / edge + 0.5, 0.0, 1.0)
    return vol + contrast_hu * weight


# --------------------------------------------------------------------------
# Vessel tree
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class VesselSegment:
    """One straight vessel piece, coordinates in mm."""

    start_mm: tuple
    end_mm: tuple
    radius_mm: float
    generation: int


def vessel_tree_segments(
    origin_mm,
    direction,
    length_mm,
    radius_mm,
    generations,
    seed,
    branch_angle_deg=35.0,
    length_ratio=0.75,
    murray_exponent=3.0,
):
    """Deterministic bifurcating vessel tree.

    Daughter radii follow Murray's law: for a symmetric bifurcation
    ``r_parent^n = 2 r_child^n``, hence ``r_child = r_parent 2^(-1/n)`` with
    ``n = 3`` for laminar flow. Branch directions rotate by
    ``+/- branch_angle`` inside a seeded random plane, which keeps the tree
    reproducible while avoiding a single preferred orientation.

    Returns ``2^generations - 1`` segments (the trunk is generation 0).
    """
    if generations < 1:
        raise ValueError("need at least one generation")
    if radius_mm <= 0 or length_mm <= 0:
        raise ValueError("radius and length must be positive")
    if not 0.0 < length_ratio <= 1.0:
        raise ValueError("length_ratio must be in (0, 1]")
    if murray_exponent <= 0:
        raise ValueError("murray_exponent must be positive")

    rng = np.random.default_rng(seed)
    origin = np.atleast_1d(np.asarray(origin_mm, dtype=float))
    d0 = np.atleast_1d(np.asarray(direction, dtype=float))
    if d0.shape != origin.shape:
        raise ValueError("origin_mm and direction must share dimensionality")
    norm = np.linalg.norm(d0)
    if norm == 0:
        raise ValueError("direction must be non-zero")
    d0 = d0 / norm
    ratio = 2.0 ** (-1.0 / murray_exponent)
    theta = np.deg2rad(branch_angle_deg)

    segments = []
    frontier = [(origin, d0, float(length_mm), float(radius_mm), 0)]
    while frontier:
        start, direct, length, radius, gen = frontier.pop(0)
        end = start + direct * length
        segments.append(
            VesselSegment(
                start_mm=tuple(float(x) for x in start),
                end_mm=tuple(float(x) for x in end),
                radius_mm=radius,
                generation=gen,
            )
        )
        if gen + 1 >= generations:
            continue
        perp = _random_perpendicular(direct, rng)
        for sign in (1.0, -1.0):
            child = np.cos(theta) * direct + sign * np.sin(theta) * perp
            child = child / np.linalg.norm(child)
            frontier.append(
                (end, child, length * length_ratio, radius * ratio, gen + 1)
            )
    return segments


def _random_perpendicular(direction, rng):
    """Unit vector orthogonal to ``direction``, drawn from ``rng``."""
    for _ in range(16):
        candidate = rng.standard_normal(direction.size)
        candidate -= direction * (candidate @ direction)
        norm = np.linalg.norm(candidate)
        if norm > 1e-8:
            return candidate / norm
    raise RuntimeError("failed to draw a perpendicular direction")


def vessel_weight_map(shape, segments, voxel_mm):
    """Partial-volume occupancy in [0, 1] of the vessel tree on a raster."""
    shape = tuple(int(n) for n in shape)
    v = _as_voxel_vector(voxel_mm, len(shape))
    weight = np.zeros(shape, dtype=float)
    edge = float(np.min(v))
    for seg in segments:
        a = np.asarray(seg.start_mm, dtype=float)
        b = np.asarray(seg.end_mm, dtype=float)
        if a.size != len(shape):
            raise ValueError("segment dimensionality does not match shape")
        pad = seg.radius_mm + edge
        lo = np.maximum(np.floor((np.minimum(a, b) - pad) / v), 0).astype(int)
        hi = np.minimum(
            np.ceil((np.maximum(a, b) + pad) / v).astype(int) + 1, shape
        )
        if np.any(lo >= hi):
            continue
        axes = [
            np.arange(l, h, dtype=float) * vi
            for l, h, vi in zip(lo, hi, v)
        ]
        grids = np.meshgrid(*axes, indexing="ij")
        points = np.stack(grids, axis=-1)
        dist = _distance_to_segment(points, a, b)
        local = np.clip((seg.radius_mm - dist) / edge + 0.5, 0.0, 1.0)
        window = tuple(slice(l, h) for l, h in zip(lo, hi))
        weight[window] = np.maximum(weight[window], local)
    return weight


def _distance_to_segment(points, a, b):
    ab = b - a
    denom = float(ab @ ab)
    if denom == 0.0:
        return np.linalg.norm(points - a, axis=-1)
    t = np.clip(((points - a) @ ab) / denom, 0.0, 1.0)
    projection = a + t[..., None] * ab
    return np.linalg.norm(points - projection, axis=-1)


def rasterize_vessels(volume, segments, voxel_mm, hu_value=VESSEL_HU):
    """Blend a vessel tree into a volume, replacing parenchyma HU."""
    vol = np.array(volume, dtype=float, copy=True)
    weight = vessel_weight_map(vol.shape, segments, voxel_mm)
    return vol * (1.0 - weight) + hu_value * weight


# --------------------------------------------------------------------------
# Task function W_task(f) (protocol section 5.2)
# --------------------------------------------------------------------------


def disk_spectrum(f_mm, diameter_mm, contrast_hu=1.0):
    """2-D Fourier transform of a uniform disk [HU mm^2].

    ``F(f) = contrast * area * 2 J1(pi d f) / (pi d f)`` with
    ``area = pi d^2 / 4``. The first zero sits at ``f = 1.2197 / d`` (the
    first zero of J1 divided by pi), the anchor used in ``tests/``.
    """
    if diameter_mm <= 0:
        raise ValueError("diameter must be positive")
    f = np.asarray(f_mm, dtype=float)
    x = np.pi * diameter_mm * f
    area = np.pi * diameter_mm**2 / 4.0
    small = np.abs(x) < 1e-12
    x_safe = np.where(small, 1.0, x)
    envelope = np.where(small, 1.0, 2.0 * j1(x_safe) / x_safe)
    return contrast_hu * area * envelope


def disk_first_zero_lpmm(diameter_mm):
    """Frequency of the first zero of the disk spectrum [lp/mm].

    The natural bandwidth scale of the detection task: model-observer channel
    sets have to cover it, and it is where W_task stops delivering contrast.
    """
    if diameter_mm <= 0:
        raise ValueError("diameter must be positive")
    return DISK_FIRST_ZERO_FACTOR / diameter_mm


def partial_volume_contrast_factor(diameter_mm, slice_thickness_mm):
    """Contrast loss of a sphere averaged over a centred slice.

    Averaging the cross-sectional area ``pi (d^2/4 - z^2)`` of a sphere over a
    slab of thickness ``T`` and dividing by the equatorial area gives

        T <= d :  1 - T^2 / (3 d^2)
        T  > d :  2 d / (3 T)      (whole sphere spread over the slab)

    The two branches meet at ``T = d`` with the value 2/3, and the factor
    tends to 1 as ``T -> 0``.
    """
    if diameter_mm <= 0 or slice_thickness_mm <= 0:
        raise ValueError("diameter and slice thickness must be positive")
    d, t = float(diameter_mm), float(slice_thickness_mm)
    if t <= d:
        return 1.0 - t**2 / (3.0 * d**2)
    return 2.0 * d / (3.0 * t)


def nodule_task_spectrum(
    f_mm, diameter_mm, contrast_hu, slice_thickness_mm=None
):
    """W_task(f) for nodule detection: disk spectrum with partial volume.

    The task is specified by lesion size and contrast (protocol section 7).
    Passing ``slice_thickness_mm`` applies the analytic partial-volume loss of
    a sphere seen in a finite slice.
    """
    factor = (
        1.0
        if slice_thickness_mm is None
        else partial_volume_contrast_factor(diameter_mm, slice_thickness_mm)
    )
    return disk_spectrum(f_mm, diameter_mm, contrast_hu * factor)
