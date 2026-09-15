"""Equation 10 — the least-cost decision rule and the dispersed-settlement override.

For any settlement that satisfies the density condition of Equation 2::

    Technology*_c = argmin over i in {grid, mg, shs} of LCOE_i,c

For building points labelled noise under Equation 2 — dispersed pastoralist
homesteads whose inter-dwelling spacing exceeds the clustering radius — the
proposal applies an override to standalone PV, because grid and mini-grid
distribution cost per household rises sharply at that spacing.

Critically, the override is *tested, not assumed* (Section 3.5.4). Before it is
applied, noise points are re-clustered at a relaxed radius of 300-500 m
(:func:`~kajiado_lceo.clustering.dbscan.micro_cluster_noise`). Where two or more
noise points form such a micro-cluster, this module still computes and compares
the LCOE of a short single-line micro-mini-grid against aggregated SHS for the
same households, and assigns whichever is cheaper. Only a genuinely isolated
homestead — no micro-cluster partner at all — takes the standalone default
without a comparison, and even then the reason is recorded in
``decision_reason`` so the share of settlements decided by override rather than
by comparison can be reported.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from kajiado_lceo.config import Config
from kajiado_lceo.costs.annualisation import npc_lcoe
from kajiado_lceo.costs.grid import grid_capex, grid_opex
from kajiado_lceo.costs.minigrid import minigrid_capex, minigrid_opex, minigrid_replacements
from kajiado_lceo.costs.standalone import (
    standalone_capex,
    standalone_opex,
    standalone_replacements,
)
from kajiado_lceo.logging_setup import get_logger

logger = get_logger(__name__)

TECHNOLOGIES = ("grid", "minigrid", "standalone")

# Column prefixes this module generates. Dropped before recomputation so that
# costing the same settlement frame twice — as a sensitivity sweep does — is
# idempotent rather than a join conflict.
_GENERATED_PREFIXES = (
    "grid_",
    "mg_",
    "shs_",
    "capex_",
    "opex_",
    "npc_",
    "lcoe_",
    "least_cost_",
)
_GENERATED_COLUMNS = ("decision_reason", "deployment_months")


def _drop_generated_columns(settlements: pd.DataFrame) -> pd.DataFrame:
    """Return a copy without the columns this module is about to (re)create."""
    stale = [
        column
        for column in settlements.columns
        if column.startswith(_GENERATED_PREFIXES) or column in _GENERATED_COLUMNS
    ]
    return settlements.drop(columns=stale).copy()


def compare_technologies(settlements: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Compute CAPEX, OPEX, NPC and LCOE for all three technologies.

    Returns a copy of ``settlements`` with ``capex_*``, ``opex_*``, ``npc_*``
    and ``lcoe_*`` columns for grid, mini-grid and standalone, together with the
    component-level cost breakdown that Equations 5-7 produce.
    """
    df = _drop_generated_columns(settlements)
    discount_rate = float(config.require("finance.discount_rate"))
    period = int(config.require("finance.analysis_period_years"))
    salvage = float(config.get("finance.cash_flow.salvage_fraction", 0.0))
    opex_escalation = float(config.get("finance.cash_flow.opex_escalation", 0.0))
    growth = float(config.get("demand.annual_growth_rate", 0.0))
    energy = df["annual_energy_kwh"]

    enabled = {t: bool(config.get(f"technologies.{t}.enabled", True)) for t in TECHNOLOGIES}

    # --- grid extension (Equation 5) ---------------------------------
    if enabled["grid"]:
        grid_terms = grid_capex(df, config).add_prefix("grid_")
        df = df.join(grid_terms)
        df["capex_grid"] = grid_terms["grid_capex_grid"]
        df["opex_grid"] = grid_opex(df["capex_grid"], energy, config)
        df["lcoe_grid"], df["npc_grid"] = npc_lcoe(
            df["capex_grid"],
            df["opex_grid"],
            energy,
            discount_rate,
            period,
            replacements=None,
            salvage_fraction=salvage,
            opex_escalation=opex_escalation,
            demand_growth=growth,
        )
    else:
        df["capex_grid"] = df["opex_grid"] = df["npc_grid"] = df["lcoe_grid"] = np.nan

    # --- solar PV mini-grid (Equation 6) ------------------------------
    if enabled["minigrid"]:
        mg_terms = minigrid_capex(df, config).add_prefix("mg_")
        df = df.join(mg_terms)
        df["capex_minigrid"] = mg_terms["mg_capex_minigrid"]
        df["opex_minigrid"] = minigrid_opex(df["capex_minigrid"], config)
        mg_replacements = minigrid_replacements(
            mg_terms.rename(columns=lambda c: c.removeprefix("mg_")), config
        )
        df["lcoe_minigrid"], df["npc_minigrid"] = npc_lcoe(
            df["capex_minigrid"],
            df["opex_minigrid"],
            energy,
            discount_rate,
            period,
            replacements=mg_replacements,
            salvage_fraction=salvage,
            opex_escalation=opex_escalation,
            demand_growth=growth,
        )
    else:
        df["capex_minigrid"] = df["opex_minigrid"] = df["npc_minigrid"] = df["lcoe_minigrid"] = (
            np.nan
        )

    # --- standalone solar PV (Equation 7) -----------------------------
    if enabled["standalone"]:
        shs_terms = standalone_capex(df, config).add_prefix("shs_")
        df = df.join(shs_terms)
        df["capex_standalone"] = shs_terms["shs_capex_standalone"]
        df["opex_standalone"] = standalone_opex(df["capex_standalone"], config)
        df["lcoe_standalone"], df["npc_standalone"] = npc_lcoe(
            df["capex_standalone"],
            df["opex_standalone"],
            energy,
            discount_rate,
            period,
            replacements=standalone_replacements(df, config),
            salvage_fraction=salvage,
            opex_escalation=opex_escalation,
            demand_growth=growth,
        )
    else:
        df["capex_standalone"] = df["opex_standalone"] = df["npc_standalone"] = df[
            "lcoe_standalone"
        ] = np.nan

    return df


