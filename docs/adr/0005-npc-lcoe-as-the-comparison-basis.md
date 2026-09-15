# 5. Use the discounted (Equation 9a) LCOE form as the comparison basis

**Status:** Accepted · **Date:** 2026-03

## Context

The proposal gives two forms of the LCOE and states them as equivalent:

- Equation 9, annualised: `(CAPEX·CRF + OPEX) / E_c`
- Equation 9a, discounted: `NPC / Σ_t [E_c/(1+r)^t]`

They coincide when OPEX is constant and there are no replacements or salvage.
They do not coincide otherwise — and the three technologies being compared have
very different replacement profiles: SHS batteries at ~5 years, mini-grid
batteries at ~8 and inverters at ~12, grid assets at essentially none within the
analysis period.

Under Equation 9, a mid-life battery replacement can only be represented by
inflating OPEX, which smears a year-8 outlay evenly across years 1–20 and
understates its discounted cost. That bias runs consistently against grid
extension, which is the comparison the whole study turns on.

## Decision

Compute both. Use Equation 9a in the pipeline. Retain Equation 9 as
`costs.annualisation.lcoe` because it is the proposal's headline form and the
form the sensitivity discussion refers to.

Assert their equivalence in the no-replacement, no-salvage case as a test, so
the equivalence claim in the proposal is verified rather than asserted.

## Consequences

**Good.** Replacement outlays are discounted in the year they occur. The
technology comparison is not biased by asset-life differences. The proposal's
equivalence claim becomes a passing test.

**Bad.** Reported LCOE values differ slightly from a naive Equation 9
calculation, which must be explained when comparing against published figures
computed the simpler way.
