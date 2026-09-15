# Methodology — the governing equations

Equation numbers follow Section 3.5.3 of the dissertation proposal. Each section
below states the equation, defines its symbols, gives the implementation, and
records any place where the implementation is more explicit than the proposal
text. Those places are marked **Implementation note** and are not silent: each
is also a test, an ADR, or both.

## Notation (Table 3.4)

| Symbol | Meaning | Units |
|---|---|---|
| `d(i,j)` | Distance between building centroid *i* and node/neighbour *j* | km |
| `ε` (eps) | DBSCAN neighbourhood radius — 50–100 m primary; 300–500 m relaxed | m |
| `MinPts` | Minimum neighbours for a core point (3–5 households) | count |
| `H_c` | Households in cluster *c*, net of the Section 3.4.3 filter | count |
| `d_h` | Standardised daily household demand for the assigned tier | kWh/hh/day |
| `E_c` | Settlement *c* annual energy demand | kWh/yr |
| `LF` | Load factor | — |
| `D_c` | Distance from cluster *c* to the nearest existing MV line | km |
| `C_MV`, `C_LV` | Cost per km of MV and LV line extension | USD/km |
| `C_xfmr` | Transformer cost, where existing capacity is insufficient | USD |
| `C_conn` | Household connection fee (wiring, meter, service drop) | USD/hh |
| `r`, `n` | Discount rate and project lifetime | —, years |
| `CAPEX_i,c`, `OPEX_i,c` | Capital and annual operating expenditure of technology *i* in cluster *c* | USD, USD/yr |
| `NPC_i,c` | Net present cost of technology *i* in cluster *c* | USD |
| `CF_t` | Net cash flow in year *t* | USD |
| `WACC` | Weighted average cost of capital — the utility hurdle rate | — |

---

## Stage 1 — Structure filtering (Section 3.4.3, Table 3.3)

AI-derived footprint datasets detect built-up structures, not dwellings. In
Kajiado's rural wards a *manyatta* combines one or two dwellings with several
stores and livestock enclosures. Counting every footprint as a household would
inflate `H_c` and therefore, through Equation 3, the settlement's demand.

Four criteria, applied in order:

| Criterion | Rule | Purpose |
|---|---|---|
| Footprint area | Below a minimum habitable threshold (6–9 m²) → non-residential | Excludes stores, pens, shelters |
| Shape compactness | `C = 4πA / P²`; low `C` → open enclosure | Distinguishes roofed dwellings from bomas |
| Roof signature | Where sub-metre imagery allows, roofing material as a secondary check | Refines beyond geometry |
| Compound co-location | Within a compound, keep the largest 1–3 structures; smaller ones within 10–15 m are ancillary | Reflects manyatta layout |

**Implementation:** `preprocessing/footprint_filter.py`. Each criterion is a
separate boolean column, so attrition at each step is auditable
(`filter_summary()`); no row is dropped, so excluded structures stay available
for validation and mapping. The filter is explicitly **not a classifier** — its
residual error rate is measured against a stratified ground-truth sample
(`VALIDATION.md`) and reported as demand uncertainty.

---

## Equation 1 — Great-circle distance

```
d(i,j) = 2R · arcsin( √[ sin²((φⱼ − φᵢ)/2) + cos φᵢ · cos φⱼ · sin²((λⱼ − λᵢ)/2) ] )
```

with `R = 6,371 km` and φ, λ in radians.

**Implementation:** `geo/distance.py::haversine_km`. The haversine metric is
used rather than a planar approximation so distances stay valid across the whole
county without reprojection, and so cluster membership (Equation 2) and
distance-to-MV (Equation 5) are decided by the *same* metric.

**Implementation note.** The proposal defines distance point-to-point, but
Equation 5 needs distance to a *line* (the MV network). Line layers are densified
into a point cloud at 100 m spacing and queried with the same metric; the
approximation error is bounded by half the spacing (50 m), which is immaterial
against MV costs of ~USD 18,000/km. See `densify_lines`.

