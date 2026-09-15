"""Section 3.4.3 / Table 3.3 — filtering non-residential structures.

AI-derived footprint datasets detect built-up structures in general, not
dwellings. In Kajiado's rural wards a homestead (manyatta/boma) typically
combines one or two dwellings with several smaller stores and livestock
enclosures, so counting every footprint as a household inflates ``H_c`` and,
through Equation 3, the settlement's demand.

Four criteria are applied in sequence, each recorded as its own boolean column
so the attrition at every step is auditable and reportable:

1. footprint area outside the habitable band  -> non-residential
2. compactness C = 4*pi*A / P^2 below threshold -> open enclosure
3. roof signature outside the residential classes (optional; needs sub-metre imagery)
4. compound co-location: keep the largest 1-3 structures per compound, treat
   smaller structures within the compound radius as ancillary

The filter is a heuristic, not a classifier. :func:`filter_summary` reports the
attrition so that the residual error rate measured on the ground-truth sample
(Section 3.8) can be carried into the demand uncertainty discussion.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kajiado_lceo.config import Config
from kajiado_lceo.geo.distance import haversine_matrix_km
from kajiado_lceo.logging_setup import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = ("building_id", "latitude", "longitude", "area_m2")


def compactness(area_m2: np.ndarray, perimeter_m: np.ndarray) -> np.ndarray:
    """Polygon compactness ``C = 4*pi*A / P^2`` (Table 3.3, criterion 2).

    C approaches 1 for a circle and falls towards 0 for long, thin or highly
    irregular polygons of the kind produced by thorn-fenced enclosures. Zero or
    missing perimeters yield ``NaN``, which the filter treats as "no evidence"
    rather than as a failed test.
    """
    area = np.asarray(area_m2, dtype=float)
    perimeter = np.asarray(perimeter_m, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        value = 4.0 * np.pi * area / np.square(perimeter)
    return np.where(perimeter > 0, value, np.nan)


def filter_footprints(footprints: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Apply the Table 3.3 heuristics and return an annotated copy.

    Adds the columns ``passes_area``, ``passes_compactness``, ``passes_roof``,
    ``is_ancillary``, ``is_dwelling`` and ``households``. No row is dropped, so
    that the excluded structures remain available for validation and mapping.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in footprints.columns]
    if missing:
        raise ValueError(f"building footprints are missing required columns: {missing}")

    df = footprints.copy()
    section = config.section("footprint_filter")
    if not section.get("enabled", True):
        df["passes_area"] = True
        df["passes_compactness"] = True
        df["passes_roof"] = True
        df["is_ancillary"] = False
        df["is_dwelling"] = True
        df["households"] = float(section.get("households_per_dwelling", 1.0))
        return df

    area = df["area_m2"].to_numpy(dtype=float)
    min_area = float(section.get("min_area_m2", 7.0))
    max_area = float(section.get("max_area_m2", np.inf))
    df["passes_area"] = (area >= min_area) & (area <= max_area)

    if "perimeter_m" in df.columns:
        c = compactness(area, df["perimeter_m"].to_numpy(dtype=float))
        df["compactness"] = c
        threshold = float(section.get("min_compactness", 0.0))
        # NaN compactness means no perimeter was supplied: do not penalise it.
        df["passes_compactness"] = np.where(np.isnan(c), True, c >= threshold)
    else:
        logger.info("no perimeter_m column supplied; compactness criterion skipped")
        df["compactness"] = np.nan
        df["passes_compactness"] = True

    roof_cfg = section.get("roof_signature", {}) or {}
    roof_attr = str(roof_cfg.get("attribute", "roof_class"))
    if roof_cfg.get("enabled", False) and roof_attr in df.columns:
        residential = set(roof_cfg.get("residential_classes", []))
        df["passes_roof"] = df[roof_attr].isin(residential)
    else:
        df["passes_roof"] = True

    candidate = df["passes_area"] & df["passes_compactness"] & df["passes_roof"]
    compound_cfg = section.get("compound", {}) or {}
    if compound_cfg.get("enabled", True):
        df["is_ancillary"] = _flag_ancillary_structures(
            df,
            candidate_mask=candidate.to_numpy(),
            radius_m=float(compound_cfg.get("radius_m", 12.0)),
            max_dwellings=int(compound_cfg.get("max_dwellings", 3)),
            earth_radius_km=float(config.get("clustering.earth_radius_km", 6371.0)),
        )
    else:
        df["is_ancillary"] = False

    df["is_dwelling"] = candidate & ~df["is_ancillary"]
    df["households"] = np.where(
        df["is_dwelling"], float(section.get("households_per_dwelling", 1.0)), 0.0
    )
    logger.info(
        "structure filter: %d of %d footprints retained as dwellings (%.1f%%)",
        int(df["is_dwelling"].sum()),
        len(df),
        100.0 * df["is_dwelling"].mean() if len(df) else 0.0,
    )
    return df


def _flag_ancillary_structures(
    df: pd.DataFrame,
    candidate_mask: np.ndarray,
    radius_m: float,
    max_dwellings: int,
    earth_radius_km: float,
) -> np.ndarray:
    """Compound co-location logic (Table 3.3, criterion 4).

    Structures are grouped into compounds by single-linkage within
    ``radius_m``. Within each compound the largest ``max_dwellings`` structures
    are kept as dwelling candidates and the remainder flagged ancillary, which
    reproduces the typical manyatta layout of one or two dwellings surrounded by
    stores and enclosures.
    """
    n = len(df)
    ancillary = np.zeros(n, dtype=bool)
    if n == 0:
        return ancillary

    coords = df[["latitude", "longitude"]].to_numpy(dtype=float)
    radius_km = radius_m / 1000.0
    labels = _single_linkage_labels(coords, radius_km, earth_radius_km)

    area = df["area_m2"].to_numpy(dtype=float)
    order = np.argsort(labels, kind="stable")
    for label in np.unique(labels):
        members = order[labels[order] == label]
        members = members[candidate_mask[members]]
        if len(members) <= max_dwellings:
            continue
        # Largest structures first; everything past max_dwellings is ancillary.
        ranked = members[np.argsort(-area[members], kind="stable")]
        ancillary[ranked[max_dwellings:]] = True
    return ancillary


def _single_linkage_labels(
    coords: np.ndarray, radius_km: float, earth_radius_km: float, chunk_size: int = 2048
) -> np.ndarray:
    """Label connected components under a fixed distance threshold.

    A small union-find over chunked distance blocks; adequate at compound scale
    and free of any external clustering dependency at this stage.
    """
    n = coords.shape[0]
    parent = np.arange(n)

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)

    for start in range(0, n, chunk_size):
        stop = min(start + chunk_size, n)
        block = haversine_matrix_km(coords[start:stop], coords, earth_radius_km)
        rows, cols = np.nonzero(block <= radius_km)
        for r, c in zip(rows + start, cols, strict=True):
            if r != c:
                union(int(r), int(c))
    return np.array([find(i) for i in range(n)], dtype=int)


def filter_summary(filtered: pd.DataFrame) -> pd.DataFrame:
    """Per-criterion attrition table, for reporting alongside Table 3.3."""
    total = len(filtered)
    rows = [
        ("footprints_in", total, 1.0),
        ("failed_area", int((~filtered["passes_area"]).sum()), None),
        ("failed_compactness", int((~filtered["passes_compactness"]).sum()), None),
        ("failed_roof_signature", int((~filtered["passes_roof"]).sum()), None),
        ("flagged_ancillary", int(filtered["is_ancillary"].sum()), None),
        ("dwellings_out", int(filtered["is_dwelling"].sum()), None),
    ]
    summary = pd.DataFrame(rows, columns=["criterion", "structures", "share"])
    summary["share"] = summary["structures"] / total if total else 0.0
    return summary
