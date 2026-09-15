# Chapter 3: Methodology

> The full statement of Equations 1–14, with notation and implementation notes,
> is in [`../METHODOLOGY.md`](../METHODOLOGY.md). This chapter is the narrative;
> that document is the reference, and it is generated alongside the code so the
> two cannot drift apart.

## 3.1 Introduction

This chapter outlines the research methodology employed to address the
electrification planning challenge in Kajiado County. Where Chapter 1 defined the
problem of aggregated, technology-neutral planning, and Chapter 2 identified the
lack of detailed infrastructure integration and settlement-density heterogeneity
in existing models, this chapter sets out the response: a systematic process for
identifying unelectrified building clusters, quantifying their demand, and
applying a GIS-aided techno-economic and financial modelling framework
underpinned throughout by explicit governing equations.

## 3.2 Research Design

The study adopts a quantitative, experimental design centred on simulation and
techno-economic modelling, investigating the relationship between spatial
settlement characteristics (independent variables) and the resulting optimal
technology choice and financial performance (dependent variables). The
experimental character is realised through a custom modelling framework that
simulates three pathways and, by manipulating settlement density, distance to
the existing MV/LV network and demand-tier assumptions, observes the impact on
LCOE and investment return metrics.

**Table 3.1 — Independent and dependent variables**

| Type | Category | Variables |
|---|---|---|
| Independent | Geospatial | Distance to existing MV/LV grid; building density and settlement morphology; terrain and land-cover constraints |
| Independent | Economic | Technology costs (CAPEX/OPEX); fuel prices and solar irradiance; electricity demand targets; household connection fees |
| Dependent | Least-cost technology | Grid extension; solar mini-grids; standalone PV |
| Dependent | Financial viability | LCOE; NPV; payback period and IRR |

Implemented as: independent variables are configuration
([`ASSUMPTIONS.md`](../ASSUMPTIONS.md)) and input data; dependent variables are
output columns ([`DATA_DICTIONARY.md`](../DATA_DICTIONARY.md)). Manipulation is
performed by the scenario and sensitivity machinery (`lceo sensitivity`,
`lceo compare-scenarios`).

## 3.3 Case Study Description: Kajiado County

Kajiado County is selected because its settlement environment is unusually
heterogeneous, making it the appropriate place to test the framework. It covers
roughly 21,903 km², with large differences between its northern peri-urban areas
and southern rural areas. Peri-urban clusters such as Kitengela, Ngong and
Kajiado town are characterised by high building density and rapid population
growth and lie close to the national grid. Large parts of the county are sparsely
populated, with settlements consisting mainly of isolated homesteads or small
clusters far from infrastructure. This diversity enables the framework to be
tested on its central task: differentiating grid-extension candidates from those
better suited to decentralised solutions. Kajiado reflects the wider challenge
across Sub-Saharan Africa, where one-size-fits-all electrification plans have
often failed to deliver affordable or timely access.

*Figure 3.1 — Location of the study area relative to a subset of the street map
of Kenya.*

## 3.4 Data Collection and Requirements

### 3.4.1 Required data layers

High-resolution building footprints; MV and LV distribution lines, transformer
locations and meter data; DEM and land cover; and techno-economic parameters for
solar PV modules, batteries, inverters and grid components.

**Table 3.2** — datasets, roles and authoritative sources: see
[`../DATA_SOURCES.md`](../DATA_SOURCES.md), which extends the proposal table with
access routes, licences, caveats and a layer register.

### 3.4.2 Data collection strategy

Secondary data is used primarily, from official government reports, utility
databases and credible international organisations, supplemented by primary data
where necessary — notably local market price surveys for renewable energy
components. The use of secondary data is justified by its reliability and by the
scale of the study area, which makes primary collection impractical for every
building cluster.

### 3.4.3 Filtering non-residential structures

