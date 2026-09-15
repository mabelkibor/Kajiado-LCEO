"""Equation 6 — solar PV mini-grid CAPEX, its sizing, and its operating cost.

    CAPEX_mg,c = (C_PV * P_sys,c) + (C_batt * Cap_batt,c) + (C_inv * P_inv,c)
                 + (C_dist * L_mg,c) + (H_c * C_conn,mg)

Equation 6 states the cost terms but leaves the plant sizing implicit.
:func:`size_minigrid` fills that in from the demand profile of Equations 3-4:

* **PV array** — sized on energy, not power: the array must deliver ``E_c``
  after inverter and array losses, given the site's peak sun hours and a
  performance ratio, with an oversize factor for soiling and degradation::

      P_sys = E_c * oversize / (365 * PSH * PR)

* **Battery** — sized on autonomy: ``Cap_batt = daily energy * autonomy days
  / (depth of discharge * round-trip efficiency)``.

* **Inverter** — sized on the coincident peak ``P_c,peak`` with a headroom
  factor.

Storage and inverter replacements fall inside the mini-grid's analysis period
and are recognised in the net present cost of Equation 9a rather than being
smeared into OPEX.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kajiado_lceo.config import Config
from kajiado_lceo.costs.sizing import lv_network_length_km


def size_minigrid(settlements: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Size PV, storage, inverter and distribution for each settlement."""
    cfg = config.section("technologies.minigrid")
    days = float(config.get("demand.days_per_year", 365))

    energy = settlements["annual_energy_kwh"].to_numpy(dtype=float)
    peak = settlements["peak_demand_kw"].to_numpy(dtype=float)
    households = settlements["households"].to_numpy(dtype=float)

    psh = float(cfg["peak_sun_hours"])
    pr = float(cfg["performance_ratio"])
    oversize = float(cfg.get("pv_oversize_factor", 1.0))

    out = pd.DataFrame(index=settlements.index)
    out["pv_capacity_kw"] = energy * oversize / (days * psh * pr)

    daily_energy_kwh = energy / days
    dod = float(cfg["battery_depth_of_discharge"])
    rte = float(cfg.get("battery_round_trip_efficiency", 1.0))
    out["battery_capacity_kwh"] = (
        daily_energy_kwh * float(cfg["battery_autonomy_days"]) / max(dod * rte, 1e-9)
    )

    out["inverter_capacity_kw"] = peak * float(cfg.get("inverter_sizing_factor", 1.0))

    out["distribution_length_km"] = lv_network_length_km(
        households,
        settlements["area_km2"].to_numpy(dtype=float),
        float(cfg["distribution_length_area_coefficient"]),
        float(cfg["distribution_length_per_household_km"]),
    )
    return out


def minigrid_capex(settlements: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Compute Equation 6 term by term for every settlement.

    Settlements below ``min_households`` receive ``NaN``: a mini-grid with an
    operator, a tariff and a distribution network is not a credible option for a
    handful of dwellings, and the micro-cluster check of Equation 10 handles the
    genuinely small cases separately by relaxing that floor.
    """
    cfg = config.section("technologies.minigrid")
    sizing = size_minigrid(settlements, config)
    out = sizing.copy()

    households = settlements["households"].to_numpy(dtype=float)
    out["cost_pv"] = float(cfg["cost_pv_per_kw"]) * sizing["pv_capacity_kw"]
    out["cost_battery"] = float(cfg["cost_battery_per_kwh"]) * sizing["battery_capacity_kwh"]
    out["cost_inverter"] = float(cfg["cost_inverter_per_kw"]) * sizing["inverter_capacity_kw"]
    out["cost_distribution"] = (
        float(cfg["cost_distribution_per_km"]) * sizing["distribution_length_km"]
    )
    out["cost_connections"] = households * float(cfg["connection_cost_per_household"])

    out["capex_minigrid"] = (
        out["cost_pv"]
        + out["cost_battery"]
        + out["cost_inverter"]
        + out["cost_distribution"]
        + out["cost_connections"]
    )

    min_households = float(cfg.get("min_households", 0))
    out.loc[households < min_households, "capex_minigrid"] = np.nan
    return out


def minigrid_opex(capex: float | np.ndarray, config: Config) -> np.ndarray:
    """Annual O&M cost of a mini-grid, as a fraction of installed CAPEX.

    Fuel is absent by construction (solar plus storage), so O&M covers the
    operator, cleaning, spares and revenue collection.
    """
    cfg = config.section("technologies.minigrid")
    return np.asarray(capex, dtype=float) * float(cfg.get("opex_fraction_of_capex", 0.0))


def minigrid_replacements(
    capex_components: pd.DataFrame, config: Config
) -> list[tuple[int, np.ndarray]]:
    """Mid-life replacement outlays, as ``(year, cost)`` pairs.

    Feeds the net present cost form of Equation 9a, where the outlay is
    discounted in the year it occurs rather than annualised across the whole
    project life.
    """
    cfg = config.section("technologies.minigrid")
    lifetime = int(config.get("finance.analysis_period_years", cfg.get("lifetime_years", 20)))
    events: list[tuple[int, np.ndarray]] = []

    battery_years = int(cfg.get("battery_replacement_years", 0) or 0)
    if battery_years > 0:
        share = float(cfg.get("battery_replacement_cost_fraction", 1.0))
        for year in range(battery_years, lifetime, battery_years):
            events.append((year, capex_components["cost_battery"].to_numpy(dtype=float) * share))

    inverter_years = int(cfg.get("inverter_replacement_years", 0) or 0)
    if inverter_years > 0:
        share = float(cfg.get("inverter_replacement_cost_fraction", 1.0))
        for year in range(inverter_years, lifetime, inverter_years):
            events.append((year, capex_components["cost_inverter"].to_numpy(dtype=float) * share))

    return events
