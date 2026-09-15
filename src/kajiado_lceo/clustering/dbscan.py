"""Equation 2 — DBSCAN settlement clustering.

    p is a core point  <=>  |{ q in D : d(p,q) <= eps }| >= MinPts

A settlement cluster is the maximal set of points density-connected under that
condition, with ``eps`` in 50-100 m and ``MinPts`` of 3-5 households — the
typical spacing of dwellings within a compound or village core.

Points failing the condition for every ``eps`` in that range are labelled noise.
Per Section 3.5.3 they are *not* discarded: they are the dispersed pastoralist
homesteads the proposal is specifically concerned with, and they are carried
forward to the decision rule of Equation 10, where the relaxed pass implemented
in :func:`micro_cluster_noise` (eps 300-500 m) gives a micro-mini-grid a chance
to beat aggregated SHS before the standalone default is applied.

``d`` is the haversine metric of Equation 1, supplied to scikit-learn as the
``haversine`` metric on radians, so cluster membership is decided by the same
distance function used everywhere else in the model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from kajiado_lceo.config import Config
from kajiado_lceo.geo.distance import EARTH_RADIUS_KM
from kajiado_lceo.logging_setup import get_logger

logger = get_logger(__name__)

NOISE_LABEL = -1


def _dbscan_labels(
    coords_deg: np.ndarray, eps_m: float, min_pts: int, earth_radius_km: float
) -> np.ndarray:
    """Run DBSCAN under the haversine metric; returns labels with -1 for noise."""
    if coords_deg.shape[0] == 0:
        return np.empty(0, dtype=int)
    eps_rad = (eps_m / 1000.0) / earth_radius_km
    model = DBSCAN(eps=eps_rad, min_samples=int(min_pts), metric="haversine", algorithm="ball_tree")
    return model.fit_predict(np.radians(coords_deg))


def cluster_buildings(
    buildings: pd.DataFrame,
    config: Config,
    eps_m: float | None = None,
    min_pts: int | None = None,
) -> pd.DataFrame:
    """Assign each unelectrified dwelling to a settlement cluster (Equation 2).

    Args:
        buildings: filtered, unelectrified dwellings with lat/lon columns.
        config: merged configuration.
        eps_m: neighbourhood radius override, in metres (sensitivity sweeps).
        min_pts: core-point threshold override.

    Returns:
        A copy with a ``cluster_label`` column; ``-1`` marks a noise point.
    """
    eps_m = float(eps_m if eps_m is not None else config.require("clustering.eps_m"))
    min_pts = int(min_pts if min_pts is not None else config.require("clustering.min_pts"))
    earth_radius_km = float(config.get("clustering.earth_radius_km", EARTH_RADIUS_KM))

    df = buildings.copy()
    coords = df[["latitude", "longitude"]].to_numpy(dtype=float)
    df["cluster_label"] = _dbscan_labels(coords, eps_m, min_pts, earth_radius_km)

    n_clusters = int(
        (df["cluster_label"] >= 0).any()
        and df.loc[df["cluster_label"] >= 0, "cluster_label"].nunique()
    )
    logger.info(
        "DBSCAN (eps=%.0f m, MinPts=%d): %d clusters, %d noise points of %d dwellings",
        eps_m,
        min_pts,
        n_clusters,
        int((df["cluster_label"] == NOISE_LABEL).sum()),
        len(df),
    )
    return df


def micro_cluster_noise(buildings: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Re-apply Equation 2 to noise points at the relaxed radius (Equation 10).

    Noise points that are density-connected at ``relaxed_eps_m`` (300-500 m)
    form *micro-clusters*, which remain eligible for the micro-mini-grid versus
    aggregated-SHS comparison rather than defaulting straight to standalone.
    Micro-cluster labels are offset above the primary cluster labels so the two
    label spaces never collide.

    Returns:
        A copy with ``micro_cluster_label`` (-1 where not applicable) and
        ``settlement_id``, the label the rest of the pipeline groups on.
    """
    df = buildings.copy()
    relaxed_eps = float(config.get("clustering.relaxed_eps_m", 400.0))
    relaxed_min_pts = int(config.get("clustering.relaxed_min_pts", 2))
    earth_radius_km = float(config.get("clustering.earth_radius_km", EARTH_RADIUS_KM))

    df["micro_cluster_label"] = NOISE_LABEL
    noise_mask = df["cluster_label"] == NOISE_LABEL
    if noise_mask.any():
        noise_coords = df.loc[noise_mask, ["latitude", "longitude"]].to_numpy(dtype=float)
        labels = _dbscan_labels(noise_coords, relaxed_eps, relaxed_min_pts, earth_radius_km)
        df.loc[noise_mask, "micro_cluster_label"] = labels
        logger.info(
            "relaxed pass (eps=%.0f m, MinPts=%d): %d micro-clusters recovered from %d noise points",
            relaxed_eps,
            relaxed_min_pts,
            len(set(labels[labels >= 0])),
            int(noise_mask.sum()),
        )

    primary_max = int(df["cluster_label"].max()) if (df["cluster_label"] >= 0).any() else -1
    offset = primary_max + 1

    settlement_ids: list[str] = []
    for row in df.itertuples(index=False):
        if row.cluster_label >= 0:
            settlement_ids.append(f"C{int(row.cluster_label):06d}")
        elif row.micro_cluster_label >= 0:
            settlement_ids.append(f"M{int(row.micro_cluster_label) + offset:06d}")
        else:
            # A genuinely isolated homestead: its own single-building settlement.
            settlement_ids.append(f"D{_row_key(row):06d}")
    df["settlement_id"] = settlement_ids
    df["is_dispersed"] = df["cluster_label"] == NOISE_LABEL
    return df


