# Data sources

Implements Table 3.2 of the proposal. No data is committed to this repository
(see [`ETHICS_AND_DATA_GOVERNANCE.md`](ETHICS_AND_DATA_GOVERNANCE.md)); this file
is the provenance record.

## Required layers

### 1. Building footprints — **critical path**

| | |
|---|---|
| **Role** | Identify unelectrified structures and settlement morphology (Stages 1–2) |
| **Source** | [Google Open Buildings](https://sites.research.google/open-buildings/) v3 (CC BY 4.0 / ODbL); [Microsoft Building Footprints](https://planetarycomputer.microsoft.com/dataset/ms-buildings) (ODbL) |
| **Needed** | Polygon or centroid, area, ideally perimeter; county-wide coverage |
| **Access** | Open |
| **Caveats** | Trained to detect built-up structure in general, not dwellings — hence the Section 3.4.3 filter. Detection confidence falls for thatched roofs and small structures, which biases *against* detecting exactly the rural dwellings this study cares about. Filter by the confidence field and report the threshold used. |

### 2. Utility infrastructure — **restricted**

| | |
|---|---|
| **Role** | Grid proximity (`D_c`, Equation 5), available transformer capacity, served status |
| **Source** | KPLC (MV/LV network, transformers, meters); REREC (rural schemes, planned extensions) |
| **Needed** | MV lines with voltage and energisation status; LV lines; transformer points with rated and spare capacity; meter locations (aggregated, no customer identifiers) |
| **Access** | **Data-sharing agreement required.** Request through the Strathmore supervisor with a stated research purpose. |
| **Caveats** | Coverage and positional accuracy vary by region and vintage. Missing LV segments cause a building to be classed unelectrified when it is connected. Record the data vintage — a 2023 extract will not show 2025 schemes. |
| **Fallback** | [Gridfinder](https://gridfinder.org/) predicted MV lines, and OpenStreetMap `power=line` / `power=minor_line`. Both are inferred and less accurate; using them materially changes what "unelectrified" means and must be declared. |

### 3. Topography and land cover

| | |
|---|---|
| **Role** | Terrain-related grid extension cost; site suitability |
| **Source** | SRTM 30 m DEM (NASA, public domain); Copernicus DEM (ESA); ESA WorldCover 2021 10 m (CC BY 4.0); RCMRD regional layers |
| **Access** | Open |
| **Status** | The terrain *multiplier* is implemented (`technologies.grid.terrain_multiplier`); DEM-derived slope classification is not yet wired in (PRD F-19). |

### 4. Solar resource

| | |
|---|---|
| **Role** | Peak sun hours for PV sizing (Equation 6) |
| **Source** | [Global Solar Atlas](https://globalsolaratlas.info/) (World Bank/Solargis, CC BY 4.0); NASA POWER |
| **Access** | Open |
| **Current use** | A single county-wide value (5.6 kWh/m²/day). Kajiado's GHI varies modestly across its ~22,000 km²; a per-settlement lookup is on the roadmap. |

### 5. Techno-economic parameters

| | |
|---|---|
| **Role** | Every cost term in Equations 5–7 |
| **Source** | EPRA tariff and cost filings; IRENA *Renewable Power Generation Costs*; World Bank ESMAP and Mission 300; KPLC connection-fee schedules; local supplier quotations |
| **Access** | Mixed — published reports open; supplier quotations require a market survey |
| **Status** | **All provisional.** Every value is listed in [`ASSUMPTIONS.md`](ASSUMPTIONS.md) with the source that must replace it. |

### 6. Socio-economic

| | |
|---|---|
| **Role** | Demand tier calibration, willingness to pay, ability to meet connection fees |
| **Source** | KNBS Census 2019 and Kenya Integrated Household Budget Survey; [WorldPop](https://www.worldpop.org/) |
| **Access** | Open |
| **Current use** | Demand tiers are assigned by settlement typology, not by measured income. Replacing that with a KNBS-calibrated assignment is an open question in the PRD. |

## Layer register

Maintain this table as data is obtained. It is the evidence for the provenance
statement in the dissertation.

| Layer | Source | Version / vintage | Licence | Obtained | Stored at | Notes |
|---|---|---|---|---|---|---|
| Building footprints | | | | | `data/raw/` | |
| MV lines | | | | | `data/raw/` | |
| LV lines | | | | | `data/raw/` | |
| Transformers | | | | | `data/raw/` | |
| Meters | | | | | `data/raw/` | |
| County boundary | | | | | `data/external/` | |
| DEM | | | | | `data/external/` | |
| Land cover | | | | | `data/external/` | |
| Solar resource | | | | | `data/external/` | |
| Cost parameters | | | | | `config/` | |

## Preparation checklist

- [ ] Clip every layer to the Kajiado County boundary
- [ ] Reproject to EPSG:4326 for storage; EPSG:32737 (UTM 37S) for area and length
- [ ] Verify footprint area units are m², not degrees or ft²
- [ ] Record the footprint confidence threshold applied
- [ ] Check MV/LV topology for gaps — a missing segment silently changes `D_c`
- [ ] Confirm meter coordinates are building-level, not transformer- or feeder-level
- [ ] Strip all customer identifiers from meter data before it enters `data/`
- [ ] Record every vintage in the register above
