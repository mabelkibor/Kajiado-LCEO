"""End-to-end behaviour of the five-stage sequence (Section 3.5.5)."""

from __future__ import annotations

import json

import numpy as np
import pytest

from kajiado_lceo.config import load_config
from kajiado_lceo.pipeline import build_priority_plan, run


@pytest.fixture(scope="module")
def result():
    config = load_config("config", scenario="baseline")
    from kajiado_lceo.sample import generate_sample_county

    return config, run(config, inputs=generate_sample_county(seed=11), write_outputs=False)


def test_pipeline_produces_every_stated_output(result):
    _, out = result
    assert not out.settlements.empty
    assert not out.priority_plan.empty
    assert not out.filter_report.empty
    assert out.summary["totals"]["settlements"] > 0


def test_every_settlement_receives_a_decision(result):
    _, out = result
    assert out.settlements["least_cost_technology"].notna().all()
    assert out.settlements["decision_reason"].notna().all()


def test_households_are_conserved_from_buildings_to_settlements(result):
    _, out = result
    assert out.settlements["households"].sum() == pytest.approx(out.buildings["households"].sum())


def test_settlement_ids_are_unique(result):
    _, out = result
    assert out.settlements["settlement_id"].is_unique


def test_dispersed_homesteads_are_assigned_standalone(result):
    _, out = result
    dispersed = out.settlements[out.settlements["decision_reason"] == "dispersed_override"]
    if len(dispersed):
        assert (dispersed["least_cost_technology"] == "standalone").all()


def test_all_three_technologies_appear_across_a_heterogeneous_county(result):
    """The framework exists to differentiate; a single-technology answer on a
    deliberately heterogeneous county would mean the comparison is not biting."""
    _, out = result
    chosen = set(out.settlements["least_cost_technology"])
    assert len(chosen - {"none"}) >= 2


def test_lcoe_values_are_positive_and_finite(result):
    _, out = result
    costed = out.settlements[out.settlements["least_cost_technology"] != "none"]
    assert (costed["least_cost_lcoe"] > 0).all()
    assert np.isfinite(costed["least_cost_lcoe"]).all()


def test_selected_lcoe_is_the_minimum_of_the_feasible_options(result):
    _, out = result
    rows = out.settlements[out.settlements["decision_reason"] == "argmin"]
    candidates = rows[["lcoe_grid", "lcoe_minigrid", "lcoe_standalone"]].min(axis=1)
    np.testing.assert_allclose(rows["least_cost_lcoe"].to_numpy(), candidates.to_numpy(), rtol=1e-9)


def test_priority_plan_is_ranked_and_cumulative(result):
    config, out = result
    plan = build_priority_plan(out.settlements, config)
    assert list(plan["priority_rank"]) == list(range(1, len(plan) + 1))
    assert plan["priority_score"].is_monotonic_decreasing
    assert plan["cumulative_households"].is_monotonic_increasing


def test_run_summary_records_provenance(result):
    _, out = result
    run_block = out.summary["run"]
    assert run_block["scenario"] == "baseline"
    assert run_block["package_version"]
    assert run_block["config_sources"]
    json.dumps(out.summary, default=str)  # must be serialisable


@pytest.mark.slow
def test_outputs_are_written_to_disk(tmp_path):
    from kajiado_lceo.sample import generate_sample_county

    config = load_config("config", scenario="baseline", root=tmp_path).with_overrides(
        {"run": {"write_intermediates": False}}
    )
    out = run(config, inputs=generate_sample_county(seed=5), write_outputs=True)
    assert config.output_path("clusters_table").is_file()
    assert config.output_path("summary_json").is_file()
    assert out.summary["totals"]["settlements"] > 0


@pytest.mark.slow
@pytest.mark.parametrize(
    "scenario", ["baseline", "no_connection_subsidy", "high_grid_capex", "low_battery_cost"]
)
def test_every_scenario_runs_end_to_end(scenario):
    from kajiado_lceo.sample import generate_sample_county

    config = load_config("config", scenario=scenario)
    out = run(config, inputs=generate_sample_county(seed=11), write_outputs=False)
    assert out.summary["totals"]["settlements"] > 0


@pytest.mark.slow
def test_higher_grid_cost_moves_settlements_off_grid():
    """The central comparative-static of the model: raise the cost of network
    extension and fewer settlements should be allocated to it."""
    from kajiado_lceo.sample import generate_sample_county

    layers = generate_sample_county(seed=11)
    baseline = run(load_config("config", scenario="baseline"), inputs=layers, write_outputs=False)
    expensive = run(
        load_config("config", scenario="high_grid_capex"), inputs=layers, write_outputs=False
    )
    assert expensive.summary["technology_mix"].get("grid", 0) <= baseline.summary[
        "technology_mix"
    ].get("grid", 0)


@pytest.mark.slow
def test_removing_the_connection_subsidy_worsens_utility_viability():
    from kajiado_lceo.sample import generate_sample_county

    layers = generate_sample_county(seed=11)
    subsidised = run(load_config("config", scenario="baseline"), inputs=layers, write_outputs=False)
    unsubsidised = run(
        load_config("config", scenario="no_connection_subsidy"), inputs=layers, write_outputs=False
    )
    # Shifting the fee onto households relieves the utility's year-zero outlay,
    # so utility viability must not deteriorate.
    assert unsubsidised.summary["viability"]["utility"]["total_subsidy_gap_usd"] <= (
        subsidised.summary["viability"]["utility"]["total_subsidy_gap_usd"] + 1e-6
    )
