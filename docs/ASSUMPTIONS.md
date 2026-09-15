# Assumptions register

Every numeric assumption in the model, where it came from, and what must replace
it before results are reportable.

> **Status: all techno-economic and demand parameters are PROVISIONAL.**
> They are drawn from OnSSET defaults, IRENA cost reporting and indicative
> market figures — sufficient to exercise and test the framework, insufficient
> to support a finding about Kajiado County. This is limitation L-01 in
> [`SPEC.md`](SPEC.md) and milestone M3 in [`PRD.md`](PRD.md).

**Status key:** 🔴 provisional, must be replaced · 🟡 defensible, should be
calibrated · 🟢 structural or derived, not a free parameter

---

## A. Structural and methodological

| ID | Assumption | Value | Status | Rationale / replacement |
|---|---|---|---|---|
| A-01 | Earth is a sphere of radius 6,371 km | 6371.0 km | 🟢 | Ellipsoidal correction is <0.5%, immaterial against cost uncertainty |
| A-02 | One dwelling houses one household | 1.0 | 🟡 | Kajiado's mean household size and multi-household compounds (KNBS 2019) may warrant >1 |
| A-03 | A building within 300 m of an LV line is served | 300 m | 🟡 | A proxy, not a fact. Bound it with the `require_meter_evidence` run — see [`VALIDATION.md`](VALIDATION.md) |
| A-04 | A transformer with spare capacity serves within 600 m | 600 m | 🟡 | Calibrate against KPLC LV design practice |
| A-05 | Settlement area = lat/lon bounding box, floored at 1 ha | — | 🟡 | Overstates area for L-shaped settlements; a convex hull would be tighter |
| A-06 | Internal network length `L = a·√(H·A) + b·H` | a=0.75/0.80, b=0.02/0.015 km | 🔴 | Calibrate against as-built KPLC/REREC scheme drawings |
| A-07 | SHS kit cost derives from tier consumption | See `sizing_basis` | 🟢 | Derived, not quoted — `scripts/derive_shs_kit_costs.py`; consistency is asserted by test |
| A-08 | Grid excluded beyond 50 km of MV | 50 km | 🟡 | A feasibility cut-off; the LCOE would reject it anyway at that distance |
| A-09 | Mini-grids require ≥15 households | 15 | 🟡 | Below this an operator, tariff and network are not credible. Check against ERC/EPRA mini-grid licensing thresholds |
| A-10 | Micro-clusters may still take grid extension | `true` | 🟢 | Deliberate; see [ADR 0004](adr/0004-micro-cluster-grid-eligibility.md) |
| A-11 | One 20-year analysis period for all technologies | 20 yr | 🟡 | Asset lives differ (15/20/30). Handled by replacements and salvage; test the period in sensitivity |

## B. Clustering (Equations 1–2)

| ID | Assumption | Value | Status | Rationale / replacement |
|---|---|---|---|---|
| B-01 | Primary neighbourhood radius ε | 75 m | 🟡 | Proposal range 50–100 m. **Results are sensitive to this** — always report the sweep |
| B-02 | Core-point threshold MinPts | 4 | 🟡 | Proposal range 3–5 |
| B-03 | Relaxed radius for micro-clusters | 400 m | 🟡 | Proposal range 300–500 m |
| B-04 | Relaxed MinPts | 2 | 🟢 | "Two or more noise points", Section 3.5.4 |
| B-05 | Peri-urban density threshold | 300 bldg/km² | 🔴 | Calibrate against Kitengela/Ngong observed densities |
| B-06 | Typology household breaks | 2 / 50 / 500 | 🔴 | Currently judgement. Derive from the observed county size distribution |

## C. Structure filtering (Table 3.3)

| ID | Assumption | Value | Status | Rationale / replacement |
|---|---|---|---|---|
| C-01 | Minimum habitable area | 7 m² | 🟡 | Proposal indicates 6–9 m². Test the range; it drives `H_c` directly |
| C-02 | Maximum dwelling area | 1,200 m² | 🟡 | Above this: institutional or commercial |
| C-03 | Minimum compactness | 0.45 | 🔴 | Calibrate on labelled Kajiado footprints, not assumed |
| C-04 | Compound radius | 12 m | 🟡 | Proposal indicates 10–15 m |
| C-05 | Max dwellings per compound | 3 | 🟡 | "Largest 1–3 structures", Table 3.3 |
| C-06 | Roof signature disabled | `false` | 🟢 | Requires sub-metre imagery not currently held |
| C-07 | Ground-truth sample fraction | 7.5% | 🟢 | Proposal indicates 5–10%, stratified |

