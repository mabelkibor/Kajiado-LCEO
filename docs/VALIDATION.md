# Validation plan

Implements Section 3.8 (Research Quality). Three claims must be defended:
**validity** — the model identifies the right settlements; **reliability** — the
parameters are standardised and traceable; **objectivity** — the optimisation is
data-driven.

---

## V1. Structure filter (Section 3.4.3)

**Claim.** The Table 3.3 heuristics separate dwellings from stores and
enclosures well enough that household counts, and therefore demand, are usable.

**Why it matters.** `H_c` enters Equation 3 linearly, so a 20% household error
is a 20% demand error, which propagates to every CAPEX term, every LCOE and
every viability verdict. This is the single largest methodological risk in the
study.

**Method.**
1. Draw a stratified random sample of 5–10% of clusters across the four
   typologies (`footprint_filter.ground_truth`).
2. Label each footprint in the sample by visual inspection of high-resolution
   imagery: dwelling / store / enclosure / other.
3. Compare against the filter's `is_dwelling`.
4. Report a confusion matrix, precision and recall per stratum.

**Report.** Residual misclassification rate by stratum, and the implied
household-count error band, carried into the demand figures as an uncertainty
range rather than a footnote. Section 1.7.1 commits to exactly this.

**Acceptance.** No absolute threshold is set in advance — an unmet threshold
would tempt post-hoc tuning. The requirement is that the error is *measured* and
*propagated*. If dwelling recall falls below ~0.8 in any stratum, the filter
parameters should be recalibrated on the sample and the validation repeated on a
fresh sample.

---

## V2. Served status

**Claim.** The buildings classed unelectrified are genuinely unelectrified.

**Why it matters.** Over-counting inflates the investment need and the plan;
under-counting makes the county's dark settlements invisible again, which is the
failure this study exists to correct.

**Method.**
1. Where meter data is available, run the model twice — once with
   `electrification_status.require_meter_evidence: false` (proximity rule) and
   once with `true` (meter evidence only).
2. The two unelectrified populations bracket the truth. Report both.
3. Where both meters and LV lines exist, compute agreement between them: the
   share of metered buildings inside the LV buffer measures how good a proxy the
   buffer is.
4. Sample-check disagreements against imagery.

**Report.** The bracket, its width as a share of the population, and the
buffer's agreement rate. Use the bracket in the results chapter, not a single
point estimate.

---

## V3. Clustering stability

**Claim.** The settlement set is a property of the county, not an artefact of ε.

**Why it matters.** ADR 0002 accepts ε-sensitivity as the price of resolving
dispersed homesteads. Accepting it obliges quantifying it.

**Method.** Sweep ε ∈ {50, 75, 100} m × MinPts ∈ {3, 4, 5}. For each
combination record: cluster count, noise-point share, household distribution,
and — the figure that actually matters — the **technology mix**.

**Report.** A stability table. The finding to defend is not "the clusters are
identical" (they will not be) but "the technology recommendation is robust
across the proposal's stated parameter range", or, if it is not, exactly where
and why it flips.

---

## V4. Equation-level correctness

**Claim.** The equations are implemented correctly.

**Method.** Automated, in `tests/`, run in CI:

| Property | Reference | Test |
|---|---|---|
| `CRF(0.10,20) = 0.117460` | Textbook annuity factor | `test_crf_matches_the_textbook_value` |
| `CRF(0,n) = 1/n` | Analytic limit | `test_crf_at_zero_discount_is_one_over_n` |
| 1° latitude `= R·π/180` | Spherical geometry | `test_one_degree_of_latitude_is_about_111_km` |
| Longitude scales by `cos φ` | Spherical geometry | `test_longitude_degrees_shrink_with_latitude` |
| Nairobi–Kajiado ≈ 62 km | Independent check | `test_known_separation_nairobi_to_kajiado_town` |
| Circle compactness `= 1`, square `= π/4` | Analytic | `test_compactness_of_a_circle_is_one` |
| Equations 9 and 9a coincide when they should | The proposal's own equivalence claim | `test_the_two_lcoe_forms_agree_without_replacements_or_salvage` |
| NPV of a flat annuity matches the closed form | Financial mathematics | `test_npv_of_a_flat_annuity_matches_the_annuity_formula` |
| IRR zeroes the NPV | Definition, Equation 13 | `test_irr_makes_npv_zero` |
| IRR of (−1000, +1200) = 20% | Hand calculation | `test_irr_of_a_known_doubling_case` |
| SHS kit cost matches its sizing basis | Internal consistency | `test_standalone_kit_costs_match_their_sizing_basis` |

