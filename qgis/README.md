# QGIS

Python produces the numbers; QGIS produces the maps that go to county
decision-makers. This directory holds the cartographic side.

| Directory | Contents |
|---|---|
| `projects/` | `.qgz` project files (git-ignored; large and binary) |
| `styles/` | `.qml` layer styles, committed so map symbology is reproducible |

## Loading results

Model outputs are CSV with `latitude`/`longitude` columns, so they load directly:

1. **Layer → Add Layer → Add Delimited Text Layer**
2. Select `outputs/tables/settlement_clusters.csv`
3. Point geometry: X = `longitude`, Y = `latitude`, CRS = EPSG:4326
4. Apply a style from `styles/`

Reproject to **EPSG:32737 (UTM 37S)** for any area or distance measurement in
QGIS; keep EPSG:4326 for storage and interchange.

## Suggested map set

| Map | Layer | Symbology |
|---|---|---|
| Unelectrified settlements | `settlement_clusters.csv` | Graduated by `households`; categorised by `typology` |
| Least-cost technology | `least_cost_technology.csv` | Categorised by `least_cost_technology` |
| LCOE surface | `least_cost_technology.csv` | Graduated by `least_cost_lcoe` |
| Investment priority | `prioritised_electrification_plan.csv` | Graduated by `priority_rank` |
| Viability | `financial_viability.csv` | Categorised by `requires_public_support` |

Overlay the MV/LV network and the county boundary on each.

## Cartographic notes

- **Never publish building-level points.** Map settlement centroids only, per
  [`../docs/ETHICS_AND_DATA_GOVERNANCE.md`](../docs/ETHICS_AND_DATA_GOVERNANCE.md).
- Keep the technology colours consistent with the generated figures — grid
  `#1f4e79`, mini-grid `#e08214`, standalone `#2e8b57` (`viz/charts.py`) — so a
  reader moving between the map and the charts is not re-learning the key.
- Label any map built on provisional parameters as provisional.
