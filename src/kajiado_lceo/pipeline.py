"""Section 3.5.5 — the full modelling sequence, from inputs to outputs.

Five linked stages, each taking a defined input, applying the governing
equations of Section 3.5.3, and producing the input to the next:

    Stage 1  spatial pre-processing and filtering      Section 3.4.3, Table 3.3
    Stage 2  settlement clustering                     Equations 1-2
    Stage 3  demand-tier estimation                    Equations 3-4
    Stage 4  least-cost technology optimisation        Equations 5-10
    Stage 5  financial viability assessment            Equations 11-14

The five outputs the proposal specifies — the settlement clusters, their demand,
their least-cost technology and LCOE, their dual-perspective viability, and the
prioritised county electrification plan — are all produced by :func:`run`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from kajiado_lceo.clustering import assign_typology, cluster_buildings, micro_cluster_noise
from kajiado_lceo.clustering.dbscan import summarise_clusters
from kajiado_lceo.config import Config
from kajiado_lceo.demand import estimate_demand
from kajiado_lceo.finance import evaluate_viability
from kajiado_lceo.io.loaders import load_inputs
from kajiado_lceo.io.writers import build_run_summary, write_run_summary, write_table
from kajiado_lceo.logging_setup import get_logger
from kajiado_lceo.optimisation import compare_technologies, select_least_cost
from kajiado_lceo.preprocessing import filter_footprints, filter_summary, tag_served_buildings

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Everything one model run produces, in memory."""

    buildings: pd.DataFrame
    settlements: pd.DataFrame
    priority_plan: pd.DataFrame
    filter_report: pd.DataFrame
    summary: dict[str, Any] = field(default_factory=dict)


def run(
    config: Config,
    inputs: dict[str, Any] | None = None,
    write_outputs: bool = True,
) -> PipelineResult:
    """Execute Stages 1-5 and, optionally, write the output tables.

    Args:
        config: merged configuration, including the scenario overlay.
        inputs: pre-loaded layers; loaded from disk when omitted.
        write_outputs: write tables and the run summary to ``outputs/``.

    Returns:
        A :class:`PipelineResult` holding the building-level table, the
        settlement-level results, the prioritised plan and the run summary.
    """
    layers = inputs if inputs is not None else load_inputs(config)
    interim_dir = config.path("interim") if config.get("run.write_intermediates", False) else None

    # -- Stage 1: pre-processing and filtering -------------------------
    logger.info("Stage 1/5 — structure filtering and served-status tagging")
    buildings = filter_footprints(layers["buildings"], config)
    report = filter_summary(buildings)
    buildings = tag_served_buildings(
        buildings[buildings["is_dwelling"]].copy(),
        mv_lines=layers.get("mv_lines"),
        lv_lines=layers.get("lv_lines"),
        transformers=layers.get("transformers"),
        meters=layers.get("meters"),
        config=config,
    )
    unelectrified = buildings[~buildings["is_served"]].copy()
    logger.info("Stage 1 complete: %d unelectrified dwellings carried forward", len(unelectrified))
    _maybe_write(interim_dir, "stage1_buildings.csv", buildings)

    if unelectrified.empty:
        raise ValueError(
            "no unelectrified dwellings remain after Stage 1 — check the "
            "electrification_status buffers in config/clustering.yaml"
        )

    # -- Stage 2: clustering (Equations 1-2) ---------------------------
    logger.info("Stage 2/5 — DBSCAN settlement clustering")
    clustered = cluster_buildings(unelectrified, config)
    clustered = micro_cluster_noise(clustered, config)
    settlements = summarise_clusters(clustered, config)
    settlements = assign_typology(settlements, config)
    settlements = _attach_transformer_capacity(settlements, clustered)
    _maybe_write(interim_dir, "stage2_clustered_buildings.csv", clustered)

    # -- Stage 3: demand (Equations 3-4) -------------------------------
    logger.info("Stage 3/5 — demand-tier estimation")
    settlements = estimate_demand(settlements, config)
    _maybe_write(interim_dir, "stage3_demand.csv", settlements)

    # -- Stage 4: least-cost optimisation (Equations 5-10) -------------
    logger.info("Stage 4/5 — technology costing and least-cost selection")
    settlements = compare_technologies(settlements, config)
    settlements = select_least_cost(settlements, config)
    _maybe_write(interim_dir, "stage4_least_cost.csv", settlements)

    # -- Stage 5: financial viability (Equations 11-14) ----------------
    logger.info("Stage 5/5 — dual-perspective financial appraisal")
    settlements = evaluate_viability(settlements, config)

    priority_plan = build_priority_plan(settlements, config)
    summary = build_run_summary(settlements, config)

    if write_outputs:
        write_table(settlements, config.output_path("clusters_table"))
        write_table(
            settlements[_technology_columns(settlements)],
            config.output_path("technology_table"),
        )
        write_table(settlements[_finance_columns(settlements)], config.output_path("finance_table"))
        write_table(priority_plan, config.output_path("priority_table"))
        write_run_summary(summary, config.output_path("summary_json"))
        write_table(report, config.path("tables") / "structure_filter_report.csv")

    return PipelineResult(
        buildings=clustered,
        settlements=settlements,
        priority_plan=priority_plan,
        filter_report=report,
        summary=summary,
    )


