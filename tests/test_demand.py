"""Equations 3-4 — annual energy demand and peak demand."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kajiado_lceo.demand.tiers import (
    annual_energy_demand_kwh,
    assign_demand_tier,
    estimate_demand,
    peak_demand_kw,
    tier_daily_kwh,
)


def test_equation_3_is_households_times_daily_times_365():
    assert annual_energy_demand_kwh(100, 1.0) == pytest.approx(36_500.0)


def test_equation_3_scales_linearly_in_households():
    single = annual_energy_demand_kwh(1, 3.4)
    assert annual_energy_demand_kwh(50, 3.4) == pytest.approx(50 * single)


def test_equation_4_recovers_average_power_at_unit_load_factor():
    # At LF = 1 the peak equals the average power: E / (365*24).
    energy = 8760.0
    assert peak_demand_kw(energy, 1.0) == pytest.approx(1.0)


def test_lower_load_factor_implies_a_higher_peak():
    energy = 100_000.0
    assert peak_demand_kw(energy, 0.30) > peak_demand_kw(energy, 0.40)


def test_peak_is_inversely_proportional_to_load_factor():
    energy = 100_000.0
    assert peak_demand_kw(energy, 0.20) == pytest.approx(2 * peak_demand_kw(energy, 0.40))


def test_tiers_increase_monotonically(config):
    values = [tier_daily_kwh(f"tier_{i}", config) for i in range(1, 5)]
    assert values == sorted(values)
    assert values[0] > 0


def test_tier_assignment_follows_the_configured_rules(config):
    assert assign_demand_tier("dispersed", config) == "tier_1"
    assert assign_demand_tier("peri_urban", config) == "tier_4"


def test_unknown_typology_falls_back_to_the_default_tier(config):
    default = config.get("demand.assignment.default_tier")
    assert assign_demand_tier("not_a_typology", config) == default


def test_estimate_demand_populates_every_expected_column(config):
    settlements = pd.DataFrame(
        {
            "settlement_id": ["a", "b"],
            "households": [10.0, 200.0],
            "typology": ["small_rural", "peri_urban"],
        }
    )
    out = estimate_demand(settlements, config)
    for column in ("demand_tier", "annual_energy_kwh", "peak_demand_kw", "load_factor"):
        assert column in out.columns
    assert (out["annual_energy_kwh"] > 0).all()
    assert (out["peak_demand_kw"] > 0).all()


def test_non_residential_uplift_applies_only_above_the_threshold(config):
    threshold = float(config.get("demand.non_residential.min_households"))
    settlements = pd.DataFrame(
        {
            "settlement_id": ["small", "large"],
            "households": [threshold - 1, threshold + 1],
            "typology": ["small_rural", "large_rural"],
        }
    )
    out = estimate_demand(settlements, config)
    assert out.loc[0, "non_residential_energy_kwh"] == 0.0
    assert out.loc[1, "non_residential_energy_kwh"] > 0.0


def test_missing_typology_column_raises(config):
    with pytest.raises(ValueError, match="typology"):
        estimate_demand(pd.DataFrame({"households": [5.0]}), config)


def test_zero_households_gives_zero_demand(config):
    out = estimate_demand(
        pd.DataFrame({"settlement_id": ["z"], "households": [0.0], "typology": ["dispersed"]}),
        config,
    )
    assert out["annual_energy_kwh"].iloc[0] == 0.0
    assert np.isnan(out["peak_demand_kw"].iloc[0]) or out["peak_demand_kw"].iloc[0] == 0.0
