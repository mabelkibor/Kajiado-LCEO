"""Equation 7 — standalone solar PV (SHS) CAPEX.

    CAPEX_shs,c = H_c * (C_panel + C_batt,shs + C_bos)

Every household carries its own panel, battery and balance-of-system, so cost
scales linearly with ``H_c`` and carries no distribution term at all. That
linearity is exactly why SHS wins in the dispersed case of Equation 10: grid and
mini-grid costs are dominated by network length per household, which rises
without bound as spacing grows, while the SHS cost per household does not move.

Kit cost is resolved by demand tier, since a Tier 1 lighting kit and a Tier 4
productive-use system differ by more than an order of magnitude.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kajiado_lceo.config import Config


def _kit_cost(tier: str, config: Config) -> float:
    kits = config.section("technologies.standalone.kit_by_tier")
    kit = kits.get(tier)
    if kit is None:
        raise KeyError(
            f"no standalone kit cost configured for demand tier '{tier}' "
            f"(available: {sorted(kits)})"
        )
    return float(kit["panel"]) + float(kit["battery"]) + float(kit["bos"])


def standalone_capex(settlements: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Compute Equation 7 for every settlement, resolving kit cost by tier."""
    out = pd.DataFrame(index=settlements.index)
    households = settlements["households"].to_numpy(dtype=float)
    kit_costs = np.array([_kit_cost(str(t), config) for t in settlements["demand_tier"]])

    out["kit_cost_per_household"] = kit_costs
    out["capex_standalone"] = households * kit_costs
    return out


def standalone_opex(capex: float | np.ndarray, config: Config) -> np.ndarray:
    """Annual servicing cost of an SHS fleet, as a fraction of CAPEX."""
    cfg = config.section("technologies.standalone")
    return np.asarray(capex, dtype=float) * float(cfg.get("opex_fraction_of_capex", 0.0))


def standalone_replacements(
    settlements: pd.DataFrame, config: Config
) -> list[tuple[int, np.ndarray]]:
    """Battery replacement outlays over the analysis period, per Equation 9a.

    SHS batteries are the shortest-lived component in the whole comparison
    (typically five years), so recognising their replacement explicitly matters
    to the grid/off-grid crossover rather than being a second-order detail.
    """
    cfg = config.section("technologies.standalone")
    lifetime = int(config.get("finance.analysis_period_years", cfg.get("lifetime_years", 15)))
    replacement_years = int(cfg.get("battery_replacement_years", 0) or 0)
    if replacement_years <= 0:
        return []

    kits = config.section("technologies.standalone.kit_by_tier")
    battery_cost = np.array([float(kits[str(t)]["battery"]) for t in settlements["demand_tier"]])
    households = settlements["households"].to_numpy(dtype=float)
    share = float(cfg.get("battery_replacement_cost_fraction", 1.0))

    return [
        (year, households * battery_cost * share)
        for year in range(replacement_years, lifetime, replacement_years)
    ]