## D. Demand (Equations 3–4)

| ID | Assumption | Value | Status | Rationale / replacement |
|---|---|---|---|---|
| D-01 | Tier 1 consumption | 0.20 kWh/hh/day | 🔴 | ESMAP MTF via OnSSET. Recalibrate on KNBS/KIHBS Kajiado data |
| D-02 | Tier 2 consumption | 1.00 kWh/hh/day | 🔴 | As above |
| D-03 | Tier 3 consumption | 3.40 kWh/hh/day | 🔴 | As above |
| D-04 | Tier 4 consumption | 6.80 kWh/hh/day | 🔴 | As above |
| D-05 | Tier assigned by typology | rules | 🟡 | Income or willingness-to-pay would be better — PRD open question 2 |
| D-06 | Load factor | 0.30–0.40 by typology | 🟡 | Proposal range for rural residential. Validate on KPLC feeder profiles |
| D-07 | Non-residential uplift | 15% above 50 households | 🔴 | A placeholder for schools, dispensaries, shops and water pumping. Should be counted from POI data, not assumed |
| D-08 | Demand growth | 3%/yr | 🔴 | Affects the DCF, not the LCOE comparison |
| D-09 | Diversity factor | 1.0 | 🟡 | Disabled; a real coincidence factor <1 would reduce peak and plant size |

## E. Grid extension (Equation 5)

| ID | Assumption | Value | Status | Replacement source |
|---|---|---|---|---|
| E-01 | MV line cost | 18,000 USD/km | 🔴 | KPLC/REREC scheme cost records |
| E-02 | LV line cost | 9,000 USD/km | 🔴 | As above |
| E-03 | Transformer cost (50 kVA) | 12,000 USD | 🔴 | KPLC procurement |
| E-04 | Connection fee | 250 USD/hh | 🔴 | **The most decision-relevant single parameter.** KPLC published schedule / Last Mile Connectivity Project |
| E-05 | Terrain multipliers | 1.00 / 1.15 / 1.40 | 🔴 | Engineering judgement; not yet DEM-driven |
| E-06 | Network OPEX | 3% of CAPEX/yr | 🟡 | Standard utility practice |
| E-07 | Technical losses | 16% | 🟡 | KPLC system average; feeder-level would be better |
| E-08 | Bulk supply cost | 0.09 USD/kWh | 🔴 | EPRA bulk tariff |
| E-09 | Deployment time | 24 months | 🟡 | Affects only the priority ranking |

## F. Mini-grid (Equation 6)

| ID | Assumption | Value | Status | Replacement source |
|---|---|---|---|---|
| F-01 | PV cost | 1,100 USD/kW | 🔴 | IRENA; Kenyan installer quotations |
| F-02 | Battery cost | 320 USD/kWh | 🔴 | IRENA storage costs; declining fast — see the `low_battery_cost` scenario |
| F-03 | Inverter cost | 420 USD/kW | 🔴 | Supplier quotations |
| F-04 | Distribution cost | 9,000 USD/km | 🔴 | Built mini-grid cost records |
| F-05 | Connection cost | 180 USD/hh | 🔴 | Developer cost records |
| F-06 | Peak sun hours | 5.6 | 🟡 | Global Solar Atlas county mean; a per-settlement lookup is on the roadmap |
| F-07 | Performance ratio | 0.80 | 🟡 | Standard; dust and heat in ASAL conditions may justify lower |
| F-08 | Battery autonomy | 1.0 day | 🟡 | Drives the largest single cost term. Test 0.5–2.0 days |
| F-09 | Depth of discharge | 0.80 | 🟡 | Li-ion typical |
| F-10 | Round-trip efficiency | 0.90 | 🟡 | Li-ion typical |
| F-11 | Battery replacement | year 8, 85% of cost | 🟡 | Warranty-implied; cycle-life modelling would be better |
| F-12 | Inverter replacement | year 12, 90% of cost | 🟡 | As above |
| F-13 | O&M | 4% of CAPEX/yr | 🟡 | Includes operator, cleaning, collection |
| F-14 | Deployment time | 9 months | 🟡 | |