---

## Equation 2 — DBSCAN density condition

```
p is a core point  ⟺  |{ q ∈ D : d(p,q) ≤ ε }| ≥ MinPts
```

A settlement cluster is the maximal set of points density-connected under this
condition, with ε ∈ [50, 100] m and MinPts ∈ [3, 5] — the typical spacing of
dwellings within a compound or village core.

**Implementation:** `clustering/dbscan.py`. scikit-learn's DBSCAN with
`metric="haversine"` on radians, so Equation 1 is the distance function.

**Noise points are not discarded.** Per Section 3.5.3, they are the dispersed
pastoralist homesteads the study exists to make visible, and they are carried
forward to Equation 10. This is the substantive departure from models that treat
noise as data to be cleaned away.

---

## Equations 3–4 — Demand

```
E_c = Σ_{h ∈ c} 365 · d_h                        (3)
P_c,peak = (E_c / 365) / LF                      (4)
```

with `LF` typically 0.3–0.4 for rural residential profiles.

**Implementation:** `demand/tiers.py`.

**Implementation note on Equation 4.** Taken literally with `E_c` in kWh/year,
`(E_c/365)/LF` has units of kWh/day, not kW. Plant sizing needs power, so the
implementation divides additionally by 24 h:

```
P_c,peak [kW] = E_c / (365 · 24 · LF)
```

This is the standard load-factor identity — average power divided by load factor
— and reduces to the proposal's expression once the daily-energy-to-power
conversion is made explicit. Tested in `test_demand.py::test_equation_4_recovers_average_power_at_unit_load_factor`.

Demand tiers follow the ESMAP Multi-Tier Framework as adapted in OnSSET, and are
assigned by settlement typology. A non-residential uplift (schools, dispensaries,
shops, water pumping) is applied to settlements above a household threshold.

---

## Equations 5–7 — Capital cost by technology

```
CAPEX_grid,c = (C_MV · D_c) + (C_LV · L_LV,c) + C_xfmr + (H_c · C_conn)        (5)
CAPEX_mg,c   = (C_PV · P_sys,c) + (C_batt · Cap_batt,c) + (C_inv · P_inv,c)
               + (C_dist · L_mg,c) + (H_c · C_conn,mg)                          (6)
CAPEX_shs,c  = H_c · (C_panel + C_batt,shs + C_bos)                             (7)
```

**Implementation:** `costs/grid.py`, `costs/minigrid.py`, `costs/standalone.py`.

The connection-fee term of Equation 5 is carried **explicitly**, not folded into
a per-household average, because — as Section 3.5.4 records — high connection
fees are in practice a decisive barrier to take-up in Kenya even where the
network already passes nearby. Keeping it separate lets the same figure appear
as a utility cost, a developer revenue, or a subsidised write-off depending on
the perspective (Equations 11–14), and makes it a first-class object of the
sensitivity analysis.

**Implementation note — internal network length.** Equations 5 and 6 contain
`L_LV,c` and `L_mg,c` without parameterising them. Both are estimated from
settlement geometry by the standard reticulation heuristic

```
L = a · √(H_c · A_c) + b · H_c
```

where `A_c` is settlement footprint area. The first term scales with the linear
extent of the settlement (the backbone that must traverse it); the second is the
per-household service drop. `a` and `b` are configuration, not constants, and
must be calibrated against a sample of built KPLC/REREC schemes. See
`costs/sizing.py`.

**Implementation note — mini-grid sizing.** Equation 6 gives the cost terms but
leaves plant sizing implicit. `size_minigrid` derives it from Equations 3–4:

- PV on energy: `P_sys = E_c · oversize / (365 · PSH · PR)`
- Battery on autonomy: `Cap_batt = (E_c/365) · autonomy / (DoD · η_rt)`
- Inverter on peak: `P_inv = P_c,peak · headroom`