AI-derived footprint datasets detect built-up area in general and do not
distinguish a dwelling from a livestock enclosure, grain store or shade
structure. This is material in Kajiado's rural wards, where homestead compounds
combine one or more dwellings with several smaller ancillary structures.
Counting every footprint as a household would systematically overestimate
household numbers and, through Equation 3, settlement demand.

A multi-criterion heuristic filter is therefore applied before clustering:
footprint area, shape compactness, roofing-material signature where image
quality allows, and compound-level co-location logic. The filter is **not a
final classifier**. Its residual error rate is estimated through ground-truth
validation on a stratified sample of clusters and reported as a quantified
source of uncertainty in demand estimates (Section 1.7.1).

**Table 3.3** — the criteria and their decision rules: implemented in
`preprocessing/footprint_filter.py`; thresholds in `config/clustering.yaml`;
attrition reported per criterion in `structure_filter_report.csv`.

## 3.5 Model Development and Algorithms

### 3.5.1 Summary of the model algorithms

1. **Spatial clustering (DBSCAN)** — groups footprints into settlement clusters
   on a density threshold (Equations 1–2).
2. **Demand-tier estimation** — assigns a demand profile from household counts
   and standardised tiers (Equations 3–4).
3. **Least-cost optimisation** — computes the LCOE for all three technologies and
   selects the minimum subject to the decision rule (Equations 5–10).
4. **Financial viability** — computes NPV, IRR and payback for the selected
   technology from both perspectives (Equations 11–14).

### 3.5.2 Methodology flowchart

*Figure 3.2 — Methodology flowchart.* The implemented sequence is documented in
[`../ARCHITECTURE.md`](../ARCHITECTURE.md) § Data flow.

### 3.5.3 Governing equations

Stated in full, with notation (Table 3.4), in
[`../METHODOLOGY.md`](../METHODOLOGY.md).

### 3.5.4 Least-cost decision rule and the dispersed-settlement override

For clusters satisfying Equation 2, the optimal technology minimises the LCOE
among the three candidates. For points labelled noise — indicating inter-dwelling
spacing beyond the clustering radius, consistent with dispersed pastoralist
homesteads — the model applies an override to standalone PV, because both grid
extension and mini-grid distribution costs per household rise sharply and
typically become prohibitive at that spacing.

This default is not applied blindly. Before finalising it, the model checks
whether two or more noise points lie within a relaxed radius of 300–500 m,
re-applying Equation 2. Where such a micro-cluster exists, the model computes and
compares the LCOE of a short single-line micro-mini-grid against aggregated SHS
cost for the same households and assigns whichever is least-cost. This ensures
the dispersed-settlement treatment is itself a tested outcome of the least-cost
framework rather than an untested assumption.

> **Implementation note.** Read literally, the micro-cluster comparison excludes
> grid extension. The implementation keeps grid in the comparison by default, so
> that a micro-cluster beside an existing MV line is not denied the cheapest
> option by category rather than by evidence — which is what this section's own
> "tested outcome" requirement demands. The behaviour is configurable and both
> branches are tested. See
> [ADR 0004](../adr/0004-micro-cluster-grid-eligibility.md).

### Financial viability

Once the least-cost technology is identified, its viability is assessed by
discounted cash flow from both perspectives. Household connection fees enter the
cash flow explicitly: where a utility or REREC subsidises the connection, the fee
is a cost within CAPEX (Equations 5–6); where the household or private developer
bears it directly, it is a one-off revenue inflow to the developer in year zero,
`CF₀ = H_c·Fee_household − CAPEX_dev,c`.

A settlement-technology pairing is viable from the utility perspective where
NPV ≥ 0 or IRR ≥ WACC; failing that, the cluster is flagged as requiring REREC or
public subsidy support, with the subsidy gap quantified. From the
private-developer perspective, viability additionally requires an IRR at or above
the hurdle rate typically demanded by Sub-Saharan African mini-grid developers,
of the order of 15–20%.

### 3.5.5 From inputs to outputs: the full modelling sequence

