# Data dictionary

Schemas for every input the model reads and every output it writes.
Units: distances km unless suffixed `_m`; energy kWh; power kW; money USD.

---

## Inputs

### `building_footprints` (required)

| Column | Type | Required | Description |
|---|---|---|---|
| `building_id` | str | No — generated | Stable identifier |
| `latitude` | float | **Yes** | Centroid latitude, EPSG:4326 |
| `longitude` | float | **Yes** | Centroid longitude, EPSG:4326 |
| `area_m2` | float | **Yes** | Footprint area — drives the Table 3.3 filter |
| `perimeter_m` | float | No | Enables the compactness criterion; absent → criterion skipped, not failed |
| `roof_class` | str | No | Roofing material; used only if `footprint_filter.roof_signature.enabled` |
| `terrain_class` | str | No | `flat` \| `undulating` \| `steep`; selects the MV cost multiplier |
| `confidence` | float | No | Detection confidence, if the source provides it |

Polygon geometry may be supplied instead of `latitude`/`longitude` in a vector
format; centroids are derived in EPSG:4326 (requires the `gis` extra).

### `mv_lines`, `lv_lines`

| Column | Type | Required | Description |
|---|---|---|---|
| `lat1`, `lon1` | float | **Yes** | Segment start |
| `lat2`, `lon2` | float | **Yes** | Segment end |

GeoJSON `LineString`/`MultiLineString` is exploded into segments automatically.
Note GeoJSON coordinate order is (lon, lat); the loader converts.

### `transformers`

| Column | Type | Required | Description |
|---|---|---|---|
| `latitude`, `longitude` | float | **Yes** | Location |
| `transformer_id` | str | No | Identifier |
| `capacity_kva` | float | No | Rated capacity |
| `spare_capacity_kva` | float | No | Available headroom; absent → treated as 0, so new capacity is costed |

### `meters`

| Column | Type | Required | Description |
|---|---|---|---|
| `latitude`, `longitude` | float | **Yes** | Connection location |
| `meter_id` | str | No | Anonymised identifier — **never** a customer identifier |

---

## Intermediate: building level

Written to `data/interim/` when `run.write_intermediates: true`.

| Column | Stage | Description |
|---|---|---|
| `passes_area` | 1 | Area within the habitable band |
| `passes_compactness` | 1 | `C = 4πA/P²` above threshold; `NaN` perimeter → `True` |
| `passes_roof` | 1 | Roof signature residential, or criterion disabled |
| `compactness` | 1 | Computed `C` |
| `is_ancillary` | 1 | Flagged by compound co-location |
| `is_dwelling` | 1 | Passes all criteria and is not ancillary |
| `households` | 1 | Households attributed (default 1.0 per dwelling) |
| `distance_to_mv_km` | 1 | Great-circle distance to nearest MV line |
| `distance_to_lv_km` | 1 | Great-circle distance to nearest LV line |
| `distance_to_transformer_km` | 1 | Distance to nearest transformer |
| `nearest_transformer_spare_kva` | 1 | Spare capacity at that transformer |
| `has_meter` | 1 | A meter record snaps to this footprint |
| `is_served` | 1 | Treated as already electrified |
| `cluster_label` | 2 | DBSCAN label; `-1` is noise |
| `micro_cluster_label` | 2 | Relaxed-pass label; `-1` where not applicable |
| `settlement_id` | 2 | `C######` cluster, `M######` micro-cluster, `D######` dispersed |
| `is_dispersed` | 2 | Was a noise point under the primary pass |

---

## Output: settlement level

The grain of every output table is one settlement.

### Identity and geometry

| Column | Description |
|---|---|
| `settlement_id` | Unique; prefix encodes how it was formed |
| `n_buildings` | Member footprints |
| `households` | `H_c` — filtered household count |
| `latitude`, `longitude` | Cluster centroid |
| `area_km2` | Bounding-box footprint area, floored at 1 ha |
| `density_bldg_per_km2` | Built density |
| `distance_to_mv_km` | `D_c` — minimum over member buildings |
| `distance_to_lv_km` | Minimum distance to LV |
| `is_dispersed`, `is_micro_cluster` | Formation flags |
| `typology` | `dispersed` \| `small_rural` \| `large_rural` \| `peri_urban` |