**Implementation note — SHS kit cost.** Equation 7 takes per-household kit cost
as a parameter, but that parameter must stay consistent with the energy the same
household is credited with in Equation 3's denominator — otherwise the SHS LCOE
is understated and Equation 10 is biased towards standalone systems. The kit
costs in `config/techno_economic.yaml` are therefore **derived** from tier
consumption by `scripts/derive_shs_kit_costs.py`, and the consistency is asserted
in `test_costs.py::test_standalone_kit_costs_match_their_sizing_basis`.

Mid-life replacements (SHS batteries ~5 yr; mini-grid batteries ~8 yr, inverters
~12 yr) fall inside the analysis period and are discounted at the year they
occur, via Equation 9a, rather than smeared into OPEX.

---

## Equations 8, 9, 9a — Annualisation and LCOE

```
CRF(r,n) = r(1+r)ⁿ / ((1+r)ⁿ − 1)                                    (8)

LCOE_i,c = (CAPEX_i,c · CRF(r,n) + OPEX_i,c) / E_c                   (9)

NPC_i,c  = Σₜ [ CAPEX·𝟙{t=0} + OPEX_t − Salvage_t ] / (1+r)ᵗ
LCOE_i,c = NPC_i,c / Σₜ [ E_c / (1+r)ᵗ ]                             (9a)
```

**Implementation:** `costs/annualisation.py`.

The two forms coincide when OPEX is constant and there are no replacements or
salvage — asserted exactly in
`test_costs.py::test_the_two_lcoe_forms_agree_without_replacements_or_salvage`.
They diverge once mid-life replacements enter, which is the case for mini-grids
and SHS, so **the pipeline uses Equation 9a**. Equation 9 is retained because it
is the proposal's headline form.

The LCOE is applied identically across all three technologies, which is what
makes the Equation 10 comparison like-for-like. Settlements with zero demand
return `NaN` rather than infinity, so they are excluded from the argmin rather
than silently ranked last.

`CRF(0.10, 20) = 0.117460`, checked against the textbook annuity factor.

---

## Equation 10 — Least-cost rule and the dispersed override

```
Technology*_c = argmin_{i ∈ {grid, mg, shs}} { LCOE_i,c }             (10)
```

For noise points under Equation 2 — spacing beyond the clustering radius,
consistent with dispersed pastoralist homesteads — the model applies an override
to standalone PV, because grid and mini-grid distribution cost per household
rises sharply and typically becomes prohibitive at that spacing.

**The override is tested, not assumed.** Before it is applied, noise points are
re-clustered at a relaxed ε of 300–500 m. Where two or more form a micro-cluster,
the model still computes and compares a short single-line micro-mini-grid
against aggregated SHS for the same households, and assigns whichever is
cheaper. Only a genuinely isolated homestead takes the default without a
comparison.

**Implementation:** `optimisation/least_cost.py`. Every settlement records a
`decision_reason` — `argmin`, `micro_cluster_comparison`, `dispersed_override`,
or `no_feasible_option` — so the share of the plan resting on the override
rather than on a comparison is reportable. `lcoe_margin` records the gap to the
runner-up, i.e. how robust each choice is to parameter error.

**Implementation note — grid eligibility for micro-clusters.** Section 3.5.4
frames the micro-cluster check as micro-mini-grid *versus* aggregated SHS. Read
literally, that excludes grid extension for any micro-cluster — including one
that happens to sit beside an existing MV line, which would then be denied the
cheapest option by assumption rather than by evidence. The default here keeps
grid in the comparison and lets the argmin decide, which is what Section 3.5.4
asks for when it requires the dispersed treatment to be "a tested outcome of the
least-cost framework, rather than an untested assumption". Set
`clustering.micro_cluster_allows_grid: false` to reproduce the literal two-way
comparison. See [`adr/0004-micro-cluster-grid-eligibility.md`](adr/0004-micro-cluster-grid-eligibility.md).

---

## Equations 11–14 — Financial viability

