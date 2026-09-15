"""Stage 1 — deciding which buildings are already served.

The proposal's first specific objective is to identify *unelectrified*
settlements. Absent a building-level connection register, served status is
inferred from three pieces of spatial evidence, in descending order of
strength:

1. a KPLC meter record snapping to the footprint (``meter_snap_distance_m``);
2. proximity to an energised LV line (``lv_service_buffer_m``);
3. proximity to a transformer with spare capacity (``transformer_service_buffer_m``).

Rules 2 and 3 are proxies: a building inside an LV service radius *could* be
connected, not *is* connected. Where meter data is available, setting
``electrification_status.require_meter_evidence: true`` restricts the served
label to rule 1 alone, and the difference between the two runs bounds the
uncertainty in the unelectrified population — the validation check called for
in Section 3.8.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kajiado_lceo.config import Config
from kajiado_lceo.geo.distance import nearest_line_distance_km, nearest_point_distance_km
from kajiado_lceo.logging_setup import get_logger

logger = get_logger(__name__)


def tag_served_buildings(
    buildings: pd.DataFrame,
    mv_lines: np.ndarray | None = None,
    lv_lines: np.ndarray | None = None,
    transformers: pd.DataFrame | None = None,
    meters: pd.DataFrame | None = None,
    config: Config | None = None,
) -> pd.DataFrame:
    """Annotate buildings with distance-to-network and a served flag.

    Args:
        buildings: frame with ``latitude``/``longitude`` columns.
        mv_lines: ``(m, 4)`` array of ``(lat1, lon1, lat2, lon2)`` MV segments.
        lv_lines: ``(m, 4)`` array of LV segments.
        transformers: frame with ``latitude``/``longitude`` and optionally
            ``spare_capacity_kva``.
        meters: frame with ``latitude``/``longitude`` of billed connections.
        config: merged configuration.

    Returns:
        A copy with ``distance_to_mv_km``, ``distance_to_lv_km``,
        ``distance_to_transformer_km``, ``has_meter`` and ``is_served``.
    """
    if config is None:
        raise ValueError("tag_served_buildings requires a Config")

    df = buildings.copy()
    coords = df[["latitude", "longitude"]].to_numpy(dtype=float)
    radius_km = float(config.get("clustering.earth_radius_km", 6371.0))
    status = config.section("electrification_status")

    df["distance_to_mv_km"] = (
        nearest_line_distance_km(coords, mv_lines, radius_km=radius_km)
        if _has_rows(mv_lines)
        else np.inf
    )
    df["distance_to_lv_km"] = (
        nearest_line_distance_km(coords, lv_lines, radius_km=radius_km)
        if _has_rows(lv_lines)
        else np.inf
    )

    if transformers is not None and len(transformers):
        tx_coords = transformers[["latitude", "longitude"]].to_numpy(dtype=float)
        tx_distance, tx_index = nearest_point_distance_km(coords, tx_coords, radius_km=radius_km)
        df["distance_to_transformer_km"] = tx_distance
        if "spare_capacity_kva" in transformers.columns:
            spare = transformers["spare_capacity_kva"].to_numpy(dtype=float)
            df["nearest_transformer_spare_kva"] = np.where(tx_index >= 0, spare[tx_index], 0.0)
        else:
            df["nearest_transformer_spare_kva"] = np.nan
    else:
        df["distance_to_transformer_km"] = np.inf
        df["nearest_transformer_spare_kva"] = 0.0

    if meters is not None and len(meters):
        meter_coords = meters[["latitude", "longitude"]].to_numpy(dtype=float)
        meter_distance, _ = nearest_point_distance_km(coords, meter_coords, radius_km=radius_km)
        snap_km = float(status.get("meter_snap_distance_m", 25.0)) / 1000.0
        df["has_meter"] = meter_distance <= snap_km
    else:
        df["has_meter"] = False

    if status.get("require_meter_evidence", False):
        df["is_served"] = df["has_meter"]
    else:
        lv_buffer_km = float(status.get("lv_service_buffer_m", 300.0)) / 1000.0
        tx_buffer_km = float(status.get("transformer_service_buffer_m", 600.0)) / 1000.0
        near_lv = df["distance_to_lv_km"] <= lv_buffer_km
        near_tx = (df["distance_to_transformer_km"] <= tx_buffer_km) & (
            df["nearest_transformer_spare_kva"].fillna(0.0) > 0.0
        )
        df["is_served"] = df["has_meter"] | near_lv | near_tx

    logger.info(
        "served status: %d of %d dwellings already served (%.1f%%)",
        int(df["is_served"].sum()),
        len(df),
        100.0 * df["is_served"].mean() if len(df) else 0.0,
    )
    return df


def _has_rows(array: np.ndarray | None) -> bool:
    return array is not None and np.asarray(array).size > 0