Five linked stages, each taking a defined input, applying one or more equations,
and producing a defined output. Stated in
[`../METHODOLOGY.md`](../METHODOLOGY.md) § Stage sequence; implemented in
`pipeline.py`.

The final outputs are: (i) settlement clusters as spatial units, including
dispersed homesteads; (ii) the demand tier and annual/peak demand of each;
(iii) the optimal technology and its LCOE; (iv) financial viability from both
perspectives; and (v) a prioritised electrification plan for Kajiado County
ranking clusters by viability and deployment time-effectiveness.

## 3.6 Choice of Simulation Software and Framework

The equations define the method; the tools implement it at county scale.
QGIS/ArcGIS is used for spatial integration, visual checking and the maps that go
to county decision-makers. Python (pandas, NumPy, scikit-learn, SciPy) implements
the equations directly as code and iterates over the full settlement set, which
is not practical in spreadsheet-based tools.

OnSSET provides a validated, peer-reviewed code base for geospatial least-cost
electrification logic, tested and published across Sub-Saharan Africa, and
adopting selected OnSSET cost modules and default parameter tables makes these
results more comparable to the literature reviewed in Chapter 2. However,
OnSSET's native implementation works at raster-cell resolution and does not, in
its standard form, ingest building-footprint vector data, apply the structure
filtering of Section 3.4.3, run the dispersed-settlement override of Equation 10,
or perform the dual-perspective discounted cash flow of Equations 11–14. Python
is therefore used as the development layer in which selected OnSSET modules and
defaults are imported and adapted. This is consistent with OnSSET's framing as an
open, flexible tool rather than a black box (Mentis et al., 2017). See
[ADR 0003](../adr/0003-adapt-onsset-rather-than-extend-it.md).

## 3.7 Data Analysis

- **Techno-economic analysis** — comparing LCOE across settlement typologies to
  identify cost crossover points between grid and off-grid solutions.
- **Financial analysis** — evaluating NPV and IRR to determine which settlements
  are investment-ready for private developers and which require public or REREC
  support.
- **Sensitivity analysis** — testing robustness against variation in demand
  growth, component costs, interest rates and the level and subsidy share of the
  household connection fee (`lceo sensitivity`).
- **Comparative analysis** — assessing deployment timelines to identify the most
  time-effective pathway for meeting access targets.

## 3.8 Research Quality

Validation compares the model's identification of electrified areas against
actual utility meter data, and validates the structure-filtering heuristic
against a stratified ground-truth sample. Reliability rests on standardised,
peer-reviewed techno-economic parameters and open-source frameworks. Objectivity
requires that the optimisation of Equation 10 be purely data-driven and free from
political or institutional bias.

The full plan, with eight named checks and their record, is in
[`../VALIDATION.md`](../VALIDATION.md).

## 3.9 Ethical Considerations

Privacy: all utility and building data is kept private, and no personally
identifiable information is used. Integrity: findings are verified and reported
as computed, including where they contradict existing policy assumptions. Social
impact: the research is grounded in universal, equitable energy access as a
cornerstone of Kajiado County's development.

Detail in [`../ETHICS_AND_DATA_GOVERNANCE.md`](../ETHICS_AND_DATA_GOVERNANCE.md).

## 3.10 Dissemination of Results

To the academic community through the dissertation and potential peer-reviewed
articles; to policy makers through a summary report and a spatial
decision-support dashboard shared with the Kajiado County Government, REREC and
KPLC; and to industry through findings on financial viability presented to
private developers and investors.

## 3.11 Summary

The chapter has set out a bottom-up, equation-based modelling framework operating
at building-footprint resolution, in five stages from structure filtering to
dual-perspective financial appraisal. Its distinguishing features against the
reviewed literature are its spatial resolution, its explicit retention and
testing of dispersed settlements, and its treatment of the household connection
fee as a first-class term whose incidence can be varied by perspective.
