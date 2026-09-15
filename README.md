# Kajiado-LCEO

**GIS-aided techno-economic modelling of least-cost electrification pathways in Kajiado County, Kenya.**

A settlement-level decision-support model that takes building footprints and
utility network data and returns, for every unelectrified settlement in the
county: how many households it holds, how much electricity it needs, which of
grid extension, a solar PV mini-grid or standalone solar PV serves it at least
cost, and whether that investment is financially viable to a utility and to a
private developer.

This repository is the computational side of the MSc dissertation *GIS-Aided
Techno-Economic Modelling of Least Cost Electrification Pathways in Kajiado
County in Kenya* (Mabel Chelagat Kibor, Strathmore University, School of
Computing and Engineering Sciences). Every modelling module implements a
numbered governing equation from Chapter 3 of the proposal and cites it in its
docstring; [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) is the equation-by-equation
reference, and [`docs/SPEC.md`](docs/SPEC.md) the technical specification.

---

## Why this exists

Kenya reports a high rate of grid presence in Kajiado, yet a large share of
Maasai *manyattas* remain unlit: they fall outside scheme boundaries and below
transformer load thresholds. Planning that works from aggregated access
statistics cannot see them. Continental models such as OnSSET work at 1 km
raster resolution — right for national trade-offs, too coarse for a county
procurement decision.

This model works from **actual building footprints**. It reads demand off
building counts rather than population proxies, keeps dispersed homesteads in
the analysis instead of discarding them as noise, and pairs the least-cost LCOE
comparison with a dual-perspective NPV/IRR appraisal, so that a county planner,
REREC/KPLC and a private developer each get the number their decision actually
turns on.

## What it produces

| Output | File | What it answers |
|---|---|---|
| Settlement clusters | `outputs/tables/settlement_clusters.csv` | Where are the unelectrified settlements, and how big are they? |
| Technology comparison | `outputs/tables/least_cost_technology.csv` | What does each option cost per kWh here, and which wins? |
| Financial viability | `outputs/tables/financial_viability.csv` | Is it bankable — to a utility, to a developer, or neither? |
| Prioritised plan | `outputs/tables/prioritised_electrification_plan.csv` | In what order should the county spend its money? |
| Run summary | `outputs/reports/run_summary.json` | Headline figures plus full provenance of the run |
| Figures | `outputs/figures/*.png` | The LCOE-versus-distance crossover, technology mix, CAPEX composition, viability scatter |

## Quick start

```bash
git clone https://github.com/mabelkibor/kajiado-lceo.git
cd kajiado-lceo
python -m pip install -e ".[dev]"

lceo sample-data          # synthetic county — the real layers are restricted
lceo run                  # Stages 1-5 under the baseline scenario
lceo figures              # render the result figures
```

Or with `make`:

```bash
make install-dev && make sample && make run && make figures
```

