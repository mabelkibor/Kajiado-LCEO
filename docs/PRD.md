# Product Requirements Document

**Product:** Kajiado-LCEO — settlement-level least-cost electrification decision support
**Version:** 0.1.0 · **Status:** Alpha · **Owner:** Mabel Chelagat Kibor
**Supervisor:** Dr. Eng. S. Roy Orenge · **Institution:** Strathmore University

---

## 1. Problem

Sub-national planners and infrastructure investors in Kenya have no
settlement-level decision-support framework for deciding *how* unelectrified
populations within a heterogeneous county should be electrified.

County governments, REREC, KPLC and private renewable energy developers must
choose between grid extension, solar mini-grids and standalone PV for different
settlement types. Today they choose using:

- **aggregated access statistics**, which cannot resolve which settlements are
  unelectrified, only what share of a county is;
- **project-based expansion**, in which the schemes nearest the existing network
  are electrified first because they are nearest, not because they are cheapest;
- **no systematic cost comparison** across technologies — capital cost, LCOE,
  deployment time and financial return are rarely set side by side.

The consequence in Kajiado is a specific and now-common failure mode: the county
reports high grid presence, yet a large share of Maasai *manyattas* remain dark
because they fall outside scheme boundaries and below transformer load
thresholds. Without a settlement-level screening tool these last-mile clusters
are invisible to budget cycles. SDG 7.1.1 goes unmet not for want of money but
for want of evidence on where to spend it.

## 2. Objectives

### General objective

Formulate and apply a GIS-aided techno-economic and financial modelling
framework that determines the least-cost and investment-feasible electrification
pathways within the heterogeneous settlements of Kajiado County.

### Specific objectives, and how the product meets them

| # | Objective | Delivered by | Verified by |
|---|---|---|---|
| I | Spatially identify and cluster unelectrified settlements from high-resolution building footprints and proximity to MV/LV networks and transformers | Stage 1-2 — `preprocessing/`, `clustering/` (Equations 1-2) | `tests/test_clustering.py`, `tests/test_preprocessing.py` |
| II | Estimate settlement-level demand from household counts and standardised demand tiers | Stage 3 — `demand/` (Equations 3-4) | `tests/test_demand.py` |
| III | Perform economic analysis of capital, long-run marginal and operational costs for all three technologies across settlement typologies | Stage 4 — `costs/` (Equations 5-9) | `tests/test_costs.py` |
| IV | Propose the optimum pathway per settlement, from both utility and private-developer lenses | Stage 4-5 — `optimisation/`, `finance/` (Equations 10-14) | `tests/test_optimisation.py`, `tests/test_finance.py` |

### Research questions the outputs must answer

1. What approach identifies and classifies unelectrified settlements from
   footprints, MV/LV networks, transformers and meter data?
2. What is each settlement's approximate demand under standardised tiers?
3. How do the three technologies compare on capital cost, operational cost and
   LCOE across settlement typologies?
4. Which technology is infrastructurally and financially optimal for each
   settlement under varying spatial and economic conditions, and fastest to
   deploy?

## 3. Users

| User | Decision they hold | What they need from this | Primary output |
|---|---|---|---|
| **Kajiado County planners** | The county investment sequence taken to the County Assembly | A defensible ranking of which settlements to electrify, in what order, with what | `prioritised_electrification_plan.csv` |
| **REREC / KPLC** | Which candidate schemes enter the budget | A transparent scheme ranking that reflects the real connection-fee structure | `least_cost_technology.csv`, `financial_viability.csv` |
| **Private RE developers** | Where to commit capital without public subsidy | A pre-screened pipeline of settlements whose IRR clears a commercial hurdle | `financial_viability.csv` filtered on `viable_developer` |
| **The researcher** | What the dissertation can defend | Reproducible, auditable, equation-traceable results with quantified uncertainty | `run_summary.json`, sensitivity and scenario tables |

Each user gets the same model with a different reading. The unifying benefit:
scarce infrastructure capital is matched to the settlement that needs it, rather
than absorbed by the corridor that already has service.

## 4. Requirements

### Functional

| ID | Requirement | Priority | Status |
|---|---|---|---|
| F-01 | Ingest high-resolution building footprints and derive centroids and areas | Must | Done |
| F-02 | Filter non-residential structures by area, compactness, roof signature and compound co-location | Must | Done |
| F-03 | Determine served/unserved status from meter records and MV/LV/transformer proximity | Must | Done |
| F-04 | Cluster unelectrified dwellings into settlements by DBSCAN on haversine distance | Must | Done |
| F-05 | Retain noise points as dispersed homesteads and re-cluster them at a relaxed radius | Must | Done |
| F-06 | Classify settlements into dispersed / small rural / large rural / peri-urban | Must | Done |
| F-07 | Assign a demand tier and compute annual and peak demand per settlement | Must | Done |
| F-08 | Compute CAPEX and OPEX for grid, mini-grid and standalone per settlement | Must | Done |
| F-09 | Compute LCOE consistently across all three technologies | Must | Done |
| F-10 | Select the least-cost technology, applying the dispersed override and micro-cluster test | Must | Done |
| F-11 | Evaluate NPV, IRR and discounted payback from utility and developer perspectives | Must | Done |
| F-12 | Treat the household connection fee as cost or revenue by perspective | Must | Done |
| F-13 | Flag settlements requiring public/REREC support, and size the subsidy gap | Must | Done |
| F-14 | Produce a prioritised county electrification plan | Must | Done |
| F-15 | Run named scenarios by configuration overlay | Must | Done |
| F-16 | Sweep parameters for sensitivity analysis | Must | Done |
| F-17 | Render the standard result figures and a quick-look map | Should | Done |
| F-18 | Export settlement results for QGIS/ArcGIS cartography | Should | Done (CSV with coordinates) |
| F-19 | Terrain- and land-cover-adjusted MV routing cost | Should | Partial — multiplier implemented, DEM ingestion not |
| F-20 | Least-cost network routing rather than straight-line distance | Could | Not started — see `docs/ROADMAP.md` |
| F-21 | Spatial decision-support dashboard for county stakeholders | Could | Not started — dissemination commitment, Section 3.10 |

