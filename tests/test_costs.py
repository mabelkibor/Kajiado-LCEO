"""Equations 5-9 — CAPEX functions, annualisation and LCOE."""

from __future__ import annotations

import numpy as np
import pytest

from kajiado_lceo.clustering.typology import assign_typology
from kajiado_lceo.costs.annualisation import (
    capital_recovery_factor,
    discounted_energy,
    lcoe,
    net_present_cost,
    npc_lcoe,
)
from kajiado_lceo.costs.grid import grid_capex, grid_opex
from kajiado_lceo.costs.minigrid import minigrid_capex, size_minigrid
from kajiado_lceo.costs.sizing import lv_network_length_km, transformers_required
from kajiado_lceo.costs.standalone import standalone_capex
from kajiado_lceo.demand.tiers import estimate_demand


@pytest.fixture
def costed(toy_settlements, config):
    return estimate_demand(assign_typology(toy_settlements, config), config)


# --- Equation 8 ---------------------------------------------------------


def test_crf_matches_the_textbook_value():
    # r = 10%, n = 20 years -> 0.117460 (standard annuity factor).
    assert capital_recovery_factor(0.10, 20) == pytest.approx(0.117460, abs=1e-6)


def test_crf_at_zero_discount_is_one_over_n():
    assert capital_recovery_factor(0.0, 10) == pytest.approx(0.1)


def test_crf_increases_with_the_discount_rate():
    assert capital_recovery_factor(0.15, 20) > capital_recovery_factor(0.05, 20)


def test_crf_decreases_with_lifetime():
    assert capital_recovery_factor(0.10, 30) < capital_recovery_factor(0.10, 10)


def test_crf_rejects_a_non_positive_lifetime():
    with pytest.raises(ValueError, match="positive"):
        capital_recovery_factor(0.10, 0)


# --- Equations 9 and 9a -------------------------------------------------


def test_lcoe_is_annualised_cost_over_annual_energy():
    value = lcoe(
        capex=100_000, opex=3_000, annual_energy_kwh=50_000, discount_rate=0.10, lifetime_years=20
    )
    expected = (100_000 * capital_recovery_factor(0.10, 20) + 3_000) / 50_000
    assert value == pytest.approx(expected)


def test_the_two_lcoe_forms_agree_without_replacements_or_salvage():
    # Equation 9 and Equation 9a are stated as equivalent; with constant OPEX,
    # no replacements and no salvage they must coincide exactly.
    annualised = lcoe(100_000, 3_000, 50_000, 0.10, 20)
    discounted, _ = npc_lcoe(100_000, 3_000, 50_000, 0.10, 20)
    assert discounted == pytest.approx(annualised, rel=1e-9)


def test_replacements_raise_the_discounted_lcoe():
    without, _ = npc_lcoe(100_000, 3_000, 50_000, 0.10, 20)
    with_replacement, _ = npc_lcoe(
        100_000, 3_000, 50_000, 0.10, 20, replacements=[(8, np.array(20_000.0))]
    )
    assert with_replacement > without


def test_salvage_lowers_the_discounted_lcoe():
    without, _ = npc_lcoe(100_000, 3_000, 50_000, 0.10, 20)
    with_salvage, _ = npc_lcoe(100_000, 3_000, 50_000, 0.10, 20, salvage_fraction=0.20)
    assert with_salvage < without


def test_zero_demand_gives_nan_not_infinity():
    # NaN is excluded from the Equation 10 argmin; infinity would rank last.
    assert np.isnan(lcoe(100_000, 3_000, 0.0, 0.10, 20))


def test_discounted_energy_is_less_than_undiscounted():
    assert discounted_energy(1000.0, 0.10, 20) < 1000.0 * 20


def test_npc_includes_discounted_opex():
    npc = net_present_cost(100_000, 5_000, 0.10, 20)
    assert npc > 100_000
    assert npc < 100_000 + 5_000 * 20  # discounting must bite


# --- Equations 5-7 ------------------------------------------------------


def test_grid_capex_terms_sum_to_the_total(costed, config):
    out = grid_capex(costed, config)
    near = out.iloc[0]
    total = near["cost_mv"] + near["cost_lv"] + near["cost_transformers"] + near["cost_connections"]
    assert near["capex_grid"] == pytest.approx(total)


def test_grid_capex_rises_with_distance_to_the_network(costed, config):
    out = grid_capex(costed, config)
    # Settlement 0 is 0.8 km out; settlement 1 is 45 km out with fewer households.
    assert out.loc[1, "cost_mv"] > out.loc[0, "cost_mv"]


def test_grid_is_infeasible_beyond_the_maximum_extension_distance(costed, config):
    out = grid_capex(costed, config)
    # Settlement 2 sits at 60 km, past the configured 50 km limit.
    assert np.isnan(out.loc[2, "capex_grid"])