### Demand (Equations 3–4)

| Column | Description |
|---|---|
| `demand_tier` | `tier_1` … `tier_4` |
| `daily_kwh_per_household` | `d_h` |
| `load_factor` | `LF` |
| `residential_energy_kwh` | Equation 3 |
| `non_residential_energy_kwh` | Uplift for anchor loads |
| `annual_energy_kwh` | `E_c` — the LCOE denominator |
| `peak_demand_kw` | `P_c,peak` — Equation 4 |

### Costs (Equations 5–9)

| Column | Description |
|---|---|
| `grid_cost_mv`, `grid_cost_lv`, `grid_cost_transformers`, `grid_cost_connections` | Equation 5 terms |
| `grid_mv_length_km`, `grid_lv_length_km`, `grid_n_transformers` | Grid sizing |
| `mg_cost_pv`, `mg_cost_battery`, `mg_cost_inverter`, `mg_cost_distribution`, `mg_cost_connections` | Equation 6 terms |
| `mg_pv_capacity_kw`, `mg_battery_capacity_kwh`, `mg_inverter_capacity_kw`, `mg_distribution_length_km` | Mini-grid sizing |
| `shs_kit_cost_per_household` | Equation 7 unit cost by tier |
| `capex_grid`, `capex_minigrid`, `capex_standalone` | Total CAPEX; `NaN` = infeasible |
| `opex_grid`, `opex_minigrid`, `opex_standalone` | Annual OPEX |
| `npc_grid`, `npc_minigrid`, `npc_standalone` | Net present cost (Equation 9a) |
| `lcoe_grid`, `lcoe_minigrid`, `lcoe_standalone` | LCOE, USD/kWh |

### Decision (Equation 10)

| Column | Description |
|---|---|
| `least_cost_technology` | `grid` \| `minigrid` \| `standalone` \| `none` |
| `least_cost_lcoe`, `least_cost_capex`, `least_cost_opex` | Of the selected option |
| `lcoe_margin` | Gap to the runner-up — robustness of the choice |
| `decision_reason` | `argmin` \| `micro_cluster_comparison` \| `dispersed_override` \| `no_feasible_option` |
| `deployment_months` | Time to energisation for the selected technology |

### Viability (Equations 11–14), one set per perspective `p`

| Column | Description |
|---|---|
| `npv_p` | Equation 12 |
| `irr_p` | Equation 13; `NaN` where no root exists |
| `dpp_p` | Equation 14, interpolated within the recovery year; `NaN` if never |
| `viable_p` | `NPV ≥ 0` or `IRR ≥ hurdle` |
| `subsidy_gap_p` | Present-value grant that would bring NPV to zero; `0` if viable |
| `requires_public_support` | Fails every perspective |

### Priority plan

| Column | Description |
|---|---|
| `priority_rank` | 1 = electrify first |
| `priority_score` | Weighted composite of LCOE, viability and deployment speed |
| `cumulative_households` | Households reached by this rank |
| `cumulative_capex_usd` | Capital committed by this rank |

---

## `run_summary.json`

```jsonc
{
  "run": {
    "timestamp_utc", "package_version", "git_revision", "python",
    "scenario", "config_sources", "seed"
  },
  "totals": {
    "settlements", "households", "annual_energy_gwh",
    "total_capex_usd", "mean_lcoe_usd_per_kwh"
  },
  "technology_mix":   { "grid": n, "minigrid": n, "standalone": n },
  "by_technology":    { "<tech>": { "settlements", "households",
                                    "annual_energy_kwh", "capex_usd", "mean_lcoe" } },
  "decision_reasons": { "argmin": n, "dispersed_override": n, ... },
  "viability":        { "<perspective>": { "viable_settlements",
                                           "total_subsidy_gap_usd", "median_irr" } }
}
```
