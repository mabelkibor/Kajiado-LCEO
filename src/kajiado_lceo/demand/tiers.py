"""Equations 3-4 — settlement energy and peak demand.

Equation 3, annual energy demand of settlement ``c``:

    E_c = sum over households h in c of 365 * d_h

where ``H_c`` is the filtered household count (Section 3.4.3) and ``d_h`` the
standardised daily demand of the tier assigned to that household. With a single
tier per settlement this reduces to ``E_c = 365 * H_c * d_h``, which is the form
implemented here; the per-household summation is preserved in the signature so
that a mixed-tier settlement can be modelled without changing call sites.

Equation 4, the coincident peak used to size mini-grid and standalone plant:

    P_c,peak = (E_c / 365) / LF

with the load factor ``LF`` in 0.3-0.4 for rural residential profiles. Both the
non-residential uplift and the diversity factor are applied before the peak is
taken, so that generation sizing sees the same load the LCOE denominator does.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kajiado_lceo.config import Config
from kajiado_lceo.logging_setup import get_logger

logger = get_logger(__name__)

HOURS_PER_DAY = 24.0


def assign_demand_tier(typology: str, config: Config) -> str:
    """Resolve the demand tier for a settlement typology (Section 3.5.1)."""
    assignment = config.section("demand.assignment")
    for rule in assignment.get("rules", []) or []:
        if str(rule.get("typology")) == str(typology):
            return str(rule.get("tier", assignment.get("default_tier", "tier_2")))
    return str(assignment.get("default_tier", "tier_2"))


def tier_daily_kwh(tier: str, config: Config) -> float:
    """Standardised daily household consumption ``d_h`` for a tier, in kWh/day."""
    return float(config.require(f"demand.tiers.{tier}.kwh_per_household_day"))


def annual_energy_demand_kwh(
    households: float | np.ndarray,
    daily_kwh_per_household: float | np.ndarray,
    days_per_year: int = 365,
) -> np.ndarray:
    """Equation 3 — annual energy demand ``E_c`` in kWh/year."""
    return (
        np.asarray(households, dtype=float)
        * np.asarray(daily_kwh_per_household, dtype=float)
        * float(days_per_year)
    )


def peak_demand_kw(
    annual_energy_kwh: float | np.ndarray,
    load_factor: float | np.ndarray,
    days_per_year: int = 365,
) -> np.ndarray:
    """Equation 4 — coincident peak demand ``P_c,peak`` in kW.

    The proposal writes ``P_c,peak = (E_c / 365) / LF``. Taken literally with
    ``E_c`` in kWh/year, the numerator is a daily energy in kWh and the result
    carries units of kWh/day; dividing additionally by 24 h converts it to the
    kW that plant sizing requires. That conversion is made explicit here:

        P_c,peak [kW] = E_c / (365 * 24 * LF)

    which is the standard load-factor identity (average power divided by the
    load factor) and is the form documented in docs/METHODOLOGY.md.
    """
    energy = np.asarray(annual_energy_kwh, dtype=float)
    lf = np.asarray(load_factor, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return energy / (float(days_per_year) * HOURS_PER_DAY * lf)


def estimate_demand(settlements: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Apply Equations 3-4 to every settlement.

    Adds ``demand_tier``, ``daily_kwh_per_household``, ``load_factor``,
    ``annual_energy_kwh`` (residential and total) and ``peak_demand_kw``.
    """
    if "typology" not in settlements.columns:
        raise ValueError("estimate_demand requires a 'typology' column; run assign_typology first")

    df = settlements.copy()
    days = int(config.get("demand.days_per_year", 365))
    default_lf = float(config.require("demand.load_factor"))
    lf_by_typology = config.section("demand.load_factor_by_typology")
    diversity = float(config.get("demand.diversity_factor", 1.0))
    non_res = config.section("demand.non_residential")

    df["demand_tier"] = [assign_demand_tier(t, config) for t in df["typology"]]
    df["daily_kwh_per_household"] = [tier_daily_kwh(t, config) for t in df["demand_tier"]]
    df["load_factor"] = [float(lf_by_typology.get(t, default_lf)) for t in df["typology"]]

    df["residential_energy_kwh"] = annual_energy_demand_kwh(
        df["households"], df["daily_kwh_per_household"], days
    )

    # Non-residential load (schools, dispensaries, shops, water pumping) is
    # added as an uplift on larger settlements only; dispersed homesteads and
    # very small clusters carry no anchor load worth modelling.
    if non_res.get("enabled", False):
        uplift = float(non_res.get("uplift_fraction", 0.0))
        min_hh = float(non_res.get("min_households", 0))
        applies = df["households"] >= min_hh
        df["non_residential_energy_kwh"] = np.where(
            applies, df["residential_energy_kwh"] * uplift, 0.0
        )
    else:
        df["non_residential_energy_kwh"] = 0.0

    df["annual_energy_kwh"] = df["residential_energy_kwh"] + df["non_residential_energy_kwh"]
    df["peak_demand_kw"] = (
        peak_demand_kw(df["annual_energy_kwh"], df["load_factor"], days) * diversity
    )

    logger.info(
        "demand estimated for %d settlements: %.1f GWh/year across %.0f households",
        len(df),
        df["annual_energy_kwh"].sum() / 1e6,
        df["households"].sum(),
    )
    return df
