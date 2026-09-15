# Architecture

## Principles

1. **One module per equation group.** `costs/grid.py` is Equation 5;
   `finance/dcf.py` is Equations 11–14. A reader holding the proposal can find
   the code for any equation without searching.
2. **Configuration, not constants.** No numeric parameter appears in `src/`. A
   run is fully described by (config files, scenario, input data).
3. **Tables in, tables out.** Every stage takes a DataFrame and returns a new
   one. Nothing mutates its input, so stages compose and can be tested alone.
4. **The core carries no GIS dependency.** The model works on coordinates and
   attributes. geopandas is imported lazily, only to read geometry formats.
5. **Record why, not just what.** Every settlement carries a `decision_reason`;
   every run carries its provenance. A result that cannot be explained cannot be
   defended at viva.

## Dependency flow

```
                       config.py  ◄──────── config/*.yaml
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
      geo/            logging_setup.py      io/
   (Equation 1)                          (loaders, writers)
        │                                     │
        ▼                                     │
  preprocessing/  ── Table 3.3, served status │
        │                                     │
        ▼                                     │
   clustering/    ── Equations 1-2, typology  │
        │                                     │
        ▼                                     │
     demand/      ── Equations 3-4            │
        │                                     │
        ▼                                     │
      costs/      ── Equations 5-9            │
        │                                     │
        ▼                                     │
  optimisation/   ── Equation 10              │
        │                                     │
        ▼                                     │
    finance/      ── Equations 11-14          │
        │                                     │
        └──────────────► pipeline.py ◄────────┘
                              │
                     ┌────────┴────────┐
                     ▼                 ▼
                   cli.py            viz/
```

Dependencies run strictly downward. `geo/` knows nothing of costs; `costs/`
knows nothing of finance; `pipeline.py` is the only module that knows the whole
sequence. `sample/` sits outside the flow entirely — it fabricates inputs and
depends on nothing in the model.

## Module responsibilities

| Module | Owns | Does not own |
|---|---|---|
| `config.py` | YAML resolution, deep merge, scenario overlay, dotted access | Any knowledge of what the parameters mean |
| `geo/distance.py` | Equation 1, nearest-point and nearest-line queries, line densification | Projections, geometry operations |
| `preprocessing/footprint_filter.py` | Table 3.3 criteria, compound co-location, attrition reporting | Deciding who is electrified |
| `preprocessing/electrification_status.py` | Served/unserved inference from meters and network proximity | Clustering |
| `clustering/dbscan.py` | Equation 2, the relaxed pass, settlement summarisation | Demand, cost |
| `clustering/typology.py` | Settlement classification | Demand tier assignment (that reads typology) |
| `demand/tiers.py` | Equations 3–4, tier assignment, non-residential uplift | Technology sizing |
| `costs/sizing.py` | Network length and transformer count heuristics | Prices |
| `costs/{grid,minigrid,standalone}.py` | Equations 5–7 and per-technology OPEX and replacements | Comparison between technologies |
| `costs/annualisation.py` | Equations 8, 9, 9a | Which technology wins |
| `optimisation/least_cost.py` | Equation 10, the override, the micro-cluster test, decision reasons | Cash flows |
| `finance/dcf.py` | Equations 11–14, perspectives, connection-fee treatment, subsidy gap | Technology choice |
| `io/` | Reading layers, writing tables, run provenance | Any modelling |
| `viz/` | Figures and quick-look maps | Publication cartography (that is QGIS) |
| `pipeline.py` | The Section 3.5.5 sequence, the priority plan | Any equation |
| `cli.py` | Argument parsing, scenario and sweep orchestration, console reporting | Any modelling |

## Key design decisions

Recorded as ADRs in [`adr/`](adr/):

| ADR | Decision |
|---|---|
| [0001](adr/0001-record-architecture-decisions.md) | Record architecture decisions |
| [0002](adr/0002-dbscan-on-footprints.md) | DBSCAN on building footprints, not raster population |
| [0003](adr/0003-adapt-onsset-rather-than-extend-it.md) | Adapt OnSSET parameters in Python rather than extend OnSSET |
| [0004](adr/0004-micro-cluster-grid-eligibility.md) | Keep grid in the micro-cluster comparison by default |
| [0005](adr/0005-npc-lcoe-as-the-comparison-basis.md) | Use the discounted (9a) LCOE form as the comparison basis |
| [0006](adr/0006-synthetic-sample-data.md) | Ship synthetic sample data |

## Data flow through one run

```
data/raw/building_footprints.csv        3,959 structures
  │  filter_footprints            Table 3.3
  ▼
  2,679 dwellings                 (stores and enclosures removed)
  │  tag_served_buildings
  ▼
  ~1,900 unelectrified dwellings  (meter / LV / transformer proximity)
  │  cluster_buildings            Equation 2, eps = 75 m
  ▼
  60 clusters + ~1,100 noise points
  │  micro_cluster_noise          Equation 2 relaxed, eps = 400 m
  ▼
  60 clusters + micro-clusters + isolated homesteads
  │  summarise_clusters, assign_typology
  ▼
  ~340 settlements                one row each
  │  estimate_demand              Equations 3-4
  │  compare_technologies         Equations 5-9
  │  select_least_cost            Equation 10
  │  evaluate_viability           Equations 11-14
  ▼
  outputs/tables/*.csv, outputs/reports/run_summary.json
```

Figures are indicative, from the synthetic county at seed 42. They will differ
with real data and with any parameter change — which is the point of recording
provenance in `run_summary.json`.

## Extension points

**A fourth technology** (wind, hybrid diesel, hydro): add
`costs/<technology>.py` with a CAPEX function and an OPEX function, add its
parameters under `technologies:`, and add its key to `TECHNOLOGIES` in
`optimisation/least_cost.py`. Nothing else changes — the argmin is generic.

**A third perspective** (a concessionaire, a development financier): add a block
under `finance.perspectives`. `evaluate_viability` iterates over whatever
perspectives exist, so columns appear automatically.

**A different clustering algorithm** (HDBSCAN, OPTICS): implement the same
signature as `cluster_buildings` and return a `cluster_label` column with `-1`
for noise. Everything downstream depends only on that contract.

**Least-cost path routing** instead of straight-line MV distance: replace
`nearest_line_distance_km` in `electrification_status.py` with a routing call
that returns a path length per building. `D_c` in Equation 5 is read from a
column, so no cost code changes.