def select_least_cost(settlements: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Apply Equation 10, including the dispersed-settlement override.

    Adds:
        ``least_cost_technology``  the selected option
        ``least_cost_lcoe``        its LCOE
        ``decision_reason``        ``argmin`` | ``micro_cluster_comparison``
                                   | ``dispersed_override`` | ``no_feasible_option``
        ``lcoe_margin``            LCOE gap to the runner-up, i.e. how robust
                                   the choice is to parameter error
    """
    df = settlements.copy()
    lcoe_columns = {
        "grid": "lcoe_grid",
        "minigrid": "lcoe_minigrid",
        "standalone": "lcoe_standalone",
    }
    matrix = df[[lcoe_columns[t] for t in TECHNOLOGIES]].to_numpy(dtype=float)

    micro_cluster_allows_grid = bool(config.get("clustering.micro_cluster_allows_grid", True))
    is_dispersed = df.get("is_dispersed", pd.Series(False, index=df.index)).to_numpy(dtype=bool)
    is_micro = df.get("is_micro_cluster", pd.Series(False, index=df.index)).to_numpy(dtype=bool)

    technologies: list[str] = []
    values: list[float] = []
    reasons: list[str] = []
    margins: list[float] = []

    for row_index in range(len(df)):
        row = matrix[row_index]
        finite = np.isfinite(row)

        if not finite.any():
            # No option is costable — usually zero modelled demand. Recorded
            # rather than silently defaulted, so it shows up in the run summary.
            technologies.append("none")
            values.append(np.nan)
            reasons.append("no_feasible_option")
            margins.append(np.nan)
            continue

        candidates = row.copy()
        if is_dispersed[row_index] and not is_micro[row_index]:
            # An isolated homestead: Equation 10's override. Grid and mini-grid
            # are not compared because neither is a credible single-dwelling
            # option at this spacing.
            technologies.append("standalone")
            values.append(float(row[TECHNOLOGIES.index("standalone")]))
            reasons.append("dispersed_override")
            margins.append(np.nan)
            continue

        if is_micro[row_index]:
            # Micro-cluster: the proposal's tested case. Micro-mini-grid competes
            # against aggregated SHS on LCOE rather than being assumed away.
            # Whether grid extension stays in that comparison is configurable:
            # excluding it is the literal reading of Section 3.5.4, but a micro-
            # cluster that happens to sit beside an existing MV line is then
            # denied the cheapest option by assumption rather than by evidence.
            # Default is to leave grid in and let Equation 10 decide.
            if not micro_cluster_allows_grid:
                candidates[TECHNOLOGIES.index("grid")] = np.nan
            reason = "micro_cluster_comparison"
        else:
            reason = "argmin"

        if not np.isfinite(candidates).any():
            candidates = row.copy()
            reason = "argmin"

        best = int(np.nanargmin(candidates))
        technologies.append(TECHNOLOGIES[best])
        values.append(float(candidates[best]))
        reasons.append(reason)

        others = np.delete(candidates, best)
        others = others[np.isfinite(others)]
        margins.append(float(others.min() - candidates[best]) if others.size else np.nan)

    df["least_cost_technology"] = technologies
    df["least_cost_lcoe"] = values
    df["decision_reason"] = reasons
    df["lcoe_margin"] = margins

    df["least_cost_capex"] = [
        df.at[idx, f"capex_{tech}"] if tech in TECHNOLOGIES else np.nan
        for idx, tech in zip(df.index, df["least_cost_technology"], strict=True)
    ]
    df["least_cost_opex"] = [
        df.at[idx, f"opex_{tech}"] if tech in TECHNOLOGIES else np.nan
        for idx, tech in zip(df.index, df["least_cost_technology"], strict=True)
    ]
    df["deployment_months"] = [
        float(config.get(f"technologies.{tech}.deployment_months", np.nan))
        if tech in TECHNOLOGIES
        else np.nan
        for tech in df["least_cost_technology"]
    ]

    counts = df["least_cost_technology"].value_counts().to_dict()
    logger.info("least-cost selection (Equation 10): %s", counts)
    return df
