"""Equations 11-14 — cash flows, NPV, IRR and discounted payback."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kajiado_lceo.finance.dcf import (
    build_cash_flows,
    discounted_payback_period,
    evaluate_viability,
    internal_rate_of_return,
    net_present_value,
)

# --- Equation 12 --------------------------------------------------------


def test_npv_of_a_flat_annuity_matches_the_annuity_formula():
    flows = np.full(10, 1_000.0)
    r = 0.08
    expected = 1_000.0 * (1 - (1 + r) ** -10) / r
    assert net_present_value(flows, 0.0, r) == pytest.approx(expected)


def test_npv_falls_as_the_discount_rate_rises():
    flows = np.full(10, 1_000.0)
    assert net_present_value(flows, 0.0, 0.15) < net_present_value(flows, 0.0, 0.05)


def test_npv_is_net_of_year_zero_capital():
    flows = np.full(10, 1_000.0)
    gross = net_present_value(flows, 0.0, 0.10)
    assert net_present_value(flows, 2_000.0, 0.10) == pytest.approx(gross - 2_000.0)


# --- Equation 13 --------------------------------------------------------


def test_irr_makes_npv_zero(config):
    flows = np.full(10, 1_500.0)
    capex = 9_000.0
    irr = internal_rate_of_return(flows, capex, config)
    assert np.isfinite(irr)
    # Tolerance is relative to the capital at stake: brentq converges on the
    # rate, so the residual NPV scales with project size.
    assert net_present_value(flows, capex, irr) == pytest.approx(0.0, abs=capex * 1e-6)


def test_irr_of_a_known_doubling_case(config):
    # 1,000 out, 1,200 back in a single year -> 20%.
    irr = internal_rate_of_return(np.array([1_200.0]), 1_000.0, config)
    assert irr == pytest.approx(0.20, abs=1e-6)


def test_irr_is_nan_when_the_project_never_pays_back(config):
    # Reporting an IRR here would be meaningless; NaN routes it to the
    # subsidy-gap branch instead.
    irr = internal_rate_of_return(np.full(10, -50.0), 1_000.0, config)
    assert np.isnan(irr)


def test_higher_cash_flows_give_a_higher_irr(config):
    low = internal_rate_of_return(np.full(10, 1_200.0), 9_000.0, config)
    high = internal_rate_of_return(np.full(10, 2_000.0), 9_000.0, config)
    assert high > low


# --- Equation 14 --------------------------------------------------------


def test_discounted_payback_is_longer_than_undiscounted():
    flows = np.full(10, 1_000.0)
    # Undiscounted payback on 4,000 is exactly 4 years.
    assert discounted_payback_period(flows, 4_000.0, 0.10) > 4.0


def test_payback_is_nan_when_capital_is_never_recovered():
    assert np.isnan(discounted_payback_period(np.full(5, 100.0), 10_000.0, 0.10))


def test_payback_interpolates_within_the_recovery_year():
    payback = discounted_payback_period(np.full(10, 1_000.0), 1_500.0, 0.0)
    assert 1.0 < payback < 2.0
    assert payback == pytest.approx(1.5)


# --- Equation 11 and the connection-fee treatment ------------------------


def test_cash_flows_run_for_the_full_analysis_period(config):
    result = build_cash_flows(
        capex=100_000,
        opex=3_000,
        annual_energy_kwh=50_000,
        households=100,
        perspective=config.section("finance.perspectives.utility"),
        config=config,
    )
    assert len(result.cash_flows) == int(config.require("finance.analysis_period_years"))


def test_unsubsidised_connection_fee_offsets_year_zero_capital(config):
    developer = dict(config.section("finance.perspectives.developer"))
    developer["connection_fee_subsidy_share"] = 0.0
    paid_by_household = build_cash_flows(
        capex=100_000,
        opex=3_000,
        annual_energy_kwh=50_000,
        households=100,
        perspective=developer,
        config=config,
        connection_fee_per_household=180.0,
    )
    developer_subsidised = dict(developer, connection_fee_subsidy_share=1.0)
    paid_by_utility = build_cash_flows(
        capex=100_000,
        opex=3_000,
        annual_energy_kwh=50_000,
        households=100,
        perspective=developer_subsidised,
        config=config,
        connection_fee_per_household=180.0,
    )
    # Section 3.5.4: CF_0 = H_c * Fee - CAPEX when the household pays.
    assert paid_by_household.capex_0 == pytest.approx(paid_by_utility.capex_0 - 100 * 180.0)


def test_utilisation_ramp_suppresses_early_revenue(config):
    result = build_cash_flows(
        capex=0.0,
        opex=0.0,
        annual_energy_kwh=50_000,
        households=100,
        perspective=config.section("finance.perspectives.developer"),
        config=config,
    )
    ramp = config.get("finance.cash_flow.utilisation_ramp")
    if ramp and ramp[0] < 1.0:
        assert result.cash_flows[0] < result.cash_flows[3]


def test_collection_efficiency_reduces_revenue(config):
    perspective = dict(config.section("finance.perspectives.developer"))
    full = dict(perspective, collection_efficiency=1.0)
    partial = dict(perspective, collection_efficiency=0.5)
    kwargs = {
        "capex": 0.0,
        "opex": 0.0,
        "annual_energy_kwh": 50_000,
        "households": 100,
        "config": config,
    }
    assert (
        build_cash_flows(perspective=partial, **kwargs).cash_flows[0]
        < build_cash_flows(perspective=full, **kwargs).cash_flows[0]
    )


def test_zero_tariff_yields_negative_cash_flows(config):
    perspective = dict(config.section("finance.perspectives.utility"), tariff_per_kwh=0.0)
    result = build_cash_flows(
        capex=0.0,
        opex=5_000,
        annual_energy_kwh=50_000,
        households=100,
        perspective=perspective,
        config=config,
    )
    assert (result.cash_flows[:-1] < 0).all()


# --- Perspective-level evaluation ---------------------------------------


@pytest.fixture
def selected():
    return pd.DataFrame(
        {
            "settlement_id": ["A", "B"],
            "households": [100.0, 10.0],
            "annual_energy_kwh": [124_100.0, 730.0],
            "least_cost_technology": ["grid", "standalone"],
            "least_cost_capex": [150_000.0, 3_000.0],
            "least_cost_opex": [12_000.0, 150.0],
        }
    )


def test_evaluate_viability_adds_metrics_for_every_perspective(selected, config):
    out = evaluate_viability(selected, config)
    for key in config.section("finance.perspectives"):
        for prefix in ("npv_", "irr_", "dpp_", "viable_", "subsidy_gap_"):
            assert f"{prefix}{key}" in out.columns


def test_subsidy_gap_is_zero_for_viable_and_positive_otherwise(selected, config):
    out = evaluate_viability(selected, config)
    for key in config.section("finance.perspectives"):
        viable = out[f"viable_{key}"]
        assert (out.loc[viable, f"subsidy_gap_{key}"] == 0).all()
        assert (out.loc[~viable, f"subsidy_gap_{key}"] >= 0).all()


def test_higher_tariff_improves_viability(selected, config):
    low = evaluate_viability(selected, config)
    high = evaluate_viability(
        selected, config.with_override_path("finance.perspectives.utility.tariff_per_kwh", 2.0)
    )
    assert high["npv_utility"].sum() > low["npv_utility"].sum()


def test_settlements_failing_both_hurdles_are_flagged_for_public_support(selected, config):
    out = evaluate_viability(selected, config)
    if "requires_public_support" in out.columns:
        expected = ~(out["viable_utility"] | out["viable_developer"])
        assert (out["requires_public_support"] == expected).all()


def test_infeasible_settlement_yields_nan_metrics(config):
    frame = pd.DataFrame(
        {
            "settlement_id": ["none"],
            "households": [5.0],
            "annual_energy_kwh": [0.0],
            "least_cost_technology": ["none"],
            "least_cost_capex": [np.nan],
            "least_cost_opex": [np.nan],
        }
    )
    out = evaluate_viability(frame, config)
    assert np.isnan(out["npv_utility"].iloc[0])
    assert not out["viable_utility"].iloc[0]