---

## V5. Conservation and invariants

Properties that must hold on every run, asserted in `tests/test_pipeline.py`:

- Households are conserved from filtered buildings to settlements.
- Every settlement receives a technology and a `decision_reason`.
- `settlement_id` is unique.
- Noise points are never dropped — settlement rows account for every
  unelectrified dwelling.
- Where `decision_reason == "argmin"`, the selected LCOE **is** the minimum of
  the feasible options.
- Dispersed overrides always yield `standalone`.

---

## V6. Comparative statics

**Claim.** The model responds to parameter changes in the direction theory
predicts. A model that does not is broken regardless of how well it fits.

| Change | Expected response | Test |
|---|---|---|
| MV cost ↑ | Fewer settlements on grid | `test_higher_grid_cost_moves_settlements_off_grid` |
| Distance to MV ↑ | Grid CAPEX ↑ | `test_grid_capex_rises_with_distance_to_the_network` |
| Connection fee → 0 | Grid CAPEX ↓ | `test_removing_the_connection_fee_lowers_grid_capex` |
| Tariff ↑ | NPV ↑ | `test_higher_tariff_improves_viability` |
| Discount rate ↑ | CRF ↑, NPV ↓ | `test_crf_increases_with_the_discount_rate` |
| Load factor ↓ | Peak demand ↑ | `test_lower_load_factor_implies_a_higher_peak` |
| Connection fee shifted to households | Utility subsidy gap ↓ | `test_removing_the_connection_subsidy_worsens_utility_viability` |
| Battery cost ↓ | Mini-grid and SHS more competitive | `low_battery_cost` scenario |

---

## V7. External comparison

**Claim.** Results sit within the range published for comparable settings.

**Method.** Compare the county-level LCOE ranges and technology mix against:
OnSSET Kenya applications (Mentis et al. 2017; Korkovelos et al. 2019); the
Kenya National Electrification Strategy; the Narok County footprint-based study
(Ronoh & WRI 2025) — the closest published analogue; and published Kenyan
mini-grid tariff filings.

**Report.** Where this model differs, explain *why* — resolution, the dispersed
treatment, the dual-perspective appraisal — rather than tuning parameters until
the numbers agree. The differences are the contribution.

---

## V8. Objectivity

**Claim.** The optimisation is free from political or institutional bias
(Section 3.8).

**How it is secured structurally, not by assertion:**

- Equation 10 is a pure argmin over computed LCOE. No technology carries a
  preference weight, a bonus or a penalty.
- Every parameter is in `config/`, so any claim of bias can be tested by
  changing a value and re-running.
- `decision_reason` records where the argmin was *not* the mechanism — the
  dispersed override — so the share of the plan resting on assumption rather
  than computation is visible.
- The one place a value judgement genuinely enters is the prioritisation
  weighting (`I-01`–`I-03` in `ASSUMPTIONS.md`). It is labelled as a policy
  judgement, kept configurable, and reported separately from the least-cost
  result, which stands on its own.

---

## Validation record

| Check | Status | Date | Result | Evidence |
|---|---|---|---|---|
| V1 Structure filter ground truth | Not started | | | |
| V2 Served-status bracket | Not started | | | |
| V3 Clustering stability sweep | Not started | | | |
| V4 Equation-level tests | **Passing** | continuous | 145 tests | CI |
| V5 Conservation invariants | **Passing** | continuous | — | CI |
| V6 Comparative statics | **Passing** | continuous | — | CI |
| V7 External comparison | Not started | | | |
| V8 Objectivity review | Structural | | | This document |