def _row_key(row) -> int:
    """Stable per-building key for naming single-homestead settlements."""
    building_id = getattr(row, "building_id", None)
    if isinstance(building_id, (int, np.integer)):
        return int(building_id)
    return abs(hash(building_id)) % 1_000_000


def summarise_clusters(buildings: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Collapse building rows into one row per settlement.

    Produces the settlement table that Stages 3-5 operate on: household count
    ``H_c`` (Equation 3), the cluster centroid, its extent, built density, and
    distance to the MV network (``D_c`` of Equation 5, taken as the minimum over
    member buildings, i.e. the nearest point of connection).
    """
    if buildings.empty:
        return pd.DataFrame(
            columns=[
                "settlement_id",
                "n_buildings",
                "households",
                "latitude",
                "longitude",
                "area_km2",
                "density_bldg_per_km2",
                "distance_to_mv_km",
                "distance_to_lv_km",
                "is_dispersed",
                "is_micro_cluster",
            ]
        )

    grouped = buildings.groupby("settlement_id", sort=True)
    rows = []
    for settlement_id, block in grouped:
        lat = block["latitude"].to_numpy(dtype=float)
        lon = block["longitude"].to_numpy(dtype=float)
        area_km2 = _bounding_area_km2(
            lat, lon, float(config.get("clustering.earth_radius_km", EARTH_RADIUS_KM))
        )
        households = (
            float(block["households"].sum()) if "households" in block else float(len(block))
        )
        rows.append(
            {
                "settlement_id": settlement_id,
                "n_buildings": len(block),
                "households": households,
                "latitude": float(lat.mean()),
                "longitude": float(lon.mean()),
                "area_km2": area_km2,
                "density_bldg_per_km2": (len(block) / area_km2) if area_km2 > 0 else np.nan,
                "distance_to_mv_km": float(block["distance_to_mv_km"].min())
                if "distance_to_mv_km" in block
                else np.inf,
                "distance_to_lv_km": float(block["distance_to_lv_km"].min())
                if "distance_to_lv_km" in block
                else np.inf,
                "is_dispersed": bool(block["is_dispersed"].all())
                if "is_dispersed" in block
                else False,
                "is_micro_cluster": str(settlement_id).startswith("M"),
            }
        )
    return pd.DataFrame(rows)


def _bounding_area_km2(lat: np.ndarray, lon: np.ndarray, earth_radius_km: float) -> float:
    """Approximate settlement footprint area from its lat/lon bounding box.

    A minimum extent of one hectare is imposed so that single-building and
    perfectly collinear settlements do not produce an infinite density.
    """
    mean_lat_rad = np.radians(lat.mean())
    km_per_deg_lat = np.pi * earth_radius_km / 180.0
    km_per_deg_lon = km_per_deg_lat * np.cos(mean_lat_rad)
    height = max((lat.max() - lat.min()) * km_per_deg_lat, 0.0)
    width = max((lon.max() - lon.min()) * km_per_deg_lon, 0.0)
    return max(height * width, 0.01)
