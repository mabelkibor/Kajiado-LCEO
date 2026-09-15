"""Stage 1 — spatial pre-processing: structure filtering and served-status tagging."""

from kajiado_lceo.preprocessing.electrification_status import tag_served_buildings
from kajiado_lceo.preprocessing.footprint_filter import (
    compactness,
    filter_footprints,
    filter_summary,
)

__all__ = ["compactness", "filter_footprints", "filter_summary", "tag_served_buildings"]
