"""Configuration loading, merging and scenario overlays."""

from __future__ import annotations

import pytest

from kajiado_lceo.config import Config, deep_merge, load_config


def test_deep_merge_is_recursive_and_non_mutating():
    base = {"a": {"b": 1, "c": 2}, "d": 3}
    overlay = {"a": {"c": 99}}
    merged = deep_merge(base, overlay)
    assert merged == {"a": {"b": 1, "c": 99}, "d": 3}
    assert base["a"]["c"] == 2, "deep_merge must not mutate its inputs"


def test_deep_merge_replaces_lists_wholesale():
    # A scenario that redefines a list replaces it; it does not append.
    merged = deep_merge({"x": [1, 2, 3]}, {"x": [9]})
    assert merged["x"] == [9]


def test_includes_are_resolved(config):
    # Keys from every component file must be present after the include pass.
    assert config.get("clustering.eps_m") is not None  # clustering.yaml
    assert config.get("demand.tiers.tier_2") is not None  # demand_tiers.yaml
    assert config.get("technologies.grid") is not None  # techno_economic.yaml
    assert config.get("finance.discount_rate") is not None  # finance.yaml


def test_dotted_access_and_require():
    cfg = Config(data={"a": {"b": {"c": 5}}})
    assert cfg.get("a.b.c") == 5
    assert cfg.get("a.b.missing", "fallback") == "fallback"
    assert cfg.require("a.b.c") == 5
    with pytest.raises(KeyError, match=r"a\.b\.missing"):
        cfg.require("a.b.missing")


def test_scenario_overlay_changes_only_the_named_parameters():
    baseline = load_config("config", scenario="baseline")
    scenario = load_config("config", scenario="high_grid_capex")

    assert scenario.get("technologies.grid.cost_mv_per_km") > baseline.get(
        "technologies.grid.cost_mv_per_km"
    )
    # Untouched parameters must survive the overlay.
    assert scenario.get("finance.discount_rate") == baseline.get("finance.discount_rate")
    assert scenario.get("demand.tiers.tier_3.kwh_per_household_day") == baseline.get(
        "demand.tiers.tier_3.kwh_per_household_day"
    )


def test_unknown_scenario_raises_with_a_useful_message():
    with pytest.raises(FileNotFoundError, match="not found"):
        load_config("config", scenario="does_not_exist")


def test_override_path_creates_nested_keys(config):
    variant = config.with_override_path("technologies.grid.cost_mv_per_km", 1.0)
    assert variant.get("technologies.grid.cost_mv_per_km") == 1.0
    # The original is untouched: Config is immutable by contract.
    assert config.get("technologies.grid.cost_mv_per_km") != 1.0


@pytest.mark.parametrize(
    "scenario",
    ["baseline", "no_connection_subsidy", "high_grid_capex", "low_battery_cost", "productive_use"],
)
def test_every_shipped_scenario_loads(scenario):
    cfg = load_config("config", scenario=scenario)
    assert cfg.scenario == scenario
    assert cfg.get("scenario.id") == scenario
