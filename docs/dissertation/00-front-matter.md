# Front matter

**GIS-Aided Techno-Economic Modelling of Least Cost Electrification Pathways in Kajiado County in Kenya**

Mabel Chelagat Kibor · Admission No. 059007
Supervisor: Dr. Eng. S. Roy Orenge

Submitted in partial fulfilment of the requirements for the Master of Science in
Sustainable Energy Transition, School of Computing and Engineering Sciences,
Strathmore University, Nairobi, Kenya.

---

## Declaration

I declare that this work has not been previously submitted and approved for the
award of a degree by this or any other University. To the best of my knowledge
and belief, the dissertation contains no material previously published or
written by another person except where due reference is made in the dissertation
itself.

© No part of this dissertation may be reproduced without the permission of the
author and Strathmore University.

---

## Abstract

Sub-Saharan Africa is undergoing an energy transition that requires accelerated
electricity access alongside cost-efficient, financially sustainable and
low-carbon infrastructure investment. Kenya faces the particular challenge of
expanding electrification beyond conventional grid extension — capital-intensive
and slow to deploy in low-density areas — towards modular alternatives such as
renewable energy mini-grids and standalone photovoltaic systems.

Current electrification planning in the country does not adequately integrate
spatial heterogeneity into core decision-making, leading to sub-optimal
investments and delayed access in rural and semi-urban communities. Sub-national
planners and investors lack a granular, settlement-level decision-support
framework. Existing approaches rely on aggregated statistics, failing to
systematically identify unelectrified building clusters or to estimate
settlement-level demand; electrification decisions rarely incorporate a factual
comparison of capital costs, the Levelized Cost of Electricity, deployment
timelines and financial return metrics across competing technologies.

The general objective of this study is to formulate and apply a GIS-aided
techno-economic and financial modelling framework that determines the
least-cost and investment-sound electrification pathways within the
heterogeneous settlements of Kajiado County.

The study adopts a quantitative, experimental research design centred on
simulation and techno-economic modelling, drawing on high-resolution building
footprints, utility infrastructure data, topographic and land-use data, and
techno-economic parameters for competing technologies. A bottom-up,
optimisation-based model is developed around four components: a spatial
clustering function grouping building footprints into settlement units; a
demand-tier estimation function; a least-cost optimisation routine computing and
comparing the LCOE across grid extension, solar PV mini-grids and standalone
systems; and a discounted-cash-flow financial viability function evaluated from
both utility and private-developer perspectives. Each component is underpinned by
explicit governing equations rather than by software alone.

Modelling and simulation are conducted using QGIS/ArcGIS for spatial analysis and
Python for custom algorithmic implementation, selectively adapting cost modules
and default parameters from the Open Source Spatial Electrification Tool
(OnSSET) where they improve comparability with the existing literature. The
expected outcome is a robust, equation-based framework that spatially identifies
and clusters unelectrified settlements — including very low-density and
dispersed homesteads — estimates their demand net of non-residential structures,
and evaluates the capital costs, LCOE and operational costs of competing options,
inclusive of household connection fees, across settlement typologies.

---

## Lists

- **Abbreviations** — see [`../GLOSSARY.md`](../GLOSSARY.md)
- **Definition of terms** — see [`../GLOSSARY.md`](../GLOSSARY.md)
- **Equations 1–14** — see [`../METHODOLOGY.md`](../METHODOLOGY.md)

### Figures

| | |
|---|---|
| Figure 3.1 | Location of the study area relative to a subset of the street map of Kenya |
| Figure 3.2 | Methodology flowchart for the GIS-aided techno-economic and financial modelling framework |
| Figure 4.1 | LCOE by technology against distance to the MV network *(generated: `fig_lcoe_vs_distance.png`)* |
| Figure 4.2 | Least-cost technology by settlement typology *(generated: `fig_technology_mix.png`)* |
| Figure 4.3 | Capital cost composition of the least-cost plan *(generated: `fig_capex_breakdown.png`)* |
| Figure 4.4 | Financial viability by perspective *(generated: `fig_viability.png`)* |

### Tables

| | |
|---|---|
| Table 2.1 | Empirical review: GIS-aided techno-economic electrification planning |
| Table 3.1 | Independent and dependent variables |
| Table 3.2 | Primary datasets, their roles and authoritative sources |
| Table 3.3 | Heuristic criteria for filtering non-residential structures |
| Table 3.4 | Notation used in the governing equations |
| Table 4.1 | Settlement clusters by typology |
| Table 4.2 | LCOE comparison by technology and typology |
| Table 4.3 | Financial viability by perspective |
| Table 4.4 | Prioritised electrification plan |
