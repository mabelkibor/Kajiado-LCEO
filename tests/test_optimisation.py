"""Equation 10 — the least-cost decision rule and the dispersed-settlement override."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kajiado_lceo.clustering.typology import assign_typology
from kajiado_lceo.demand.tiers import estimate_demand
from kajiado_lceo.optimisation.least_cost import compare_technologies, select_least_cost


@pytest.fixture
def compared(toy_settlements, config):
    prepared = estimate_demand(assign_typology(toy_settlements, config), config)
    return compare_technologies(prepared, config)


def _selected(rows: dict, config) -> pd.DataFrame:
    """Build a one-row frame with LCOEs set directly, to test the rule alone.

    Cost columns the caller does not supply are filled with placeholders, so a
    test can state only the LCOEs it cares about.
    """
    frame = pd.DataFrame([rows])
    for column in (
        "capex_grid",
        "capex_minigrid",
        "capex_standalone",
        "opex_grid",
        "opex_minigrid",
        "opex_standalone",
    ):
        if column not in frame.columns:
            frame[column] = 1.0
    return select_least_cost(frame, config)


def test_all_three_technologies_are_costed(compared):
    for column in ("lcoe_grid", "lcoe_minigrid", "lcoe_standalone"):
        assert column in compared.columns


def test_argmin_picks_the_cheapest_option(config):
    out = _selected(
        {
            "settlement_id": "X",
            "is_dispersed": False,
            "is_micro_cluster": False,
            "lcoe_grid": 0.50,
            "lcoe_minigrid": 0.30,
            "lcoe_standalone": 0.90,
            "capex_grid": 1.0,
            "capex_minigrid": 2.0,
            "capex_standalone": 3.0,
            "opex_grid": 0.1,
            "opex_minigrid": 0.2,
            "opex_standalone": 0.3,
        },
        config,
    )
    assert out["least_cost_technology"].iloc[0] == "minigrid"
    assert out["decision_reason"].iloc[0] == "argmin"
    assert out["least_cost_lcoe"].iloc[0] == pytest.approx(0.30)


def test_selected_capex_matches_the_selected_technology(config):
    out = _selected(
        {
            "settlement_id": "X",
            "is_dispersed": False,
            "is_micro_cluster": False,
            "lcoe_grid": 0.50,
            "lcoe_minigrid": 0.30,
            "lcoe_standalone": 0.90,
            "capex_grid": 10.0,
            "capex_minigrid": 20.0,
            "capex_standalone": 30.0,
            "opex_grid": 1.0,
            "opex_minigrid": 2.0,
            "opex_standalone": 3.0,
        },
        config,
    )
    assert out["least_cost_capex"].iloc[0] == 20.0
    assert out["least_cost_opex"].iloc[0] == 2.0


def test_infeasible_options_are_skipped_not_ranked_last(config):
    out = _selected(
        {
            "settlement_id": "X",
            "is_dispersed": False,
            "is_micro_cluster": False,
            "lcoe_grid": np.nan,
            "lcoe_minigrid": 0.60,
            "lcoe_standalone": 0.80,
        },
        config,
    )
    assert out["least_cost_technology"].iloc[0] == "minigrid"


def test_no_feasible_option_is_recorded_rather_than_defaulted(config):
    out = _selected(
        {
            "settlement_id": "X",
            "is_dispersed": False,
            "is_micro_cluster": False,
            "lcoe_grid": np.nan,
            "lcoe_minigrid": np.nan,
            "lcoe_standalone": np.nan,
        },
        config,
    )
    assert out["least_cost_technology"].iloc[0] == "none"
    assert out["decision_reason"].iloc[0] == "no_feasible_option"


def test_dispersed_homestead_takes_the_standalone_override(config):
    # Even where grid is nominally cheapest, an isolated homestead defaults to
    # SHS per Equation 10's override.
    out = _selected(
        {
            "settlement_id": "D1",
            "is_dispersed": True,
            "is_micro_cluster": False,
            "lcoe_grid": 0.10,
            "lcoe_minigrid": 0.20,
            "lcoe_standalone": 0.90,
        },
        config,
    )
    assert out["least_cost_technology"].iloc[0] == "standalone"
    assert out["decision_reason"].iloc[0] == "dispersed_override"


def test_micro_cluster_is_decided_by_comparison_not_by_override(config):
    # Section 3.5.4: the dispersed treatment must be a tested outcome.
    out = _selected(
        {
            "settlement_id": "M1",
            "is_dispersed": True,
            "is_micro_cluster": True,
            "lcoe_grid": np.nan,
            "lcoe_minigrid": 0.40,
            "lcoe_standalone": 0.85,
        },
        config,
    )
    assert out["least_cost_technology"].iloc[0] == "minigrid"
    assert out["decision_reason"].iloc[0] == "micro_cluster_comparison"


def test_micro_cluster_can_take_grid_when_allowed_and_cheapest(config):
    out = _selected(
        {
            "settlement_id": "M2",
            "is_dispersed": True,
            "is_micro_cluster": True,
            "lcoe_grid": 0.20,
            "lcoe_minigrid": 0.55,
            "lcoe_standalone": 0.60,
        },
        config,
    )
    assert out["least_cost_technology"].iloc[0] == "grid"


def test_disabling_micro_cluster_grid_reproduces_the_literal_two_way_rule(config):
    strict = config.with_override_path("clustering.micro_cluster_allows_grid", False)
    out = _selected(
        {
            "settlement_id": "M2",
            "is_dispersed": True,
            "is_micro_cluster": True,
            "lcoe_grid": 0.20,
            "lcoe_minigrid": 0.55,
            "lcoe_standalone": 0.60,
        },
        strict,
    )
    assert out["least_cost_technology"].iloc[0] == "minigrid"


def test_lcoe_margin_reports_the_gap_to_the_runner_up(config):
    out = _selected(
        {
            "settlement_id": "X",
            "is_dispersed": False,
            "is_micro_cluster": False,
            "lcoe_grid": 0.50,
            "lcoe_minigrid": 0.30,
            "lcoe_standalone": 0.90,
        },
        config,
    )
    assert out["lcoe_margin"].iloc[0] == pytest.approx(0.20)


def test_near_settlement_takes_grid_and_remote_village_does_not(compared, config):
    out = select_least_cost(compared, config)
    assert out.loc[0, "least_cost_technology"] == "grid", "0.8 km from MV, 150 households"
    assert out.loc[1, "least_cost_technology"] != "grid", "45 km from MV"
    assert out.loc[2, "least_cost_technology"] == "standalone", "isolated homestead"


def test_higher_grid_capex_shifts_settlements_off_grid(compared, config):
    baseline = select_least_cost(compared, config)
    expensive_cfg = config.with_override_path("technologies.grid.cost_mv_per_km", 500_000.0)
    expensive = select_least_cost(compare_technologies(compared, expensive_cfg), expensive_cfg)
    assert (expensive["least_cost_technology"] == "grid").sum() <= (
        baseline["least_cost_technology"] == "grid"
    ).sum()


def test_deployment_months_are_attached_for_the_selected_technology(compared, config):
    out = select_least_cost(compared, config)
    assert out["deployment_months"].notna().all()