def test_connection_fee_term_scales_with_households(costed, config):
    out = grid_capex(costed, config)
    fee = float(config.get("technologies.grid.connection_cost_per_household"))
    assert out.loc[0, "cost_connections"] == pytest.approx(150.0 * fee)


def test_removing_the_connection_fee_lowers_grid_capex(costed, config):
    free = config.with_override_path("technologies.grid.connection_cost_per_household", 0.0)
    assert (
        grid_capex(costed, free)["capex_grid"].iloc[0]
        < grid_capex(costed, config)["capex_grid"].iloc[0]
    )


def test_terrain_multiplier_raises_the_mv_term(costed, config):
    flat = grid_capex(costed, config)
    hilly = costed.copy()
    hilly["terrain_class"] = "steep"
    assert grid_capex(hilly, config)["cost_mv"].iloc[0] > flat["cost_mv"].iloc[0]


def test_spare_transformer_capacity_reduces_new_transformers():
    peak = np.array([80.0])
    without = transformers_required(peak, 50.0, 0.9, spare_capacity_kva=0.0)
    with_spare = transformers_required(peak, 50.0, 0.9, spare_capacity_kva=60.0)
    assert with_spare[0] < without[0]


def test_lv_length_grows_with_households_and_area():
    short = lv_network_length_km(10, 0.05, 0.75, 0.02)
    long = lv_network_length_km(100, 0.50, 0.75, 0.02)
    assert long > short


def test_minigrid_sizing_is_consistent_with_demand(costed, config):
    sizing = size_minigrid(costed, config)
    cfg = config.section("technologies.minigrid")
    energy = costed["annual_energy_kwh"].iloc[0]
    expected_pv = (
        energy
        * cfg["pv_oversize_factor"]
        / (365 * cfg["peak_sun_hours"] * cfg["performance_ratio"])
    )
    assert sizing["pv_capacity_kw"].iloc[0] == pytest.approx(expected_pv)
    assert sizing["battery_capacity_kwh"].iloc[0] > 0
    assert sizing["inverter_capacity_kw"].iloc[0] >= costed["peak_demand_kw"].iloc[0]


def test_minigrid_capex_terms_sum_to_the_total(costed, config):
    out = minigrid_capex(costed, config)
    row = out.iloc[0]
    total = (
        row["cost_pv"]
        + row["cost_battery"]
        + row["cost_inverter"]
        + row["cost_distribution"]
        + row["cost_connections"]
    )
    assert row["capex_minigrid"] == pytest.approx(total)


def test_minigrid_is_not_offered_below_the_minimum_size(costed, config):
    out = minigrid_capex(costed, config)
    assert np.isnan(out.loc[2, "capex_minigrid"]), "a single homestead is not a mini-grid"


def test_standalone_capex_is_linear_in_households(costed, config):
    out = standalone_capex(costed, config)
    per_household = out["kit_cost_per_household"].iloc[0]
    assert out["capex_standalone"].iloc[0] == pytest.approx(150.0 * per_household)


def test_standalone_kit_cost_rises_with_demand_tier(config):
    kits = config.section("technologies.standalone.kit_by_tier")
    totals = [sum(kits[f"tier_{i}"].values()) for i in range(1, 5)]
    assert totals == sorted(totals)


def test_standalone_kit_costs_match_their_sizing_basis(config):
    """Equation 7's kit costs must be consistent with the energy of Equation 3.

    Guards the failure mode where a cheap kit is credited with delivering a high
    tier's consumption, which would understate the SHS LCOE and bias Equation 10.
    """
    basis = config.section("technologies.standalone.sizing_basis")
    kits = config.section("technologies.standalone.kit_by_tier")
    for tier, kit in kits.items():
        daily = float(config.require(f"demand.tiers.{tier}.kwh_per_household_day"))
        pv_kw = (
            daily
            * basis["pv_oversize_factor"]
            / (basis["peak_sun_hours"] * basis["performance_ratio"])
        )
        battery_kwh = daily / (
            basis["battery_depth_of_discharge"] * basis["battery_round_trip_efficiency"]
        )
        expected_panel = max(pv_kw * basis["small_system_pv_cost_per_kw"], basis["min_panel_cost"])
        expected_battery = max(
            battery_kwh * basis["small_system_battery_cost_per_kwh"], basis["min_battery_cost"]
        )
        assert kit["panel"] == pytest.approx(expected_panel, rel=0.01), tier
        assert kit["battery"] == pytest.approx(expected_battery, rel=0.01), tier


def test_grid_opex_includes_the_cost_of_losses(config, costed):
    energy = 100_000.0
    with_losses = grid_opex(0.0, energy, config)
    lossless = config.with_override_path("technologies.grid.technical_losses", 0.0)
    assert with_losses > grid_opex(0.0, energy, lossless)
