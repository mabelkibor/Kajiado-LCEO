"""Shared fixtures."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kajiado_lceo.config import load_config
from kajiado_lceo.sample import generate_sample_county


@pytest.fixture(scope="session")
def config():
    """The baseline configuration as shipped in ``config/``."""
    return load_config("config", scenario="baseline")


@pytest.fixture(scope="session")
def sample_layers():
    """A small synthetic county, generated once per session."""
    return generate_sample_county(seed=7)


@pytest.fixture
def toy_settlements():
    """Three settlements spanning the cases Equation 10 must separate.

    A large village on the network, a mid-size village far from it, and an
    isolated homestead — the grid, mini-grid and standalone cases respectively.
    """
    return pd.DataFrame(
        {
            "settlement_id": ["C000001", "C000002", "D000003"],
            "households": [150.0, 60.0, 1.0],
            "n_buildings": [150, 60, 1],
            "latitude": [-1.85, -2.60, -2.90],
            "longitude": [36.78, 37.10, 37.40],
            "area_km2": [0.30, 0.12, 0.01],
            "density_bldg_per_km2": [500.0, 500.0, 100.0],
            "distance_to_mv_km": [0.8, 45.0, 60.0],
            "distance_to_lv_km": [1.2, 46.0, 61.0],
            "is_dispersed": [False, False, True],
            "is_micro_cluster": [False, False, False],
            "nearest_transformer_spare_kva": [0.0, 0.0, 0.0],
            "terrain_class": ["flat", "flat", "flat"],
        }
    )


@pytest.fixture
def toy_buildings():
    """A tight cluster, a loose pair, and one isolated point, with ancillaries."""
    rng = np.random.default_rng(3)
    rows = []
    # Tight cluster: 12 dwellings within ~40 m of one another.
    for i in range(12):
        rows.append(
            {
                "building_id": f"B{i:04d}",
                "latitude": -1.8500 + rng.normal(0, 0.00018),
                "longitude": 36.7800 + rng.normal(0, 0.00018),
                "area_m2": 48.0,
                "perimeter_m": 28.0,
            }
        )
    # A loose pair ~350 m apart: noise at eps=75 m, a micro-cluster at eps=400 m.
    rows.append(
        {
            "building_id": "B1000",
            "latitude": -2.5000,
            "longitude": 37.0000,
            "area_m2": 40.0,
            "perimeter_m": 26.0,
        }
    )
    rows.append(
        {
            "building_id": "B1001",
            "latitude": -2.5031,
            "longitude": 37.0000,
            "area_m2": 40.0,
            "perimeter_m": 26.0,
        }
    )
    # A genuinely isolated homestead.
    rows.append(
        {
            "building_id": "B2000",
            "latitude": -2.9000,
            "longitude": 37.4000,
            "area_m2": 35.0,
            "perimeter_m": 25.0,
        }
    )
    return pd.DataFrame(rows)
