# Technical Specification

**Component:** `kajiado_lceo` · **Version:** 0.1.0
Companion documents: [`PRD.md`](PRD.md) (what and why), [`METHODOLOGY.md`](METHODOLOGY.md)
(the equations), [`ARCHITECTURE.md`](ARCHITECTURE.md) (how the code is organised).

---

## 1. Interfaces

### 1.1 Command line

```
lceo [--config-dir DIR] [--log-level LEVEL] <command>

  sample-data        [--output-dir DIR] [--seed N]
  run                [--scenario ID] [--no-write]
  sensitivity        [--scenario ID] [--output CSV]
  compare-scenarios  [SCENARIO ...] [--output CSV]
  validate-config    [--scenario ID] [--key DOTTED.PATH]
  figures            [--scenario ID]
```

Exit codes: `0` success; `1` handled failure (missing parameter, unusable
input); non-zero traceback for unhandled errors, which are bugs.

### 1.2 Python

```python
from kajiado_lceo import load_config
from kajiado_lceo.pipeline import run

config = load_config("config", scenario="baseline")
result = run(config)                    # PipelineResult
result.settlements                      # one row per settlement, all metrics
result.priority_plan                    # ranked investment sequence
result.summary                          # headline figures + provenance
```

Stages are independently callable, in this order:

```python
filter_footprints(footprints, config)        -> DataFrame   # Table 3.3
tag_served_buildings(dwellings, ..., config) -> DataFrame
cluster_buildings(unelectrified, config)     -> DataFrame   # Eq. 2
micro_cluster_noise(clustered, config)       -> DataFrame   # Eq. 10 relaxed pass
summarise_clusters(clustered, config)        -> DataFrame
assign_typology(settlements, config)         -> DataFrame
estimate_demand(settlements, config)         -> DataFrame   # Eq. 3-4
compare_technologies(settlements, config)    -> DataFrame   # Eq. 5-9
select_least_cost(settlements, config)       -> DataFrame   # Eq. 10
evaluate_viability(settlements, config)      -> DataFrame   # Eq. 11-14
```

Every stage takes a DataFrame and a `Config` and returns a **new** DataFrame.
No stage mutates its input. `compare_technologies` is idempotent — it drops the
columns it is about to regenerate — so a settlement frame can be re-costed under
varied parameters, which is what the sensitivity sweep does.

---

## 2. Data contracts

Full column specifications in [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md).

### 2.1 Inputs

| Layer | Required columns | Optional | Formats |
|---|---|---|---|
| Building footprints | `latitude`, `longitude`, `area_m2` | `building_id`, `perimeter_m`, `roof_class`, `terrain_class` | CSV, Parquet, GeoJSON, GPKG/SHP¹ |
| MV lines | `lat1`, `lon1`, `lat2`, `lon2` | — | CSV, GeoJSON, GPKG/SHP¹ |
| LV lines | as MV | — | as MV |
| Transformers | `latitude`, `longitude` | `transformer_id`, `capacity_kva`, `spare_capacity_kva` | CSV, GeoJSON, GPKG/SHP¹ |
| Meters | `latitude`, `longitude` | `meter_id` | CSV, GeoJSON, GPKG/SHP¹ |

¹ Geometry formats require the optional `gis` extra (`pip install -e ".[gis]"`).
Polygon geometries are reduced to centroids in EPSG:4326.

**Missing-layer behaviour.** MV, LV, transformer and meter layers are optional
and degrade gracefully: an absent MV layer yields infinite distance, which
Equation 10 reads as "grid is not a candidate". Building footprints are
mandatory. Set `run.strict_inputs: true` to fail instead of degrading.

### 2.2 Outputs

| File | Grain | Contents |
|---|---|---|
| `settlement_clusters.csv` | settlement | Every computed column — the full record |
| `least_cost_technology.csv` | settlement | Demand, distance, CAPEX and LCOE for all three options, the selection, its margin and reason |
| `financial_viability.csv` | settlement | NPV, IRR, DPP, viability flag and subsidy gap per perspective |
| `prioritised_electrification_plan.csv` | settlement, ranked | Priority rank and score, cumulative households and CAPEX |
| `structure_filter_report.csv` | criterion | Attrition at each Table 3.3 step |
| `run_summary.json` | run | Totals, technology mix, decision reasons, viability, provenance |
| `data/interim/stage{1..4}_*.csv` | varies | Per-stage intermediates when `run.write_intermediates: true` |

---

## 3. Configuration

### 3.1 Resolution order

1. `config/default.yaml`
2. each file in its `include:` list, in order
3. `config/scenarios/<scenario>.yaml`
4. programmatic overrides (`Config.with_overrides`, `with_override_path`)

Mappings merge key-by-key; every other type — **including lists** — is replaced
wholesale, so a scenario that redefines a list replaces it rather than appending.

### 3.2 Access contract

`Config` is frozen. `get(path, default)` returns a default; `require(path)`
raises `KeyError` naming the missing key and the files loaded. `with_*` methods
return new instances. A parameter absent from config and required by a
computation is an error, never a silent default — this is what makes a run fully
described by (config, scenario, data).

### 3.3 Key parameter groups

| Group | Governs | Section |
|---|---|---|
| `footprint_filter.*` | Structure filtering | 3.4.3 / Table 3.3 |
| `electrification_status.*` | Who counts as already served | 3.4 |
| `clustering.*` | ε, MinPts, relaxed pass, micro-cluster grid eligibility | Eq. 1–2, 10 |
| `typology.*` | Settlement classification thresholds | 3.3, 3.7 |
| `demand.*` | Tiers, load factors, assignment rules, non-residential uplift | Eq. 3–4 |
| `technologies.{grid,minigrid,standalone}.*` | CAPEX, OPEX, sizing, lifetimes, deployment time | Eq. 5–7 |
| `finance.*` | Discount rate, analysis period, perspectives, tariffs, hurdles | Eq. 8–14 |
| `sensitivity.parameters` | What the sweep varies | 3.7 |

