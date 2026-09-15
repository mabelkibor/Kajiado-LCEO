# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [0.1.0] — 2026-03

First release: the modelling framework, complete and tested against synthetic
data. **Not yet run against real Kajiado data**, and no parameter is yet
sourced from Kenyan primary data.

### Added

- **Stage 1 — pre-processing.** Table 3.3 structure filter (area, compactness,
  roof signature, compound co-location) with per-criterion attrition reporting;
  served-status tagging from meter records and MV/LV/transformer proximity.
- **Stage 2 — clustering.** Equations 1–2: haversine distance and DBSCAN
  settlement clustering; the relaxed micro-cluster pass; settlement typology.
  Noise points are retained as dispersed homesteads, not discarded.
- **Stage 3 — demand.** Equations 3–4: annual energy and coincident peak, with
  tier assignment by typology and a non-residential uplift.
- **Stage 4 — costs and selection.** Equations 5–10: CAPEX for all three
  technologies with explicit sizing; CRF; both LCOE forms; the least-cost rule
  with the dispersed override and the micro-cluster test; `decision_reason` and
  `lcoe_margin` on every settlement.
- **Stage 5 — finance.** Equations 11–14: NPV, IRR and discounted payback from
  utility and developer perspectives, with the connection fee moving between
  cost and revenue by perspective, and a subsidy gap for non-viable settlements.
- Prioritised county electrification plan with a transparent, configurable
  weighting.
- CLI: `sample-data`, `run`, `sensitivity`, `compare-scenarios`,
  `validate-config`, `figures`.
- Configuration system with includes, deep merge and scenario overlays; five
  shipped scenarios.
- Synthetic sample county, so the repository is runnable without restricted data.
- Four standard result figures and a quick-look settlement map.
- 145 tests, asserting equation values rather than only code execution.
- Documentation: PRD, technical spec, methodology reference, architecture, data
  sources, data dictionary, assumptions register, validation plan, ethics and
  data governance, glossary, roadmap, six ADRs, and dissertation chapter drafts.

### Known limitations

See [`docs/SPEC.md`](docs/SPEC.md) § 7 and
[`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md). The load-bearing ones: every
techno-economic parameter is provisional; MV distance is straight-line rather
than routed; served status is inferred from proximity rather than a connection
register; the structure filter is a heuristic whose residual error is not yet
measured.