## G. Standalone PV (Equation 7)

| ID | Assumption | Value | Status | Replacement source |
|---|---|---|---|---|
| G-01 | Small-system PV cost | 1,500 USD/kW | 🔴 | Higher than mini-grid: no economies of scale. Kenyan SHS retail pricing |
| G-02 | Small-system battery cost | 400 USD/kWh | 🔴 | As above |
| G-03 | BOS | 25% of components + 60 USD | 🔴 | Includes install and distribution margin |
| G-04 | Battery replacement | every 5 years, full cost | 🟡 | The shortest asset life in the comparison; materially affects the crossover |
| G-05 | Servicing | 5% of CAPEX/yr | 🟡 | PAYG service model |
| G-06 | Deployment time | 3 months | 🟢 | Fastest option — the basis of its time-effectiveness advantage |

## H. Finance (Equations 8, 11–14)

| ID | Assumption | Value | Status | Replacement source |
|---|---|---|---|---|
| H-01 | Social discount rate | 10% | 🟡 | Standard for infrastructure appraisal in Kenya. Sweep it |
| H-02 | Analysis period | 20 years | 🟡 | See A-11 |
| H-03 | Utility WACC | 10% | 🔴 | KPLC published cost of capital |
| H-04 | Utility tariff | 0.155 USD/kWh | 🔴 | EPRA domestic/lifeline schedule — blended, and the blend matters |
| H-05 | Developer WACC | 14% | 🔴 | Market evidence |
| H-06 | Developer hurdle rate | 17.5% | 🟡 | Proposal cites 15–20% for SSA mini-grid developers |
| H-07 | Mini-grid tariff | 0.55 USD/kWh | 🔴 | EPRA-approved mini-grid tariffs; cost-reflective tariffs are contested and this drives developer viability outright |
| H-08 | Connection fee fully subsidised (utility) | 1.0 | 🟢 | Baseline choice; the `no_connection_subsidy` scenario tests the alternative |
| H-09 | Connection fee borne by household (developer) | 0.0 | 🟢 | Section 3.5.4: `CF₀ = H_c·Fee − CAPEX_dev` |
| H-10 | Collection efficiency | 0.92 / 0.88 | 🔴 | Utility and developer arrears data. Assuming 100% is a standard way to overstate viability |
| H-11 | Utilisation ramp | 60/80/95/100% | 🔴 | Observed connection-to-consumption ramps |
| H-12 | Tariff escalation | 2%/yr real | 🟡 | |
| H-13 | OPEX escalation | 3%/yr real | 🟡 | |
| H-14 | Salvage value | 10% of CAPEX | 🟡 | |
| H-15 | Results-based finance | 0 USD/connection | 🟢 | Off by default; Mission 300 and KOSAP grants can be modelled here |

## I. Prioritisation

| ID | Assumption | Value | Status | Note |
|---|---|---|---|---|
| I-01 | Weight on LCOE | 0.40 | 🟡 | A **policy judgement**, not a technical parameter |
| I-02 | Weight on viability | 0.35 | 🟡 | Should be elicited from county stakeholders — PRD open question 3 |
| I-03 | Weight on deployment speed | 0.25 | 🟡 | As above |
| I-04 | Criteria min-max normalised | — | 🟢 | Prevents any one unit dominating the composite |

---

## Replacement workflow

1. Obtain the sourced figure; record it in the `DATA_SOURCES.md` register.
2. Update the value in `config/`, **keeping the inline source comment current**.
3. If it is a standalone sizing input, re-run `scripts/derive_shs_kit_costs.py`
   and paste the regenerated block — do not hand-edit derived values.
4. Change the status here from 🔴 to 🟡/🟢 and name the source.
5. Re-run `lceo sensitivity` — a parameter that changes the technology mix
   deserves a paragraph in the results chapter, not just a table row.
