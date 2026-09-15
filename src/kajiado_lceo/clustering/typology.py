"""Settlement typology labels.

The proposal repeatedly distinguishes dispersed homesteads, small and large
rural clusters, and dense peri-urban zones (Sections 1.6, 3.3, 3.7). Typology is
assigned from household count and built density and then drives demand-tier
assignment (Section 3.5.1, algorithm 2) and the by-typology reporting of
Section 3.7.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kajiado_lceo.config import Config

TYPOLOGIES = ("dispersed", "small_rural", "large_rural", "peri_urban")


def assign_typology(settlements: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Add a ``typology`` column to the settlement table.

    Density is tested first: a small but very dense cluster on the Kitengela or
    Ngong fringe is peri-urban regardless of household count, which is the
    heterogeneity the framework exists to capture.
    """
    cfg = config.section("typology")
    dispersed_max = float(cfg.get("dispersed_max_households", 2))
    small_max = float(cfg.get("small_rural_max_households", 50))
    large_max = float(cfg.get("large_rural_max_households", 500))
    peri_urban_density = float(cfg.get("peri_urban_min_density_bldg_per_km2", 300.0))

    df = settlements.copy()
    households = df["households"].to_numpy(dtype=float)
    density = df.get("density_bldg_per_km2", pd.Series(np.nan, index=df.index)).to_numpy(
        dtype=float
    )

    labels = np.full(len(df), "large_rural", dtype=object)
    labels[households <= dispersed_max] = "dispersed"
    labels[(households > dispersed_max) & (households <= small_max)] = "small_rural"
    labels[(households > small_max) & (households <= large_max)] = "large_rural"
    labels[households > large_max] = "peri_urban"

    dense = (~np.isnan(density)) & (density >= peri_urban_density) & (households > dispersed_max)
    labels[dense] = "peri_urban"

    df["typology"] = labels
    return df