```
CF_t = R_t − O_t − C_t                                                (11)
NPV  = Σₜ [ CF_t / (1+r)ᵗ ] − CAPEX₀                                  (12)
0    = Σₜ [ CF_t / (1+IRR)ᵗ ] − CAPEX₀                                (13)
DPP  = min{ T : Σ_{t≤T} [ CF_t / (1+r)ᵗ ] ≥ CAPEX₀ }                  (14)
```

**Implementation:** `finance/dcf.py`.

**Implementation note — capital counted once.** Equations 12–14 as written
contain both a `C_t` term inside `CF_t` and a separate `− CAPEX₀`. Taken
literally that charges year-zero capital twice. The implementation builds `CF_t`
for `t ≥ 1` from revenue and operating cost only, and keeps capital in the
explicit `CAPEX₀` term. This matches the stated intent of Section 3.5.4, which
gives the developer case as `CF₀ = H_c · Fee_household − CAPEX_dev,c`.

**The connection fee switches sides by perspective.** Where a utility or REREC
subsidises the connection, the fee is a cost inside CAPEX (Equations 5–6). Where
the household or developer bears it, it is a one-off inflow at `t = 0`. The
`connection_fee_subsidy_share` parameter selects between these treatments.

Revenue is reduced by two factors that are explicit parameters rather than an
assumed 100%: a **utilisation ramp** (new connections take several years to
reach their modelled tier) and **collection efficiency** (billed is not
collected). Assuming full revenue from year one is the commonest way an
electrification appraisal overstates viability.

IRR returns `NaN` where no sign change brackets a root: a project that never
turns cash-positive has no IRR, and reporting one would be meaningless. Those
settlements route to the subsidy-gap branch instead.

**Viability tests.** Utility: `NPV ≥ 0` or `IRR ≥ WACC`; failing that, the
settlement is flagged as requiring REREC or public subsidy. Developer:
additionally `IRR ≥ hurdle`, of the order of 15–20% for Sub-Saharan African
mini-grid developers. For each non-viable settlement the model reports a
**subsidy gap** — the present-value grant that would bring NPV to zero, which is
the number a county budget submission or a results-based-finance application
actually needs.

---

## Stage sequence (Section 3.5.5)

| Stage | Input | Equations | Output |
|---|---|---|---|
| 1 | Raw footprints, network layers, meters | Table 3.3 | Cleaned dwellings with household counts and served status |
| 2 | Cleaned dwellings | 1, 2 | Settlement clusters + dispersed homesteads |
| 3 | Household counts per settlement | 3, 4 | Annual and peak demand |
| 4 | Demand, distance, cost data | 5–10 | Least-cost technology and its LCOE |
| 5 | Selected technology, tariffs, discount rates | 11–14 | NPV, IRR, payback, viability flag, per perspective |

**Final outputs:** (i) settlement clusters including dispersed homesteads;
(ii) demand tier and annual/peak demand; (iii) optimal technology and LCOE;
(iv) dual-perspective financial viability; (v) a prioritised county
electrification plan ranked on viability and deployment time-effectiveness.

---

## Software (Section 3.6)

The equations define the method; the tools implement it at county scale.

- **QGIS/ArcGIS** for spatial integration, visual checking and the maps that go
  to county decision-makers.
- **Python** (NumPy, pandas, scikit-learn, SciPy) to implement the equations
  directly as code and iterate over the full settlement set.

**On OnSSET.** OnSSET provides a validated, peer-reviewed code base for
geospatial least-cost electrification, and adopting its cost modules and default
parameter tables keeps these results comparable with the literature reviewed in
Chapter 2. But OnSSET's native implementation works at raster-cell resolution
and does not ingest building-footprint vectors, apply the Section 3.4.3
structure filter, run the Equation 10 dispersed override, or perform the
dual-perspective DCF of Equations 11–14. Python is therefore the development
layer in which OnSSET's parameters are adapted and the missing functions built —
consistent with OnSSET's own framing as an open, flexible tool rather than a
black box.
