"""Equation 5 — grid extension CAPEX, and its operating cost.

    CAPEX_grid,c = (C_MV * D_c) + (C_LV * L_LV,c) + C_xfmr + (H_c * C_conn)

The four terms are, in order: the medium-voltage spur from the nearest existing
MV line to the settlement; the internal low-voltage reticulation; transformer
capacity where the existing network has none to spare; and the household
connection cost.

The connection-fee term is carried explicitly rather than folded into a
per-household average because, as the proposal notes (Section 3.5.4), high
household connection fees are in practice a decisive barrier to take-up in
Kenya even where the network already passes nearby. Keeping it separate lets
the same number appear as a utility cost, a developer revenue, or a subsidised
write-off depending on the perspective being evaluated (Equations 11-14).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kajiado_lceo.config import Config
from kajiado_lceo.costs.sizing import lv_network_length_km, transformers_required


def grid_capex(settlements: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Compute Equation 5 term by term for every settlement.

    Returns a frame indexed like ``settlements`` with one column per term plus
    ``capex_grid``. Settlements beyond ``max_extension_distance_km`` — or with
    no reachable MV network at all — receive ``NaN``, which the decision rule of
    Equation 10 reads as "grid is not a candidate here".
    """
    cfg = config.section("technologies.grid")
    out = pd.DataFrame(index=settlements.index)

    distance_km = settlements["distance_to_mv_km"].to_numpy(dtype=float)
    households = settlements["households"].to_numpy(dtype=float)

    terrain = settlements.get("terrain_class", pd.Series("flat", index=settlements.index))
    multipliers = cfg.get("terrain_multiplier", {}) or {}
    terrain_factor = np.array([float(multipliers.get(str(t), 1.0)) for t in terrain])

    out["mv_length_km"] = distance_km
    out["cost_mv"] = float(cfg["cost_mv_per_km"]) * distance_km * terrain_factor

    out["lv_length_km"] = lv_network_length_km(
        households,
        settlements["area_km2"].to_numpy(dtype=float),
        float(cfg["lv_length_area_coefficient"]),
        float(cfg["lv_length_per_household_km"]),
    )
    out["cost_lv"] = float(cfg["cost_lv_per_km"]) * out["lv_length_km"]

    spare = (
        settlements.get("nearest_transformer_spare_kva", pd.Series(0.0, index=settlements.index))
        .fillna(0.0)
        .to_numpy(dtype=float)
    )
    out["n_transformers"] = transformers_required(
        settlements["peak_demand_kw"].to_numpy(dtype=float),
        float(cfg["transformer_capacity_kva"]),
        float(cfg.get("transformer_power_factor", 0.9)),
        spare,
    )
    out["cost_transformers"] = float(cfg["cost_transformer"]) * out["n_transformers"]

    out["cost_connections"] = households * float(cfg["connection_cost_per_household"])

    out["capex_grid"] = (
        out["cost_mv"] + out["cost_lv"] + out["cost_transformers"] + out["cost_connections"]
    )

    max_distance = float(cfg.get("max_extension_distance_km", np.inf))
    infeasible = ~np.isfinite(distance_km) | (distance_km > max_distance)
    out.loc[infeasible, "capex_grid"] = np.nan
    return out


def grid_opex(
    capex: float | np.ndarray,
    annual_energy_kwh: float | np.ndarray,
    config: Config,
) -> np.ndarray:
    """Annual operating cost of a grid-extension scheme.

    Two components: network operation and maintenance, taken as a fraction of
    CAPEX, and the cost of the energy itself purchased at the bulk supply point
    and grossed up for technical losses — the extended network must import more
    than it delivers.
    """
    cfg = config.section("technologies.grid")
    capex = np.asarray(capex, dtype=float)
    energy = np.asarray(annual_energy_kwh, dtype=float)
    losses = float(cfg.get("technical_losses", 0.0))
    energy_purchased = energy / max(1.0 - losses, 1e-9)
    return capex * float(cfg.get("opex_fraction_of_capex", 0.0)) + energy_purchased * float(
        cfg.get("bulk_supply_cost_per_kwh", 0.0)
    )