---

## 4. Algorithms

### 4.1 Complexity

| Operation | Complexity | Note |
|---|---|---|
| Structure filter (area, compactness, roof) | O(n) | Vectorised |
| Compound co-location | O(n²/c) worst case | Chunked union-find; c = chunk size |
| DBSCAN (haversine, ball-tree) | O(n log n) expected | Degrades to O(n²) at large ε |
| Nearest-network distance | O(n·m) chunked | m = densified network points |
| Demand, CAPEX, LCOE | O(n) | Vectorised |
| Decision rule (Equation 10) | O(n) | Per-row; branches on decision reason |
| DCF (Equations 11–14) | O(n·T) | T = analysis period; IRR is a Brent solve per settlement |

The county-scale bottleneck is the nearest-network query. It is chunked to bound
peak memory (`chunk_size`, default 4096 rows); N-04 in the PRD (10⁶ footprints)
is not yet benchmarked.

### 4.2 Numerical conventions

| Situation | Behaviour | Why |
|---|---|---|
| No reachable network | Distance `inf`, CAPEX `NaN` | Equation 10 excludes it as infeasible |
| Zero demand | LCOE `NaN`, not `inf` | Excluded from argmin, not ranked last |
| No IRR root | `NaN` | A project that never pays back has no IRR |
| Capital never recovered | DPP `NaN` | Distinct from "recovered in year T" |
| Zero discount rate | `CRF = 1/n` | The analytic limit; keeps a zero-rate sweep valid |
| Zero perimeter | Compactness `NaN`, treated as "no evidence" | Absence of data must not fail a criterion |
| All options infeasible | Technology `none`, reason `no_feasible_option` | Recorded, never silently defaulted |

### 4.3 Reproducibility

Seeded RNG (`run.seed`) governs sample generation and any stochastic validation
sampling. Every run writes package version, git revision, Python version,
scenario, config source list and seed into `run_summary.json`. Identical inputs,
config and seed reproduce results exactly.

---

## 5. Quality

### 5.1 Testing

145 tests. The suite asserts the **equations**, not merely that the code runs:

| Property asserted | Test |
|---|---|
| `CRF(0.10,20) = 0.117460` | `test_crf_matches_the_textbook_value` |
| One degree of latitude `= R·π/180` | `test_one_degree_of_latitude_is_about_111_km` |
| Longitude degrees shrink by `cos φ` | `test_longitude_degrees_shrink_with_latitude` |
| Equations 9 and 9a coincide when they should | `test_the_two_lcoe_forms_agree_without_replacements_or_salvage` |
| IRR is the rate that zeroes NPV | `test_irr_makes_npv_zero` |
| Compactness of a circle `= 1`, of a square `= π/4` | `test_compactness_of_a_circle_is_one` |
| SHS kit costs match their sizing basis | `test_standalone_kit_costs_match_their_sizing_basis` |
| Households conserved across all five stages | `test_households_are_conserved_from_buildings_to_settlements` |
| Noise points are never discarded | `test_noise_points_are_never_discarded` |
| Raising grid CAPEX moves settlements off grid | `test_higher_grid_cost_moves_settlements_off_grid` |

Markers: `slow` (end-to-end runs), `gis` (needs the optional stack).

### 5.2 Static checks

`ruff` (lint + format, line length 100), `mypy` on the package. Equation symbols
keep their published casing (`E_c`, `H_c`, `P_c`) — `N803`/`N806` are disabled
deliberately rather than renaming the mathematics.

### 5.3 CI

GitHub Actions on Python 3.10–3.12: lint, type-check, test, then a full
end-to-end run against the synthetic county to catch integration regressions the
unit tests cannot.

---

## 6. Dependencies

| Package | Role | Required |
|---|---|---|
| numpy, pandas | Arrays and tables | Yes |
| scikit-learn | DBSCAN with haversine metric | Yes |
| scipy | `brentq` for the IRR solve | Yes |
| PyYAML | Configuration | Yes |
| matplotlib | Figures | Yes |
| geopandas, shapely, pyproj, rasterio | Vector/raster I/O | Optional (`gis`) |

The numerical core deliberately carries **no GIS dependency**: the model
operates on coordinates and attributes, so it installs and runs anywhere, and
the heavyweight geospatial stack is needed only to read geometry formats.

---

## 7. Known limitations

| # | Limitation | Consequence | Path |
|---|---|---|---|
| L-01 | Cost and demand parameters are provisional | No result is reportable as a finding yet | `ASSUMPTIONS.md`, milestone M3 |
| L-02 | MV distance is straight-line, not routed | Understates real extension cost; biases towards grid | Terrain multiplier now; least-cost path on the roadmap |
| L-03 | Served status inferred from proximity, not a connection register | Over- or under-states the unelectrified population | Bounded by the `require_meter_evidence` run (`VALIDATION.md`) |
| L-04 | Structure filter is heuristic | Household counts carry a residual error | Ground-truth sample, reported as demand uncertainty |
| L-05 | Demand static by tier | Ignores load growth and productive use | `productive_use` scenario; DCF growth rate |
| L-06 | One analysis period for assets of 15/20/30-year life | Comparability rests on replacements and salvage being right | Sensitivity on the period |
| L-07 | Transformer siting is a count, not a location | LV cost is approximate within a settlement | Out of scope — this screens, it does not design |
| L-08 | No reliability or quality-of-supply dimension | A grid connection and a mini-grid connection are treated as equal service | Out of scope per PRD §5 |
