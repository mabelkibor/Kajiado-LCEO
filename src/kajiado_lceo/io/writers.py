"""Writing model outputs: tables, the run summary, and provenance."""

from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from kajiado_lceo import __version__
from kajiado_lceo.config import Config
from kajiado_lceo.logging_setup import get_logger

logger = get_logger(__name__)


def write_table(df: pd.DataFrame, path: str | Path, index: bool = False) -> Path:
    """Write a DataFrame to CSV or Parquet, creating parent directories."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".parquet":
        df.to_parquet(path, index=index)
    else:
        df.to_csv(path, index=index)
    logger.info("wrote %s (%d rows)", path, len(df))
    return path


def _git_revision() -> str | None:
    """Current commit hash, so a result can be traced back to the code."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        ).stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return None


def build_run_summary(settlements: pd.DataFrame, config: Config) -> dict[str, Any]:
    """Assemble the headline figures and provenance for one model run.

    The summary is what gets quoted in the dissertation, so it records not only
    the results but the exact configuration, code revision and scenario that
    produced them.
    """
    technology_counts = settlements["least_cost_technology"].value_counts().to_dict()
    by_technology = (
        settlements.groupby("least_cost_technology")
        .agg(
            settlements=("settlement_id", "count"),
            households=("households", "sum"),
            annual_energy_kwh=("annual_energy_kwh", "sum"),
            capex_usd=("least_cost_capex", "sum"),
            mean_lcoe=("least_cost_lcoe", "mean"),
        )
        .to_dict(orient="index")
    )

    summary: dict[str, Any] = {
        "run": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "package_version": __version__,
            "git_revision": _git_revision(),
            "python": platform.python_version(),
            "scenario": config.scenario,
            "config_sources": [str(p) for p in config.sources],
            "seed": config.get("run.seed"),
        },
        "totals": {
            "settlements": len(settlements),
            "households": float(settlements["households"].sum()),
            "annual_energy_gwh": float(settlements["annual_energy_kwh"].sum() / 1e6),
            "total_capex_usd": float(settlements["least_cost_capex"].sum(skipna=True)),
            "mean_lcoe_usd_per_kwh": float(settlements["least_cost_lcoe"].mean(skipna=True)),
        },
        "technology_mix": {str(k): int(v) for k, v in technology_counts.items()},
        "by_technology": {str(k): v for k, v in by_technology.items()},
        "decision_reasons": {
            str(k): int(v)
            for k, v in settlements["decision_reason"].value_counts().to_dict().items()
        },
    }

    for key in ("utility", "developer"):
        if f"viable_{key}" in settlements.columns:
            summary.setdefault("viability", {})[key] = {
                "viable_settlements": int(settlements[f"viable_{key}"].sum()),
                "total_subsidy_gap_usd": float(settlements[f"subsidy_gap_{key}"].sum(skipna=True)),
                "median_irr": float(settlements[f"irr_{key}"].median(skipna=True)),
            }
    return summary


def write_run_summary(summary: dict[str, Any], path: str | Path) -> Path:
    """Serialise the run summary to JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, default=str)
    logger.info("wrote run summary to %s", path)
    return path
