"""Result figures.

Four figures carry the analysis of Section 3.7:

1. **LCOE against distance to the MV network** — the crossover chart. This is
   the single most informative output of the whole model: it shows the distance
   at which grid extension stops being the least-cost option for each settlement
   size, which is exactly the evidence a county planner needs.
2. **Technology mix by settlement typology** — how the recommendation varies
   across the heterogeneity the study is built around.
3. **CAPEX composition** — where the money goes, including the connection-fee
   term that Section 3.5.4 singles out.
4. **Viability scatter** — IRR against LCOE, split by perspective, separating
   the developer-bankable pipeline from the settlements needing public support.

A non-interactive Matplotlib backend is selected so figures render on a headless
machine or in CI.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from kajiado_lceo.config import Config
from kajiado_lceo.logging_setup import get_logger

logger = get_logger(__name__)

TECHNOLOGY_COLOURS = {
    "grid": "#1f4e79",
    "minigrid": "#e08214",
    "standalone": "#2e8b57",
    "none": "#999999",
}
TECHNOLOGY_LABELS = {
    "grid": "Grid extension",
    "minigrid": "Solar PV mini-grid",
    "standalone": "Standalone solar PV",
    "none": "No feasible option",
}


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.info("wrote figure %s", path)
    return path


def plot_lcoe_by_distance(settlements: pd.DataFrame, path: Path) -> Path:
    """LCOE of each technology against distance to the MV network."""
    fig, ax = plt.subplots(figsize=(8, 5))
    finite = settlements[np.isfinite(settlements["distance_to_mv_km"])]
    series = [
        ("lcoe_grid", "grid"),
        ("lcoe_minigrid", "minigrid"),
        ("lcoe_standalone", "standalone"),
    ]
    for column, technology in series:
        if column not in finite.columns:
            continue
        ax.scatter(
            finite["distance_to_mv_km"],
            finite[column],
            s=12,
            alpha=0.5,
            label=TECHNOLOGY_LABELS[technology],
            color=TECHNOLOGY_COLOURS[technology],
            edgecolors="none",
        )
    ax.set_xlabel("Distance to nearest MV line, $D_c$ (km)")
    ax.set_ylabel("LCOE (USD/kWh)")
    ax.set_title("Levelized cost by technology and distance to network (Equations 5-9)")
    ax.set_yscale("log")
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(frameon=False)
    return _save(fig, path)


def plot_technology_mix(settlements: pd.DataFrame, path: Path) -> Path:
    """Stacked share of least-cost technology by settlement typology."""
    pivot = settlements.pivot_table(
        index="typology",
        columns="least_cost_technology",
        values="settlement_id",
        aggfunc="count",
    ).fillna(0)
    shares = pivot.div(pivot.sum(axis=1).replace(0, np.nan), axis=0)

    fig, ax = plt.subplots(figsize=(8, 5))
    bottom = np.zeros(len(shares))
    for technology in shares.columns:
        values = shares[technology].to_numpy(dtype=float)
        ax.bar(
            shares.index,
            values,
            bottom=bottom,
            label=TECHNOLOGY_LABELS.get(str(technology), str(technology)),
            color=TECHNOLOGY_COLOURS.get(str(technology), "#777777"),
        )
        bottom += values
    ax.set_ylabel("Share of settlements")
    ax.set_xlabel("Settlement typology")
    ax.set_title("Least-cost technology by settlement typology (Equation 10)")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)
    return _save(fig, path)


def plot_capex_breakdown(settlements: pd.DataFrame, path: Path) -> Path:
    """Total CAPEX by cost component for the selected technologies."""
    components = {
        "MV line": "grid_cost_mv",
        "LV network": "grid_cost_lv",
        "Transformers": "grid_cost_transformers",
        "Grid connections": "grid_cost_connections",
        "PV array": "mg_cost_pv",
        "Battery": "mg_cost_battery",
        "Inverter": "mg_cost_inverter",
        "Mini-grid distribution": "mg_cost_distribution",
        "SHS kits": "shs_capex_standalone",
    }
    selected = settlements["least_cost_technology"]
    totals: dict[str, float] = {}
    for label, column in components.items():
        if column not in settlements.columns:
            continue
        prefix = column.split("_")[0]
        technology = {"grid": "grid", "mg": "minigrid", "shs": "standalone"}[prefix]
        mask = selected == technology
        value = float(settlements.loc[mask, column].sum(skipna=True))
        if value > 0:
            totals[label] = value

    fig, ax = plt.subplots(figsize=(8, 5))
    labels = list(totals)
    values = [totals[k] / 1e6 for k in labels]
    ax.barh(labels, values, color="#1f4e79")
    ax.set_xlabel("CAPEX (USD millions)")
    ax.set_title("Capital cost composition of the least-cost plan (Equations 5-7)")
    ax.grid(axis="x", alpha=0.25, linestyle=":")
    return _save(fig, path)


def plot_viability(settlements: pd.DataFrame, config: Config, path: Path) -> Path:
    """IRR against LCOE for each perspective, with the hurdle rates marked."""
    fig, ax = plt.subplots(figsize=(8, 5))
    markers = {"utility": "o", "developer": "^"}
    for key, marker in markers.items():
        column = f"irr_{key}"
        if column not in settlements.columns:
            continue
        ax.scatter(
            settlements["least_cost_lcoe"],
            settlements[column] * 100.0,
            s=14,
            alpha=0.55,
            marker=marker,
            edgecolors="none",
            label=str(config.get(f"finance.perspectives.{key}.label", key)),
        )
        hurdle = config.get(f"finance.perspectives.{key}.hurdle_rate") or config.get(
            f"finance.perspectives.{key}.wacc"
        )
        if hurdle is not None:
            ax.axhline(float(hurdle) * 100.0, linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xlabel("LCOE of selected technology (USD/kWh)")
    ax.set_ylabel("IRR (%)")
    ax.set_title("Financial viability by perspective (Equations 12-13)")
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(frameon=False)
    return _save(fig, path)


def render_standard_figures(settlements: pd.DataFrame, config: Config) -> list[Path]:
    """Render every standard figure into ``paths.figures``."""
    figures_dir = config.path("figures")
    paths = [
        plot_lcoe_by_distance(settlements, figures_dir / "fig_lcoe_vs_distance.png"),
        plot_technology_mix(settlements, figures_dir / "fig_technology_mix.png"),
        plot_capex_breakdown(settlements, figures_dir / "fig_capex_breakdown.png"),
        plot_viability(settlements, config, figures_dir / "fig_viability.png"),
    ]
    return paths
