# Chapter 1: Introduction

## 1.1 Background of the Study

In Sub-Saharan Africa, the energy transition is occurring concurrently with the
accelerated expansion of electricity access. The decisions made are not only
about how many households are electrified but about which technologies supply
new demand. In high-income countries, transition efforts focus on decarbonising
established grids; countries like Kenya face the challenge of expanding access
while ensuring infrastructure investments are cost-efficient, financially
sustainable and aligned with low-carbon development pathways (IEA, 2024; ESMAP,
2019).

Grid extension remains central to electrification strategy, but it is
capital-intensive and slow to deploy in low-density settlements. Settlements
must meet set thresholds to acquire electrification scheme status before a
budget is approved, after which network expansion proceeds systematically:
schemes nearest the existing network are electrified first. Renewable energy
mini-grids and standalone photovoltaic systems offer modular, rapidly deployable
alternatives that lower infrastructure burdens and support renewable
integration.

County-level electrification planning remains largely aggregated and
technology-neutral, with limited integration of spatial heterogeneity into core
decision-making. Spatial electrification work across Africa and Asia shows that
failing to model settlement heterogeneity leads to sub-optimal technology
allocation and higher system costs (Mentis et al., 2017; Dagnachew et al., 2020).

## 1.2 Problem Statement

Despite Kenya's electrification milestones, sub-national planners and
infrastructure investors lack a settlement-level decision-support framework for
determining how unelectrified populations within heterogeneous counties should
be electrified in an optimal and financially sustainable manner.

County governments, REREC, KPLC and private renewable energy developers must
decide whether grid extension, solar mini-grids or standalone photovoltaic
systems are appropriate for different settlement types. Current planning
approaches rely largely on aggregated access statistics and project-based
expansion strategies; they do not systematically identify unelectrified building
clusters using detailed spatial infrastructure data, nor do they estimate
settlement-level electricity demand (Ronoh & WRI, 2025).

In practice, unelectrified homes are implicitly categorised as future
grid-extension candidates despite substantial differences in settlement density,
demand profile, infrastructure distance and investment recovery potential.
Electrification decisions rarely incorporate factual comparison of capital
costs, LCOE, deployment time and financial return across competing technologies.

Consequently, planners and investors have no GIS-driven techno-economic and
financial decision-support framework with which to map unelectrified settlements
using detailed spatial infrastructure data, quantify demand at settlement level,
compare the costs of the three technologies, identify the least-cost option for
each settlement, and assess investment viability from both utility and private
developer perspectives. The absence of such an integrated approach constrains
transparent, evidence-based planning and limits a county like Kajiado in
balancing cost efficiency, renewable deployment and long-term transition goals.

## 1.3 Research Objectives

### 1.3.1 General Objective

To formulate and apply a GIS-aided techno-economic and financial modelling
framework that determines the least-cost and investment-feasible electrification
pathways within the heterogeneous settlements of Kajiado County.

### 1.3.2 Specific Objectives

I. To spatially identify and cluster unelectrified settlements using
high-resolution building footprint data and their proximity to existing medium
and low voltage distribution networks and transformer infrastructure in Kajiado
County.

II. To estimate settlement-level electricity demand based on household counts and
standardised demand tier assumptions.

III. To perform economic analysis of capital costs, long-run marginal costs and
operational costs required for grid extension, solar PV mini-grids and
standalone solar photovoltaic systems across different settlement typologies.

IV. To propose the optimum electrification pathway or technology for each
clustered settlement from both utility and private renewable energy developer
lenses.

## 1.4 Research Questions

I. What approach can be used to spatially identify and classify unelectrified
settlements in Kajiado County using geospatial analysis of building footprints,
medium and low voltage distribution networks, transformer locations and meter
data?

II. What is the approximate electricity demand for each identified settlement or
cluster based on household counts and standardised demand tier assumptions?

III. How do grid extension, solar PV mini-grids and standalone solar photovoltaic
systems compare in light of capital cost, operational cost and levelized cost of
electricity across varied settlement typologies?

IV. Which electrification technology represents the infrastructurally and
financially optimal option for each settlement under varying spatial and
economic conditions, and is time-effective in deployment?

