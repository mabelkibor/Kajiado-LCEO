# Working notes for AI assistants

Context for automated contributors. Human contributors: see
[`CONTRIBUTING.md`](CONTRIBUTING.md), which these notes supplement rather than
replace.

## What this repository is

The computational side of an MSc dissertation: a settlement-level
electrification planning model for Kajiado County, Kenya. Its correctness will be
examined at viva. Plausible-looking output that is subtly wrong is worse here
than output that fails loudly.

## Before changing modelling code

1. Read [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md). Every modelling module
   implements a numbered equation from the proposal.
2. Check [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md) — the parameter may
   already be registered, and may be provisional.
3. Check [`docs/adr/`](docs/adr/) — the choice may already have been made and
   argued.

## Non-negotiables

- **No numeric parameter in `src/`.** Everything lives in `config/`.
- **Tests assert values**, against textbook figures, closed forms, hand
  calculations or analytic limits. Not merely that the code runs.
- **Departures from the proposal text require an ADR.** Not a code comment.
- **Never commit anything under `data/`.**
- **Stages are pure**: DataFrame in, new DataFrame out, no mutation.

## Where the traps are

- **Units.** Equation 4 as written in the proposal yields kWh/day, not kW; the
  implementation divides by 24 h and documents it. Energy is kWh, power kW,
  distance km unless suffixed `_m`, money USD.
- **`NaN` versus `inf`.** `NaN` means "not a candidate" and is excluded from the
  Equation 10 argmin. `inf` would be ranked last, which is a different and wrong
  claim. Infeasible options must be `NaN`.
- **Capital counted once.** Equations 12–14 as written double-count year-zero
  capital. `CF_t` covers `t ≥ 1` only; capital stays in the explicit `CAPEX₀`
  term.
- **LCOE has two forms.** Equations 9 and 9a coincide only without replacements
  or salvage. The pipeline uses 9a. Their equivalence in the simple case is a
  test — do not "fix" it.
- **Noise points are data.** DBSCAN noise means a dispersed homestead, not an
  error. Never filter them out.
- **`compare_technologies` must stay idempotent.** The sensitivity sweep re-costs
  the same frame; that is why it drops the columns it regenerates.
- **SHS kit costs are derived, not quoted.** Change `sizing_basis`, then re-run
  `scripts/derive_shs_kit_costs.py`. A test asserts the two agree.

## Verifying a change

```bash
make test                          # 145 tests
lceo run                           # end-to-end on the synthetic county
lceo compare-scenarios             # every scenario still loads and runs
```

If a change moves the technology mix on the sample county, say so explicitly in
the PR with the before and after numbers. A silent change in results is the one
outcome this repository cannot tolerate.

## What not to do

- Do not present synthetic-county numbers as findings about Kajiado.
- Do not tune parameters so results match published figures; where this model
  differs from the literature, the difference is the contribution and needs
  explaining, not erasing.
- Do not remove a limitation from the documentation without fixing the
  underlying limitation.
