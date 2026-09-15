"""Equation 1 — great-circle distance."""

from __future__ import annotations

import numpy as np
import pytest

from kajiado_lceo.geo.distance import (
    EARTH_RADIUS_KM,
    densify_lines,
    haversine_km,
    nearest_line_distance_km,
    nearest_point_distance_km,
)


def test_distance_to_self_is_zero():
    assert haversine_km(-1.85, 36.78, -1.85, 36.78) == pytest.approx(0.0, abs=1e-9)


def test_one_degree_of_latitude_is_about_111_km():
    # A degree of latitude is R * pi/180 regardless of longitude.
    expected = EARTH_RADIUS_KM * np.pi / 180.0
    assert haversine_km(0.0, 36.0, 1.0, 36.0) == pytest.approx(expected, rel=1e-9)


def test_longitude_degrees_shrink_with_latitude():
    at_equator = haversine_km(0.0, 36.0, 0.0, 37.0)
    at_kajiado = haversine_km(-2.0, 36.0, -2.0, 37.0)
    assert at_kajiado < at_equator
    assert at_kajiado == pytest.approx(at_equator * np.cos(np.radians(2.0)), rel=1e-6)


def test_distance_is_symmetric():
    forward = haversine_km(-1.29, 36.82, -1.85, 36.78)
    backward = haversine_km(-1.85, 36.78, -1.29, 36.82)
    assert forward == pytest.approx(backward, rel=1e-12)


def test_known_separation_nairobi_to_kajiado_town():
    # Roughly 62 km; a coarse check that the formula is not out by a factor.
    distance = haversine_km(-1.2921, 36.8219, -1.8521, 36.7769)
    assert 60.0 < distance < 65.0


def test_broadcasting_gives_one_to_many_distances():
    distances = haversine_km(-1.85, 36.78, np.array([-1.85, -1.95, -2.05]), 36.78)
    assert distances.shape == (3,)
    assert distances[0] == pytest.approx(0.0, abs=1e-9)
    assert distances[1] < distances[2]


def test_nearest_point_picks_the_closest_target():
    points = np.array([[-1.85, 36.78]])
    targets = np.array([[-2.50, 37.00], [-1.86, 36.79], [-1.00, 36.00]])
    distance, index = nearest_point_distance_km(points, targets)
    assert index[0] == 1
    assert distance[0] < 2.0


def test_no_targets_yields_infinite_distance():
    # Read downstream as "grid is not a candidate", never as distance zero.
    distance, index = nearest_point_distance_km(np.array([[-1.85, 36.78]]), np.empty((0, 2)))
    assert np.isinf(distance[0])
    assert index[0] == -1


def test_chunking_does_not_change_the_answer():
    rng = np.random.default_rng(0)
    points = rng.uniform([-3.0, 36.2], [-1.4, 37.8], size=(500, 2))
    targets = rng.uniform([-3.0, 36.2], [-1.4, 37.8], size=(40, 2))
    small, _ = nearest_point_distance_km(points, targets, chunk_size=7)
    large, _ = nearest_point_distance_km(points, targets, chunk_size=10_000)
    np.testing.assert_allclose(small, large)


def test_densify_samples_a_line_at_the_requested_spacing():
    line = np.array([[-1.80, 36.70, -1.90, 36.70]])  # ~11 km due south
    cloud = densify_lines(line, spacing_km=1.0)
    assert len(cloud) >= 11


def test_point_on_a_line_has_near_zero_distance():
    line = np.array([[-1.80, 36.70, -1.90, 36.70]])
    midpoint = np.array([[-1.85, 36.70]])
    assert nearest_line_distance_km(midpoint, line, spacing_km=0.05)[0] < 0.05