### Non-functional

| ID | Requirement | Target | Status |
|---|---|---|---|
| N-01 | **Reproducibility** — identical inputs, config and seed give identical outputs | Exact | Done; provenance in `run_summary.json` |
| N-02 | **Traceability** — every computation cites its governing equation | 100% of modelling functions | Done |
| N-03 | **No hidden parameters** — every numeric assumption lives in `config/` | 100% | Done |
| N-04 | **Runs county-scale** | ~10⁶ footprints without a workstation | Chunked distance queries; not yet benchmarked at 10⁶ |
| N-05 | **Runnable without restricted data** | Synthetic county ships with the repo | Done |
| N-06 | **Optional GIS stack** — the numerical core runs without geopandas | Core has no GIS dependency | Done |
| N-07 | **Tested at equation level**, not merely at code level | Every equation has a value-level test | Done — 145 tests |
| N-08 | **Auditable uncertainty** — provisional parameters are marked, not silently used | Every one listed in `ASSUMPTIONS.md` | Done |

## 5. Scope

**In scope.** Kajiado County. Settlement-level analysis on building footprints.
Electricity *access expansion* only. Three technologies: grid extension, solar
PV mini-grids, standalone solar PV. Cost, LCOE, NPV, IRR, payback, deployment
time. Utility and private-developer perspectives.

**Out of scope.** National generation planning, transmission reinforcement,
reliability improvement. Wind, hydro, biomass, hybrid diesel. Social and
political determinants of technology adoption. Macroeconomic impacts of
electrification. Detailed engineering design — this model screens and ranks; it
does not size a scheme for construction.

## 6. Success criteria

The product succeeds if:

1. Every unelectrified settlement in Kajiado — **including dispersed homesteads**
   — receives a technology recommendation with an LCOE and a stated reason.
2. The grid/off-grid crossover distance is quantified by settlement size, and is
   stable under the sensitivity sweep, or its instability is quantified.
3. Both the utility and the developer can identify their viable subsets, and the
   subsidy gap for the remainder is sized in money.
4. A county planner can reproduce any number in the dissertation from this
   repository plus the input data, using the provenance in `run_summary.json`.
5. Results are defensible at viva: each figure traces to an equation, each
   parameter to a source, each judgement call to an ADR.

## 7. Explicit non-goals

- **Not a replacement for OnSSET.** OnSSET cost modules and default parameters
  are adapted deliberately so results stay comparable to the published
  literature. The contribution is resolution — building footprints rather than
  1 km raster cells — plus the dispersed-settlement treatment and the
  dual-perspective appraisal that OnSSET does not natively provide.
- **Not an engineering design tool.** It screens and ranks.
- **Not a forecast.** Demand is static by tier; growth enters only through the
  `productive_use` scenario and the DCF growth rate.

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| KPLC/REREC network and meter data are not released | High — served status becomes far less certain | Proximity-based fallback implemented; `require_meter_evidence` run bounds the error (`VALIDATION.md`) |
| Structure filter misclassifies dwellings as ancillary, or vice versa | High — propagates to demand and to every cost | Stratified ground-truth validation; residual error reported as demand uncertainty |
| Provisional cost parameters are mistaken for findings | High — invalidates conclusions | Every provisional value flagged in config and in `ASSUMPTIONS.md`; README states the limitation up front |
| DBSCAN `eps` choice drives the settlement count | Medium — changes the whole result set | `eps`/`MinPts` sweep built into the sensitivity command |
| Straight-line MV distance understates real routing cost | Medium — biases towards grid | Terrain multiplier now; least-cost path routing on the roadmap |
| Static demand overstates off-grid adequacy | Medium | `productive_use` scenario; limitation stated |

## 9. Milestones

| Milestone | Contents | Status |
|---|---|---|
| M1 Framework | Equations implemented, tested, runnable on synthetic data | **Complete** |
| M2 Data acquisition | Footprints, KPLC/REREC layers, DEM, land cover, solar resource | In progress |
| M3 Parameterisation | Replace every provisional parameter with a sourced Kenyan figure | Not started |
| M4 Validation | Ground-truth the structure filter; validate served status against meters | Not started |
| M5 Results | County-wide run, sensitivity, scenarios, figures | Not started |
| M6 Dissemination | Dissertation chapters, summary report, stakeholder dashboard | Not started |

## 10. Open questions

1. Will KPLC release LV and meter data at building resolution, or only MV?
2. Should the demand tier be assigned from typology alone, or should a
   willingness-to-pay or income proxy enter (KNBS income tiers)?
3. Should the prioritisation weights be fixed by the researcher or elicited from
   county stakeholders? They are configurable either way.
4. Is a 20-year analysis period right for all three technologies, given SHS
   assets last ~15 years and grid assets ~30? (Currently: one common period with
   replacements and salvage handling the difference.)
