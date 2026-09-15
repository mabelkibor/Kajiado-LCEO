"""Command-line interface.

    lceo sample-data              generate the synthetic county
    lceo run                      run Stages 1-5 for one scenario
    lceo sensitivity              sweep the parameters in config
    lceo compare-scenarios        run several scenarios and tabulate the mix
    lceo validate-config          resolve and print the merged configuration
    lceo figures                  render the standard result figures

Built on argparse so that the tool runs with no dependency beyond the modelling
stack itself.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from kajiado_lceo import __version__
from kajiado_lceo.config import load_config
from kajiado_lceo.logging_setup import configure_logging, get_logger

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lceo",
        description="GIS-aided techno-economic modelling of least-cost electrification "
        "pathways in Kajiado County, Kenya.",
    )
    parser.add_argument("--version", action="version", version=f"kajiado-lceo {__version__}")
    parser.add_argument("--config-dir", default="config", help="configuration directory")
    parser.add_argument("--log-level", default=None, help="DEBUG | INFO | WARNING | ERROR")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sample = sub.add_parser("sample-data", help="generate synthetic input layers")
    p_sample.add_argument("--output-dir", default="data/raw")
    p_sample.add_argument("--seed", type=int, default=42)

    p_run = sub.add_parser("run", help="run the full modelling sequence")
    p_run.add_argument("--scenario", default=None, help="scenario id (config/scenarios/<id>.yaml)")
    p_run.add_argument("--no-write", action="store_true", help="compute without writing outputs")

    p_sens = sub.add_parser("sensitivity", help="sweep parameters and report the technology mix")
    p_sens.add_argument("--scenario", default=None)
    p_sens.add_argument("--output", default=None, help="CSV path for the sweep results")

    p_cmp = sub.add_parser("compare-scenarios", help="run several scenarios side by side")
    p_cmp.add_argument("scenarios", nargs="*", help="scenario ids; defaults to all on disk")
    p_cmp.add_argument("--output", default=None)

    p_cfg = sub.add_parser("validate-config", help="resolve and print the merged configuration")
    p_cfg.add_argument("--scenario", default=None)
    p_cfg.add_argument("--key", default=None, help="print a single dotted key")

    p_fig = sub.add_parser("figures", help="render the standard result figures")
    p_fig.add_argument("--scenario", default=None)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config_dir, scenario=getattr(args, "scenario", None))
    level = args.log_level or str(config.get("run.log_level", "INFO"))
    configure_logging(level=level, log_dir=config.path("logs"))

    handlers = {
        "sample-data": _cmd_sample_data,
        "run": _cmd_run,
        "sensitivity": _cmd_sensitivity,
        "compare-scenarios": _cmd_compare_scenarios,
        "validate-config": _cmd_validate_config,
        "figures": _cmd_figures,
    }
    return handlers[args.command](args, config)


def _cmd_sample_data(args, config) -> int:
    from kajiado_lceo.sample import write_sample_data

    paths = write_sample_data(args.output_dir, seed=args.seed)
    print(f"Wrote {len(paths)} synthetic layers to {args.output_dir}:")
    for name, path in paths.items():
        print(f"  {name:22s} {path}")
    print("\nThis data is SYNTHETIC. It exercises the code; it says nothing about Kajiado.")
    return 0


def _cmd_run(args, config) -> int:
    from kajiado_lceo.pipeline import run

    result = run(config, write_outputs=not args.no_write)
    summary = result.summary
    print(f"\nScenario: {config.scenario}")
    print(f"  Settlements modelled : {summary['totals']['settlements']:,}")
    print(f"  Households            : {summary['totals']['households']:,.0f}")
    print(f"  Annual demand         : {summary['totals']['annual_energy_gwh']:.2f} GWh")
    print(f"  Total CAPEX           : USD {summary['totals']['total_capex_usd']:,.0f}")
    print(f"  Mean LCOE             : USD {summary['totals']['mean_lcoe_usd_per_kwh']:.4f}/kWh")
    print("\n  Least-cost technology mix (Equation 10):")
    for technology, count in sorted(summary["technology_mix"].items(), key=lambda kv: -kv[1]):
        print(f"    {technology:12s} {count:6,d} settlements")
    for key, block in (summary.get("viability") or {}).items():
        print(
            f"\n  {key.capitalize()} perspective: {block['viable_settlements']:,} viable, "
            f"subsidy gap USD {block['total_subsidy_gap_usd']:,.0f}"
        )
    if not args.no_write:
        print(f"\nOutputs written to {config.path('outputs')}")
    return 0


def _cmd_sensitivity(args, config) -> int:
    from kajiado_lceo.pipeline import run

    parameters = config.get("sensitivity.parameters", []) or []
    if not parameters:
        logger.error("no sensitivity.parameters configured in config/techno_economic.yaml")
        return 1

    rows = []
    for entry in parameters:
        path = str(entry["path"])
        base_value = config.get(path)
        if base_value is None:
            logger.warning("skipping unknown sensitivity parameter: %s", path)
            continue
        for multiplier in entry.get("multipliers", []):
            value = float(base_value) * float(multiplier)
            variant = config.with_override_path(path, value)
            result = run(variant, write_outputs=False)
            mix = result.summary["technology_mix"]
            rows.append(
                {
                    "parameter": path,
                    "multiplier": multiplier,
                    "value": value,
                    "mean_lcoe": result.summary["totals"]["mean_lcoe_usd_per_kwh"],
                    "total_capex_usd": result.summary["totals"]["total_capex_usd"],
                    **{f"n_{k}": v for k, v in mix.items()},
                }
            )
            logger.info("sensitivity: %s = %.4g -> %s", path, value, mix)

    table = pd.DataFrame(rows).fillna(0)
    output = Path(args.output) if args.output else config.path("tables") / "sensitivity_sweep.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    print(table.to_string(index=False))
    print(f"\nWrote {output}")
    return 0


def _cmd_compare_scenarios(args, config) -> int:
    from kajiado_lceo.pipeline import run

    scenario_dir = Path(args.config_dir) / "scenarios"
    scenarios = args.scenarios or sorted(p.stem for p in scenario_dir.glob("*.yaml"))

    rows = []
    for scenario in scenarios:
        variant = load_config(args.config_dir, scenario=scenario)
        result = run(variant, write_outputs=False)
        totals = result.summary["totals"]
        row = {
            "scenario": scenario,
            "settlements": totals["settlements"],
            "households": totals["households"],
            "mean_lcoe": totals["mean_lcoe_usd_per_kwh"],
            "total_capex_usd": totals["total_capex_usd"],
            **{f"n_{k}": v for k, v in result.summary["technology_mix"].items()},
        }
        # Viability columns matter: a scenario that shifts who pays the
        # connection fee changes nothing about cost or technology mix, and
        # without these columns would appear — wrongly — to be a no-op.
        for key, block in (result.summary.get("viability") or {}).items():
            row[f"viable_{key}"] = block["viable_settlements"]
            row[f"subsidy_gap_{key}"] = block["total_subsidy_gap_usd"]
        rows.append(row)

    table = pd.DataFrame(rows).fillna(0)
    output = Path(args.output) if args.output else config.path("tables") / "scenario_comparison.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    print(table.to_string(index=False))
    print(f"\nWrote {output}")
    return 0


def _cmd_validate_config(args, config) -> int:
    if args.key:
        print(json.dumps(config.get(args.key), indent=2, default=str))
        return 0
    print(f"# scenario: {config.scenario}")
    print(f"# sources : {', '.join(str(p) for p in config.sources)}")
    print(json.dumps(config.data, indent=2, default=str))
    return 0


def _cmd_figures(args, config) -> int:
    from kajiado_lceo.pipeline import run
    from kajiado_lceo.viz import render_standard_figures

    result = run(config, write_outputs=False)
    paths = render_standard_figures(result.settlements, config)
    for path in paths:
        print(f"  wrote {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
