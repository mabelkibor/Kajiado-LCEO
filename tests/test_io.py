"""Input loading and output writing."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from kajiado_lceo.io.loaders import load_building_footprints, load_line_layer, load_point_layer
from kajiado_lceo.io.writers import write_run_summary, write_table
from kajiado_lceo.sample import write_sample_data


def test_sample_data_round_trips_through_csv(tmp_path, config):
    paths = write_sample_data(tmp_path, seed=3)
    footprints = load_building_footprints(paths["building_footprints"], config)
    assert len(footprints) > 0
    assert {"building_id", "latitude", "longitude", "area_m2"} <= set(footprints.columns)


def test_line_layer_loads_from_csv(tmp_path):
    path = tmp_path / "mv.csv"
    pd.DataFrame({"lat1": [-1.8], "lon1": [36.7], "lat2": [-1.9], "lon2": [36.8]}).to_csv(
        path, index=False
    )
    assert load_line_layer(path).shape == (1, 4)


def test_line_layer_loads_from_geojson(tmp_path):
    path = tmp_path / "mv.geojson"
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[36.70, -1.80], [36.80, -1.90], [36.90, -1.95]],
                },
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    segments = load_line_layer(path)
    assert segments.shape == (2, 4), "a three-vertex line explodes into two segments"
    # GeoJSON is (lon, lat); the loader must return (lat, lon).
    assert segments[0][0] == pytest.approx(-1.80)
    assert segments[0][1] == pytest.approx(36.70)


def test_missing_line_layer_is_treated_as_absent(tmp_path):
    assert load_line_layer(tmp_path / "nope.csv").shape == (0, 4)


def test_missing_point_layer_returns_an_empty_frame(tmp_path):
    assert load_point_layer(tmp_path / "nope.csv").empty


def test_footprints_without_area_are_rejected(tmp_path, config):
    path = tmp_path / "b.csv"
    pd.DataFrame({"latitude": [-2.0], "longitude": [37.0]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="area_m2"):
        load_building_footprints(path, config)


def test_building_ids_are_generated_when_absent(tmp_path, config):
    path = tmp_path / "b.csv"
    pd.DataFrame({"latitude": [-2.0], "longitude": [37.0], "area_m2": [40.0]}).to_csv(
        path, index=False
    )
    assert "building_id" in load_building_footprints(path, config).columns


def test_write_table_creates_parent_directories(tmp_path):
    path = write_table(pd.DataFrame({"a": [1, 2]}), tmp_path / "deep" / "nested" / "t.csv")
    assert path.is_file()
    assert len(pd.read_csv(path)) == 2


def test_run_summary_is_valid_json(tmp_path):
    path = write_run_summary(
        {"totals": {"settlements": 3}, "x": np.float64(1.5)}, tmp_path / "s.json"
    )
    with path.open(encoding="utf-8") as handle:
        assert json.load(handle)["totals"]["settlements"] == 3
