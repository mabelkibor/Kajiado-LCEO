"""Loading the spatial input layers of Table 3.2.

The model core operates on plain tabular data — coordinates and attributes —
rather than on geometry objects, so that the numerical pipeline runs without a
GIS stack installed. CSV and GeoJSON are read natively; where GeoPackage,
Shapefile or other vector formats are supplied, ``geopandas`` is imported
lazily, so it is an optional rather than a required dependency.

Expected columns are documented in docs/DATA_DICTIONARY.md.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from kajiado_lceo.config import Config
from kajiado_lceo.logging_setup import get_logger

logger = get_logger(__name__)

VECTOR_SUFFIXES = {".gpkg", ".shp", ".geojson", ".json", ".parquet", ".fgb"}


def _read_table(path: Path) -> pd.DataFrame:
    """Read a tabular or vector file into a DataFrame."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in VECTOR_SUFFIXES:
        try:
            import geopandas as gpd
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ImportError(
                f"reading {path.name} requires geopandas; install the 'gis' extra "
                "(pip install -e '.[gis]') or export the layer to CSV"
            ) from exc
        return gpd.read_file(path)
    raise ValueError(f"unsupported input format: {path.suffix} ({path})")


def _ensure_columns(df: pd.DataFrame, columns: tuple[str, ...], path: Path) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(
            f"{path.name} is missing required column(s) {missing}; "
            "see docs/DATA_DICTIONARY.md for the expected schema"
        )


def _centroids_from_geometry(df: pd.DataFrame) -> pd.DataFrame:
    """Derive latitude/longitude columns from a geometry column, if present."""
    if "geometry" not in df.columns or {"latitude", "longitude"} <= set(df.columns):
        return df
    try:
        import geopandas as gpd
    except ImportError:  # pragma: no cover
        return df
    if not isinstance(df, gpd.GeoDataFrame):
        return df
    geographic = df.to_crs("EPSG:4326")
    centroids = geographic.geometry.centroid
    out = pd.DataFrame(df.drop(columns="geometry"))
    out["latitude"] = centroids.y.to_numpy()
    out["longitude"] = centroids.x.to_numpy()
    return out


def load_building_footprints(path: str | Path, config: Config) -> pd.DataFrame:
    """Load building footprints, deriving centroids and areas where needed."""
    path = Path(path)
    df = _centroids_from_geometry(_read_table(path))
    _ensure_columns(df, ("latitude", "longitude"), path)

    if "building_id" not in df.columns:
        df = df.assign(building_id=[f"B{i:08d}" for i in range(len(df))])
    if "area_m2" not in df.columns:
        raise ValueError(
            f"{path.name} must carry an 'area_m2' column: footprint area drives the "
            "Table 3.3 structure filter"
        )
    logger.info("loaded %d building footprints from %s", len(df), path.name)
    return df


def load_line_layer(path: str | Path) -> np.ndarray:
    """Load a network layer as an ``(m, 4)`` array of ``(lat1, lon1, lat2, lon2)``.

    Accepts either a CSV already in segment form or a GeoJSON LineString /
    MultiLineString collection, which is exploded into its constituent segments.
    """
    path = Path(path)
    if not path.is_file():
        logger.warning("network layer not found: %s (treated as absent)", path)
        return np.empty((0, 4))

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        _ensure_columns(df, ("lat1", "lon1", "lat2", "lon2"), path)
        return df[["lat1", "lon1", "lat2", "lon2"]].to_numpy(dtype=float)

    if path.suffix.lower() in {".geojson", ".json"}:
        with path.open("r", encoding="utf-8") as handle:
            payload: dict[str, Any] = json.load(handle)
        return _segments_from_geojson(payload)

    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            f"reading {path.name} requires geopandas; install the 'gis' extra"
        ) from exc
    frame = gpd.read_file(path).to_crs("EPSG:4326")
    return _segments_from_geojson(json.loads(frame.to_json()))


def _segments_from_geojson(payload: dict[str, Any]) -> np.ndarray:
    """Explode a GeoJSON line collection into (lat1, lon1, lat2, lon2) rows."""
    segments: list[tuple[float, float, float, float]] = []

    def add_line(coordinates: list[list[float]]) -> None:
        for (lon1, lat1), (lon2, lat2) in itertools.pairwise(coordinates):
            segments.append((lat1, lon1, lat2, lon2))

    for feature in payload.get("features", []):
        geometry = feature.get("geometry") or {}
        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates") or []
        if geom_type == "LineString":
            add_line(coordinates)
        elif geom_type == "MultiLineString":
            for line in coordinates:
                add_line(line)
    return np.array(segments, dtype=float) if segments else np.empty((0, 4))


def load_point_layer(
    path: str | Path, required: tuple[str, ...] = ("latitude", "longitude")
) -> pd.DataFrame:
    """Load a point layer (transformers, meters); empty frame if absent."""
    path = Path(path)
    if not path.is_file():
        logger.warning("point layer not found: %s (treated as absent)", path)
        return pd.DataFrame(columns=list(required))
    df = _centroids_from_geometry(_read_table(path))
    _ensure_columns(df, required, path)
    return df


def load_inputs(config: Config) -> dict[str, Any]:
    """Load every input layer declared under ``inputs`` in the configuration.

    Missing optional layers degrade gracefully unless ``run.strict_inputs`` is
    set, in which case a missing layer raises. Building footprints are always
    required — without them there is no model.
    """
    strict = bool(config.get("run.strict_inputs", False))
    footprints_path = config.input_path("building_footprints")
    if not footprints_path.is_file():
        raise FileNotFoundError(
            f"building footprints not found at {footprints_path}. "
            "Run `lceo sample-data` to generate a synthetic county for testing, "
            "or place the real layer at the configured path."
        )

    layers: dict[str, Any] = {
        "buildings": load_building_footprints(footprints_path, config),
        "mv_lines": load_line_layer(config.input_path("mv_lines")),
        "lv_lines": load_line_layer(config.input_path("lv_lines")),
        "transformers": load_point_layer(config.input_path("transformers")),
        "meters": load_point_layer(config.input_path("meters")),
    }

    if strict:
        empty = [name for name, layer in layers.items() if len(layer) == 0]
        if empty:
            raise FileNotFoundError(f"run.strict_inputs is set and these layers are empty: {empty}")
    return layers
