#!/usr/bin/env python3
"""Regenerate the standalone kit cost table from the sizing basis.

Equation 7 takes per-household kit cost as a parameter, but that parameter must
stay consistent with the energy the same household is credited with delivering
in Equation 3 — otherwise the SHS LCOE is understated and the least-cost rule of
Equation 10 is biased towards standalone systems.

This script derives the table in ``technologies.standalone.kit_by_tier`` from
``technologies.standalone.sizing_basis`` and the tier consumption figures in
``config/demand_tiers.yaml``, and prints a YAML block to paste back.

    python scripts/derive_shs_kit_costs.py [--scenario baseline]
"""

from __future__ import annotations

import argparse

from kajiado_lceo.config import load_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--scenario", default=None)
    args = parser.parse_args()

    config = load_config(args.config_dir, scenario=args.scenario)
    basis = config.section("technologies.standalone.sizing_basis")
    if not basis:
        raise SystemExit("no technologies.standalone.sizing_basis configured")

    psh = float(basis["peak_sun_hours"])
    pr = float(basis["performance_ratio"])
    oversize = float(basis["pv_oversize_factor"])
    dod = float(basis["battery_depth_of_discharge"])
    rte = float(basis["battery_round_trip_efficiency"])
    pv_cost = float(basis["small_system_pv_cost_per_kw"])
    battery_cost = float(basis["small_system_battery_cost_per_kwh"])
    bos_fraction = float(basis["bos_fraction"])
    bos_fixed = float(basis["bos_fixed"])
    min_panel = float(basis.get("min_panel_cost", 0.0))
    min_battery = float(basis.get("min_battery_cost", 0.0))

    print("    kit_by_tier:")
    for tier, spec in config.section("demand.tiers").items():
        daily_kwh = float(spec["kwh_per_household_day"])
        pv_kw = daily_kwh * oversize / (psh * pr)
        battery_kwh = daily_kwh / (dod * rte)
        panel = max(pv_kw * pv_cost, min_panel)
        battery = max(battery_kwh * battery_cost, min_battery)
        bos = bos_fraction * (panel + battery) + bos_fixed
        print(
            f"      {tier}: {{panel: {panel:.1f}, battery: {battery:.1f}, bos: {bos:.1f}}}"
            f"   # {daily_kwh:.2f} kWh/day -> {pv_kw:.2f} kW PV, {battery_kwh:.2f} kWh storage"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
