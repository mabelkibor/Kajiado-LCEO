# Glossary

Terms and abbreviations as used in this repository and in the dissertation.

## Abbreviations

| | |
|---|---|
| **ArcGIS** | Arc Geographic Information System (Esri) |
| **BESS** | Battery Energy Storage System |
| **BOS** | Balance of System — wiring, mounting, charge controller, installation |
| **CAPEX** | Capital Expenditure |
| **CRF** | Capital Recovery Factor (Equation 8) |
| **DBSCAN** | Density-Based Spatial Clustering of Applications with Noise |
| **DCF** | Discounted Cash Flow |
| **DEM** | Digital Elevation Model |
| **DoD** | Depth of Discharge |
| **DPP** | Discounted Payback Period (Equation 14) |
| **EPRA** | Energy and Petroleum Regulatory Authority (Kenya) |
| **ESMAP** | Energy Sector Management Assistance Program (World Bank) |
| **GHI** | Global Horizontal Irradiance |
| **GIS** | Geographic Information Systems |
| **IRR** | Internal Rate of Return (Equation 13) |
| **KNBS** | Kenya National Bureau of Statistics |
| **KNES** | Kenya National Electrification Strategy |
| **KPLC** | Kenya Power and Lighting Company |
| **LCOE** | Levelized Cost of Electricity (Equations 9, 9a) |
| **LF** | Load Factor |
| **LV** | Low Voltage — below 1 kV |
| **MTF** | Multi-Tier Framework (ESMAP energy access tiers) |
| **MV** | Medium Voltage — 1–33 kV in the Kenyan context |
| **NPC** | Net Present Cost |
| **NPV** | Net Present Value (Equation 12) |
| **OnSSET** | Open Source Spatial Electrification Tool |
| **OPEX** | Operating Expenditure |
| **PR** | Performance Ratio |
| **PSH** | Peak Sun Hours |
| **PV** | Photovoltaic |
| **QGIS** | Quantum Geographic Information System |
| **REREC** | Rural Electrification and Renewable Energy Corporation (Kenya) |
| **SHS** | Solar Home System |
| **WACC** | Weighted Average Cost of Capital |

## Terms

**Ancillary structure.** A detected footprint within a compound that is not a
dwelling — a store, grain silo, shade structure or livestock enclosure. Removed
by the Table 3.3 filter so it does not inflate the household count.

**Boma / manyatta.** Traditional Maasai homestead compound, typically one or
more dwellings together with livestock enclosures and storage structures. The
reason the structure filter exists: a naive footprint count treats a single
homestead as five households.

**Compactness.** `C = 4πA / P²`. Approaches 1 for a circle; falls towards 0 for
elongated or irregular polygons. Distinguishes roofed dwellings from open
enclosures.

**Connection fee.** The one-off charge for the wiring, meter and service drop
required to connect a household — distinct from the ongoing energy tariff. In
Kenya a decisive barrier to take-up even where the network passes nearby, which
is why it is carried as its own term in Equations 5 and 6 and can move between
cost and revenue depending on perspective.

**Core point.** In DBSCAN, a point with at least `MinPts` neighbours within `ε`
(Equation 2). Clusters grow from core points.

**Crossover distance.** The distance from the MV network at which grid
extension stops being the least-cost option for a settlement of a given size.
The single most decision-relevant output of the model.

**Demand tier.** A standardised consumption band (Tier 1–4, following the ESMAP
MTF) assigned to each settlement, determining `d_h` in Equation 3 — from basic
lighting and phone charging through to productive use.

**Dispersed settlement.** A dwelling whose spacing from its neighbours exceeds
the clustering radius; a DBSCAN noise point. In Kajiado, a dispersed pastoralist
homestead. Defaults to SHS under the Equation 10 override — but only after the
micro-cluster test.

**Levelized Cost of Electricity.** The discounted lifetime cost of a system
divided by its discounted lifetime energy output, per unit of energy. Applied
identically across all three technologies here, which is what makes Equation 10
a like-for-like comparison.

**Micro-cluster.** Two or more noise points that are density-connected at the
relaxed radius of 300–500 m. Still eligible for a cost comparison rather than
the standalone default, so the dispersed treatment is a tested outcome rather
than an assumption.

**Mini-grid.** A local generation and distribution system — here solar PV with
battery storage — serving a settlement independently of the national grid.

**Noise point.** In DBSCAN terminology, a point not density-reachable from any
core point. In most clustering applications, data to discard. Here, the object
of study.

**Settlement cluster.** A group of building footprints identified by the
clustering algorithm as sufficiently proximate to be treated as a single unit of
electrification analysis. The model's fundamental unit.

**Solar Home System.** A standalone PV system — panel, battery, basic appliances
— serving a single household independently of any distribution network.

**Subsidy gap.** The present-value grant that would bring a non-viable
settlement to NPV = 0. The number a county budget submission or a
results-based-finance application actually needs.

**Typology.** The settlement classification used throughout — dispersed, small
rural, large rural, peri-urban — assigned from household count and built
density, and driving demand-tier assignment and by-type reporting.
