"""Section 3.4.3 / Table 3.3 — structure filtering and served-status tagging."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kajiado_lceo.preprocessing.electrification_status import tag_served_buildings
from kajiado_lceo.preprocessing.footprint_filter import (
    compactness,
    filter_footprints,
    filter_summary,
)


def test_compactness_of_a_circle_is_one():
    radius = 10.0
    area = np.pi * radius**2
    perimeter = 2 * np.pi * radius
    assert compactness(np.array([area]), np.array([perimeter]))[0] == pytest.approx(1.0)


def test_compactness_of_a_square_is_pi_over_four():
    assert compactness(np.array([100.0]), np.array([40.0]))[0] == pytest.approx(np.pi / 4)


def test_elongated_shapes_are_less_compact_than_squares():
    square = compactness(np.array([100.0]), np.array([40.0]))[0]
    sliver = compactness(np.array([100.0]), np.array([202.0]))[0]
    assert sliver < square


def test_zero_perimeter_gives_nan_not_a_division_error():
    assert np.isnan(compactness(np.array([50.0]), np.array([0.0]))[0])


def test_small_structures_are_excluded_as_non_residential(config):
    df = pd.DataFrame(
        {
            "building_id": ["a", "b"],
            "latitude": [-2.0, -2.5],
            "longitude": [37.0, 37.5],
            "area_m2": [3.0, 45.0],  # 3 m2 is below any habitable threshold
            "perimeter_m": [7.0, 27.0],
        }
    )
    out = filter_footprints(df, config)
    assert not out.loc[0, "is_dwelling"]
    assert out.loc[1, "is_dwelling"]


def test_compound_logic_keeps_only_the_largest_structures(config):
    # Six structures inside one compound; at most max_dwellings survive.
    max_dwellings = int(config.get("footprint_filter.compound.max_dwellings"))
    df = pd.DataFrame(
        {
            "building_id": [f"s{i}" for i in range(6)],
            "latitude": [-2.0 + i * 1e-5 for i in range(6)],
            "longitude": [37.0] * 6,
            "area_m2": [80.0, 70.0, 60.0, 50.0, 40.0, 30.0],
            "perimeter_m": [36.0, 34.0, 31.0, 28.0, 25.0, 22.0],
        }
    )
    out = filter_footprints(df, config)
    assert int(out["is_dwelling"].sum()) == max_dwellings
    # The retained ones are the largest.
    assert set(out.loc[out["is_dwelling"], "area_m2"]) == {80.0, 70.0, 60.0}


def test_filter_never_drops_rows(config, sample_layers):
    out = filter_footprints(sample_layers["buildings"], config)
    assert len(out) == len(sample_layers["buildings"])
    assert {"is_dwelling", "is_ancillary", "households"} <= set(out.columns)


def test_filter_removes_a_material_share_of_synthetic_ancillaries(config, sample_layers):
    out = filter_footprints(sample_layers["buildings"], config)
    truth = sample_layers["buildings"]["structure_kind"]
    # Stores are small and must be filtered; the check is on the dominant signal,
    # not on perfect classification — the heuristic is explicitly not a classifier.
    store_retention = out.loc[truth == "store", "is_dwelling"].mean()
    dwelling_retention = out.loc[truth == "dwelling", "is_dwelling"].mean()
    assert store_retention < 0.10
    assert dwelling_retention > 0.50


def test_filter_summary_reports_every_criterion(config, sample_layers):
    report = filter_summary(filter_footprints(sample_layers["buildings"], config))
    assert set(report["criterion"]) == {
        "footprints_in",
        "failed_area",
        "failed_compactness",
        "failed_roof_signature",
        "flagged_ancillary",
        "dwellings_out",
    }


def test_missing_required_column_raises(config):
    with pytest.raises(ValueError, match="missing required columns"):
        filter_footprints(pd.DataFrame({"building_id": ["a"]}), config)


def test_building_near_lv_line_is_treated_as_served(config):
    buildings = pd.DataFrame(
        {
            "building_id": ["near", "far"],
            "latitude": [-1.8600, -2.9000],
            "longitude": [36.7800, 37.4000],
            "households": [1.0, 1.0],
        }
    )
    lv_lines = np.array([[-1.8600, 36.7700, -1.8600, 36.7900]])
    out = tag_served_buildings(buildings, lv_lines=lv_lines, config=config)
    assert out.loc[0, "is_served"]
    assert not out.loc[1, "is_served"]


def test_require_meter_evidence_ignores_proximity(config):
    strict = config.with_override_path("electrification_status.require_meter_evidence", True)
    buildings = pd.DataFrame(
        {"building_id": ["near"], "latitude": [-1.86], "longitude": [36.78], "households": [1.0]}
    )
    lv_lines = np.array([[-1.86, 36.77, -1.86, 36.79]])
    out = tag_served_buildings(buildings, lv_lines=lv_lines, config=strict)
    assert not out.loc[0, "is_served"], "without a meter, proximity alone must not count"


def test_transformer_without_spare_capacity_does_not_confer_service(config):
    buildings = pd.DataFrame(
        {"building_id": ["b"], "latitude": [-2.12], "longitude": [36.91], "households": [1.0]}
    )
    transformers = pd.DataFrame(
        {"latitude": [-2.12], "longitude": [36.91], "spare_capacity_kva": [0.0]}
    )
    out = tag_served_buildings(buildings, transformers=transformers, config=config)
    assert not out.loc[0, "is_served"]