## 1.5 Justification

Electrification planning in Kenya is steadily being implemented at sub-national
level. County governments, REREC, utilities like KPLC and private developers are
compelled to make geographically differentiated investment decisions. In diverse
counties like Kajiado, densely built peri-urban zones coexist with sparsely
populated rural areas, and technology-neutral planning risks sub-optimal
infrastructure investment and delayed access.

Kajiado illustrates a failure mode now common across Kenya's arid and semi-arid
lands. The county reports a relatively high rate of grid presence, yet a large
share of Maasai *manyattas* remain dark because they fall outside scheme
boundaries and below transformer load thresholds. Without a settlement-level
screening tool these last-mile clusters are invisible to budget cycles, and
policy targets such as SDG 7.1.1 remain unmet not for lack of money but for lack
of evidence on where to spend it.

Much of the existing literature, including acknowledged OnSSET applications by
Mentis et al. and Falchetta et al., works at population raster and 1 km grid
resolution. That scale is appropriate for national trade-offs but not for
sub-national procurement decisions. By anchoring the analysis in actual building
footprints, reading the demand tier off building count rather than coarse
population proxies, and marrying a least-cost LCOE comparison with a
dual-perspective NPV/IRR appraisal, this study produces an evidence base that
current continental frameworks cannot deliver. Settlement-level electrification
status makes the invisible visible.

The framework is built for three sets of users with different decision rights.
County planners in Kajiado gain a defended investment sequence they can take to
the County Assembly. REREC and KPLC get a transparent way to rank candidate
schemes, including the impact of household-level connection charges that the
current fee structure imposes. Private renewable energy developers get a
pre-screened pipeline of settlements in which the IRR passes muster without
public subsidy. The unifying benefit is that scarce infrastructure capital is
matched to the settlement that needs it, rather than absorbed by the corridor
that already has it.

## 1.6 Scope

The study is geographically confined to Kajiado County, Kenya, a representative
heterogeneous case characterised by dense peri-urban settlements with sparsely
populated rural interiors. Analysis is at the settlement level, using existing
utility infrastructure and high-resolution building footprint data as the
primary spatial unit. The research focuses exclusively on electricity access
expansion and does not extend to national generation planning, transmission
reinforcement or reliability improvement analysis.

Technically, the study evaluates three pathways: grid extension, solar PV
mini-grids and standalone solar PV systems. Renewable integration is
incorporated through the modelling of solar-based decentralised systems; other
renewable technologies such as wind or hydro are outside the scope. A
GIS-assisted framework integrates building footprints, MV and LV distribution
networks, transformer locations and meter data to identify unelectrified
settlements, assess infrastructure proximity and classify settlements by density
characteristics. The outputs are designed to support county governments, REREC,
KPLC and private developers.

## 1.7 Limitations and Delimitations

### 1.7.1 Limitations

- **Data accuracy.** The analysis relies on publicly available or requested
  datasets, including building footprints, grid data and population statistics.
  Model accuracy is contingent on the accuracy of these inputs. The residual
  misclassification rate of the structure filter (Section 3.4.3) is measured
  against a stratified ground-truth sample and reported as a quantified source
  of uncertainty in demand estimates.
- **Demand projections.** Electricity demand is estimated from standardised
  tiers and does not account for dynamic future load growth or the stimulation
  of productive uses, which may affect long-term financial viability.
- **Cost assumptions.** Technology and infrastructure costs are informed by
  credible literature and industry data for Kenya; they remain subject to market
  volatility, supply chain disruption and inflation.

### 1.7.2 Delimitations

- **Technology focus.** The analysis is restricted to off-grid solar PV
  solutions — mini-grids and SHS — and conventional grid extension, as the most
  prevalent and scalable options in Kenya currently.
- **Geographic confines.** Kajiado was chosen as a representative case of high
  settlement heterogeneity, making the findings and methodology relevant to
  similar Kenyan counties; results are not directly generalisable without
  further study.
- **Analytical focus.** The study develops a cost-minimising techno-economic
  modelling framework for expanding access. It does not model the social and
  political factors influencing technology adoption, nor the macroeconomic
  impacts of electrification.