> **The sample data is synthetic.** It reproduces the *structure* of the problem
> — a dense peri-urban corridor, mid-sized villages at varying distance from the
> MV network, dispersed pastoralist homesteads, ancillary structures inside
> compounds — so that the code is runnable and testable by anyone. It says
> nothing whatsoever about Kajiado County. Real results require the layers
> listed in [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

### Running against real data

1. Obtain the layers in [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md); the KPLC
   and REREC network and meter data require a data-sharing agreement
   ([`docs/ETHICS_AND_DATA_GOVERNANCE.md`](docs/ETHICS_AND_DATA_GOVERNANCE.md)).
2. Place them at the paths in `config/default.yaml` under `inputs:`, matching
   the schema in [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).
3. Replace the provisional cost and demand parameters — every one is flagged in
   [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md) — with sourced Kenyan figures.
4. `lceo run --scenario baseline`.

## How the model works

Five stages, each implementing the governing equations of Section 3.5.3:

```
  building footprints, MV/LV network, transformers, meters
        │
  ┌─────▼─────────────────────────────────────────────────────┐
  │ Stage 1  Structure filtering + served status               │  Table 3.3
  │          drop stores and enclosures; find who is unlit     │
  ├───────────────────────────────────────────────────────────┤
  │ Stage 2  DBSCAN settlement clustering                      │  Eq. 1-2
  │          villages become clusters; homesteads become noise │
  │          — and noise is kept, not discarded                │
  ├───────────────────────────────────────────────────────────┤
  │ Stage 3  Demand-tier estimation                            │  Eq. 3-4
  │          annual energy E_c and coincident peak P_c,peak    │
  ├───────────────────────────────────────────────────────────┤
  │ Stage 4  Cost all three options, pick the cheapest         │  Eq. 5-10
  │          grid / mini-grid / standalone, compared on LCOE   │
  ├───────────────────────────────────────────────────────────┤
  │ Stage 5  Discounted cash flow, twice                       │  Eq. 11-14
  │          utility view and private-developer view           │
  └─────┬─────────────────────────────────────────────────────┘
        ▼
  settlement clusters · demand · least-cost technology · viability · priority plan
```

The heart of it is Equation 10: `Technology*_c = argmin_i LCOE_i,c`. The result
that matters is the **crossover** — the distance from the MV network at which
grid extension stops being cheapest for a settlement of a given size. That
crossover is what `outputs/figures/fig_lcoe_vs_distance.png` shows, and it is
what a county investment sequence should be built on.

### Dispersed homesteads

Most spatial electrification models discard DBSCAN noise points. Here they are
the point: a noise point is a dispersed pastoralist homestead, and in Kajiado
those are a large share of the unelectrified population. Equation 10 defaults
them to standalone PV — but only after re-clustering at a relaxed 300–500 m
radius and testing a micro-mini-grid against aggregated SHS on cost. Every
settlement's `decision_reason` column records which path decided it, so the
share of the plan resting on the override rather than on a comparison is
visible rather than buried.

## Commands

| Command | Purpose |
|---|---|
| `lceo sample-data` | Generate the synthetic county into `data/raw/` |
| `lceo run [--scenario ID]` | Run Stages 1–5 and write the outputs |
| `lceo sensitivity` | Sweep the parameters in `config/techno_economic.yaml` |
| `lceo compare-scenarios` | Run every scenario side by side |
| `lceo validate-config [--key PATH]` | Print the merged configuration |
| `lceo figures` | Render the standard result figures |

## Scenarios

Scenarios are deep-merged over the base configuration, so a scenario file states
only what it changes.

| Scenario | Question it answers |
|---|---|
| `baseline` | Central case |
| `no_connection_subsidy` | What if households bear the full connection fee? |
| `high_grid_capex` | Where does the crossover move if line costs rise 40%? |
| `low_battery_cost` | How much does continued storage cost decline change the mix? |
| `productive_use` | What if demand stimulation lifts every typology one tier? |

## Configuration

Nothing numeric is hard-coded. A run is fully described by the config files, the
scenario, and the input data.

```
config/
├── default.yaml           # master: project, paths, inputs, outputs, includes
├── clustering.yaml        # Table 3.3 filter, DBSCAN eps/MinPts, typology
├── demand_tiers.yaml      # Tier 1-4 consumption, load factors, assignment rules
├── techno_economic.yaml   # CAPEX/OPEX for all three technologies
├── finance.yaml           # discount rates, tariffs, hurdle rates, perspectives
└── scenarios/             # overlays
```

## Repository layout

```
├── config/            Model parameters (see above)
├── data/              Inputs — git-ignored; provenance in docs/DATA_SOURCES.md
├── docs/              PRD, spec, methodology, assumptions, ADRs, chapter drafts
├── notebooks/         Exploratory analysis
├── outputs/           Generated tables, figures, maps, reports — git-ignored
├── qgis/              Layer styles and project notes for cartography
├── scripts/           Utilities (e.g. deriving SHS kit costs from sizing)
├── src/kajiado_lceo/  The model
│   ├── geo/           Equation 1 — haversine distance, nearest-network queries
│   ├── preprocessing/ Table 3.3 structure filter; served-status tagging
│   ├── clustering/    Equation 2 — DBSCAN, relaxed pass, typology
│   ├── demand/        Equations 3-4 — energy and peak demand
│   ├── costs/         Equations 5-9 — CAPEX, CRF, LCOE
│   ├── optimisation/  Equation 10 — least-cost rule and dispersed override
│   ├── finance/       Equations 11-14 — NPV, IRR, discounted payback
│   ├── viz/           Figures and maps
│   └── pipeline.py    Section 3.5.5 — the five-stage sequence
└── tests/             145 tests, including equation-level checks
```

## Development

```bash
make test        # pytest
make lint        # ruff
make typecheck   # mypy
make format      # ruff format + autofix
pre-commit install
```

Tests assert the equations directly, not just that code runs: the Capital
Recovery Factor against its textbook value, one degree of latitude against
`R·π/180`, the two LCOE forms of Equations 9 and 9a against each other, IRR
against the rate that zeroes NPV, and the SHS kit costs against the system
sizing that must justify them.

## Status and honest limitations

**Alpha.** The modelling framework is complete and tested end to end; it has
**not** yet been run against real Kajiado data.

Before any number from this repository is reported as a finding:

- **Every cost and demand parameter is provisional.** They come from OnSSET
  defaults, IRENA reporting and indicative market figures, not from Kenyan
  primary sources. Each is listed in [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md)
  with the source it must be replaced by.
- **Served status is inferred from proximity, not from a connection register.**
  The bound on that inference is quantified in
  [`docs/VALIDATION.md`](docs/VALIDATION.md).
- **The structure filter is a heuristic, not a classifier.** Its residual error
  rate must be measured on a stratified ground-truth sample and reported as
  demand uncertainty.
- **Demand is static by tier.** Load growth and productive-use stimulation are
  handled only through the `productive_use` scenario.

## Citation

See [`CITATION.cff`](CITATION.cff).

## Licence

Code is MIT ([`LICENSE`](LICENSE)). The dissertation text in `docs/dissertation/`
is © Mabel Chelagat Kibor and Strathmore University; see the licence file for
terms. Input data remains under the licence of its provider.
