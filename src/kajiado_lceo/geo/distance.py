"""Equation 1 — great-circle distance, and the nearest-network queries built on it.

    d(i,j) = 2R * arcsin( sqrt( sin^2((phi_j - phi_i)/2)
                          + cos(phi_i) * cos(phi_j) * sin^2((lam_j - lam_i)/2) ) )

with R the mean Earth radius (6,371 km) and phi, lam latitude and longitude in
radians. The haversine form is used rather than a planar approximation so that
distances remain valid across the whole county without reprojection, and so the
same metric feeds both the DBSCAN neighbourhood test (Equation 2) and the
distance-to-MV term of Equation 5.
"""

from __future__ import annotations

import numpy as np

EARTH_RADIUS_KM = 6371.0


def haversine_km(
    lat1: np.ndarray | float,
    lon1: np.ndarray | float,
    lat2: np.ndarray | float,
    lon2: np.ndarray | float,
    radius_km: float = EARTH_RADIUS_KM,
) -> np.ndarray:
    """Great-circle distance in km between paired coordinates (Equation 1).

    Inputs are degrees and broadcast against one another, so this serves both
    the one-to-one and the one-to-many case.
    """
    phi1, lam1, phi2, lam2 = (
        np.radians(np.asarray(v, dtype=float)) for v in (lat1, lon1, lat2, lon2)
    )
    dphi = phi2 - phi1
    dlam = lam2 - lam1
    h = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2.0) ** 2
    # Clip guards against floating-point excursions above 1 for antipodal pairs.
    return 2.0 * radius_km * np.arcsin(np.sqrt(np.clip(h, 0.0, 1.0)))


def haversine_matrix_km(
    points_a: np.ndarray,
    points_b: np.ndarray,
    radius_km: float = EARTH_RADIUS_KM,
) -> np.ndarray:
    """Full (n_a, n_b) distance matrix between two arrays of ``(lat, lon)``.

    Memory grows as n_a * n_b; :func:`nearest_point_distance_km` chunks over the
    first axis and should be preferred for county-scale inputs.
    """
    a = np.atleast_2d(np.asarray(points_a, dtype=float))
    b = np.atleast_2d(np.asarray(points_b, dtype=float))
    return haversine_km(
        a[:, 0][:, None], a[:, 1][:, None], b[:, 0][None, :], b[:, 1][None, :], radius_km
    )


def nearest_point_distance_km(
    points: np.ndarray,
    targets: np.ndarray,
    radius_km: float = EARTH_RADIUS_KM,
    chunk_size: int = 4096,
) -> tuple[np.ndarray, np.ndarray]:
    """Distance from each point to its nearest target, and that target's index.

    Args:
        points: ``(n, 2)`` array of ``(lat, lon)`` in degrees.
        targets: ``(m, 2)`` array of ``(lat, lon)`` in degrees.
        radius_km: Earth radius used by Equation 1.
        chunk_size: rows processed per block, bounding peak memory.

    Returns:
        ``(distances_km, indices)``. With no targets, distances are ``inf`` and
        indices ``-1``, which the cost functions read as "grid not a candidate".
    """
    points = np.atleast_2d(np.asarray(points, dtype=float))
    targets = np.asarray(targets, dtype=float)
    n = points.shape[0]
    if targets.size == 0:
        return np.full(n, np.inf), np.full(n, -1, dtype=int)
    targets = np.atleast_2d(targets)

    distances = np.empty(n, dtype=float)
    indices = np.empty(n, dtype=int)
    for start in range(0, n, chunk_size):
        stop = min(start + chunk_size, n)
        block = haversine_matrix_km(points[start:stop], targets, radius_km)
        indices[start:stop] = np.argmin(block, axis=1)
        distances[start:stop] = block[np.arange(stop - start), indices[start:stop]]
    return distances, indices


def densify_lines(
    lines: np.ndarray,
    spacing_km: float = 0.1,
    radius_km: float = EARTH_RADIUS_KM,
) -> np.ndarray:
    """Convert line segments into a point cloud sampled at ``spacing_km``.

    ``lines`` is an ``(m, 4)`` array of ``(lat1, lon1, lat2, lon2)``. Sampling
    the network into points lets the same nearest-neighbour machinery answer
    "distance to the nearest MV line" (Equation 5's ``D_c``) without a planar
    projection; the approximation error is bounded by ``spacing_km / 2``.
    """
    lines = np.atleast_2d(np.asarray(lines, dtype=float))
    if lines.size == 0:
        return np.empty((0, 2))
    lengths = haversine_km(lines[:, 0], lines[:, 1], lines[:, 2], lines[:, 3], radius_km)
    samples: list[np.ndarray] = []
    for (lat1, lon1, lat2, lon2), length in zip(lines, lengths, strict=True):
        steps = max(int(np.ceil(length / max(spacing_km, 1e-6))), 1)
        t = np.linspace(0.0, 1.0, steps + 1)
        # Linear interpolation in lat/lon is adequate at sub-kilometre spacing.
        samples.append(np.column_stack([lat1 + (lat2 - lat1) * t, lon1 + (lon2 - lon1) * t]))
    return np.unique(np.vstack(samples), axis=0)


def nearest_line_distance_km(
    points: np.ndarray,
    lines: np.ndarray,
    spacing_km: float = 0.1,
    radius_km: float = EARTH_RADIUS_KM,
) -> np.ndarray:
    """Distance from each point to the nearest line in a network layer.

    The network is densified to a point cloud first (see :func:`densify_lines`),
    which keeps the query exact to within ``spacing_km / 2`` while avoiding a
    dependency on a full geometry engine for the core model.
    """
    cloud = densify_lines(lines, spacing_km=spacing_km, radius_km=radius_km)
    distances, _ = nearest_point_distance_km(points, cloud, radius_km=radius_km)
    return distances
