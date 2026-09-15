# Roadmap

Current release: **0.1.0** — framework complete, tested, runnable on synthetic
data. Not yet run against real Kajiado data.

---

## 0.2 — Real data (milestones M2–M3)

The blocking release. Nothing downstream is meaningful until this lands.

- [ ] Acquire Google Open Buildings footprints for Kajiado; record vintage and
      confidence threshold
- [ ] Execute the KPLC and REREC data-sharing agreements; ingest MV/LV,
      transformers, meters
- [ ] Replace every 🔴 parameter in [`ASSUMPTIONS.md`](ASSUMPTIONS.md) with a
      sourced Kenyan figure
- [ ] Conduct the local market survey for PV, battery and inverter pricing
- [ ] Calibrate the structure-filter thresholds (C-01, C-03) on labelled Kajiado
      footprints rather than on judgement
- [ ] Calibrate the network-length coefficients (A-06) against as-built scheme
      drawings
- [ ] Benchmark performance at county scale — the nearest-network query is the
      bottleneck (PRD N-04)

## 0.3 — Validation (milestone M4)

- [ ] V1: structure-filter ground truth on a stratified sample; report the
      confusion matrix and propagate the error band into demand
- [ ] V2: served-status bracket, running the proximity and meter-evidence rules
      as bounds
- [ ] V3: clustering stability sweep over ε × MinPts, reporting the technology
      mix rather than just the cluster count
- [ ] V7: external comparison against OnSSET Kenya, KNES and the Narok study
- [ ] Publish the completed validation record in
      [`VALIDATION.md`](VALIDATION.md)

## 0.4 — Spatial fidelity

Where the current model is weakest, in order of how much the weakness matters:

- [ ] **Least-cost path MV routing** (PRD F-20) replacing straight-line
      distance. Straight-line `D_c` understates real extension cost and
      therefore biases towards grid — the most consequential simplification in
      the model. Terrain, land cover, roads and protected areas as a cost
      surface.
- [ ] **DEM-driven terrain classification** (PRD F-19) so the multiplier is
      computed rather than assumed
- [ ] **Per-settlement solar resource** from Global Solar Atlas rather than one
      county mean
- [ ] **Convex-hull settlement area** in place of the bounding box (A-05)
- [ ] **Transformer siting**, not just counting, within larger settlements

## 0.5 — Analysis depth

- [ ] Monte Carlo uncertainty propagation — replace one-at-a-time sensitivity
      with joint parameter uncertainty, and report technology choice as a
      probability rather than a verdict
- [ ] Phased investment: stage CAPEX over several years rather than concentrating
      it at `t = 0`
- [ ] Demand growth trajectories per typology, not a single county rate
- [ ] Grid arrival option value — a settlement that will be reached by a planned
      scheme in five years is a different investment case from one that never
      will be
- [ ] Reliability dimension: a grid connection at 60% availability is not the
      same service as a mini-grid at 95%, and the model currently treats them as
      equal

## 0.6 — Dissemination (milestone M6, PRD F-21)

- [ ] Spatial decision-support dashboard for the County Government, REREC and
      KPLC — the Section 3.10 commitment
- [ ] QGIS project file with styled layers, bundled rather than described
- [ ] Summary report template generated directly from `run_summary.json`, so a
      re-run regenerates the report
- [ ] Developer-facing pipeline export: settlements clearing the commercial
      hurdle, with the IRR evidence attached

## Beyond

- Additional technologies — wind, hybrid diesel, small hydro. The architecture
  takes a fourth technology with no change to the decision rule
  ([`ARCHITECTURE.md`](ARCHITECTURE.md) § Extension points).
- Generalisation to other Kenyan ASAL counties. The delimitation states results
  are not directly generalisable without further study; the *method* is, and a
  second county would test that claim.
- Contribution of the footprint-based clustering and dispersed-settlement
  treatment back to the OnSSET community.