def build_priority_plan(settlements: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Output (v) of Section 3.5.5 — the prioritised county electrification plan.

    Settlements are ranked on a transparent composite of the three criteria the
    proposal names: cost efficiency (LCOE), financial viability (utility NPV per
    household), and deployment time-effectiveness (months to energisation). Each
    criterion is min-max normalised so no single unit dominates, and the weights
    are visible here rather than buried, because the ranking is a policy
    judgement the county must be able to interrogate and change.
    """
    df = settlements.copy()
    weights = config.section("prioritisation") or {
        "weight_lcoe": 0.4,
        "weight_viability": 0.35,
        "weight_speed": 0.25,
    }

    lcoe_score = 1.0 - _min_max(df["least_cost_lcoe"])  # lower LCOE is better
    speed_score = 1.0 - _min_max(df["deployment_months"])  # faster is better
    npv_per_household = df.get("npv_utility", pd.Series(0.0, index=df.index)) / df[
        "households"
    ].replace(0, np.nan)
    viability_score = _min_max(npv_per_household)

    df["priority_score"] = (
        float(weights.get("weight_lcoe", 0.4)) * lcoe_score
        + float(weights.get("weight_viability", 0.35)) * viability_score
        + float(weights.get("weight_speed", 0.25)) * speed_score
    )
    df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)
    df["priority_rank"] = np.arange(1, len(df) + 1)
    df["cumulative_households"] = df["households"].cumsum()
    df["cumulative_capex_usd"] = df["least_cost_capex"].cumsum()

    columns = [
        "priority_rank",
        "settlement_id",
        "typology",
        "households",
        "demand_tier",
        "annual_energy_kwh",
        "distance_to_mv_km",
        "least_cost_technology",
        "least_cost_lcoe",
        "least_cost_capex",
        "deployment_months",
        "npv_utility",
        "irr_utility",
        "npv_developer",
        "irr_developer",
        "requires_public_support",
        "priority_score",
        "cumulative_households",
        "cumulative_capex_usd",
    ]
    return df[[c for c in columns if c in df.columns]]


def _min_max(series: pd.Series) -> pd.Series:
    """Scale a series to [0, 1]; a constant series maps to 0.5 (no signal)."""
    values = pd.to_numeric(series, errors="coerce")
    low, high = values.min(skipna=True), values.max(skipna=True)
    if not np.isfinite(low) or not np.isfinite(high) or high - low < 1e-12:
        return pd.Series(0.5, index=series.index)
    return ((values - low) / (high - low)).fillna(0.5)


def _attach_transformer_capacity(
    settlements: pd.DataFrame, buildings: pd.DataFrame
) -> pd.DataFrame:
    """Carry the best available spare transformer capacity up to the settlement."""
    if "nearest_transformer_spare_kva" not in buildings.columns:
        settlements["nearest_transformer_spare_kva"] = 0.0
        return settlements
    spare = (
        buildings.groupby("settlement_id")["nearest_transformer_spare_kva"]
        .max()
        .rename("nearest_transformer_spare_kva")
    )
    return settlements.merge(spare, on="settlement_id", how="left")


def _technology_columns(df: pd.DataFrame) -> list[str]:
    base = [
        "settlement_id",
        "typology",
        "households",
        "demand_tier",
        "annual_energy_kwh",
        "peak_demand_kw",
        "distance_to_mv_km",
        "capex_grid",
        "capex_minigrid",
        "capex_standalone",
        "lcoe_grid",
        "lcoe_minigrid",
        "lcoe_standalone",
        "least_cost_technology",
        "least_cost_lcoe",
        "lcoe_margin",
        "decision_reason",
    ]
    return [c for c in base if c in df.columns]


def _finance_columns(df: pd.DataFrame) -> list[str]:
    base = [
        "settlement_id",
        "typology",
        "households",
        "least_cost_technology",
        "least_cost_capex",
        "least_cost_opex",
        "least_cost_lcoe",
    ]
    base += [
        c for c in df.columns if c.startswith(("npv_", "irr_", "dpp_", "viable_", "subsidy_gap_"))
    ]
    base += ["requires_public_support"]
    return [c for c in base if c in df.columns]


def _maybe_write(directory: Path | None, name: str, df: pd.DataFrame) -> None:
    if directory is not None:
        write_table(df, directory / name)
