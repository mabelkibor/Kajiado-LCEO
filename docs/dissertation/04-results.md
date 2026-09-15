# Chapter 4: Results

> **Outline only.** No results are recorded here yet: the model has not been run
> against real Kajiado data (milestone M2 in [`../PRD.md`](../PRD.md)). Every
> table and figure below names the artefact that will produce it, so the chapter
> can be populated by running the model rather than by transcription.
>
> **Do not paste synthetic output into this chapter.** The sample county is
> fabricated; its numbers describe nothing.

## 4.1 Introduction

Reporting order follows the four specific objectives, and therefore the five
stages: settlement identification, demand, cost comparison, and the recommended
pathway with its viability.

## 4.2 Settlement identification and clustering *(Objective I)*

**Source:** `outputs/tables/settlement_clusters.csv`,
`outputs/tables/structure_filter_report.csv`

To report:

- Structures detected; structures removed by each Table 3.3 criterion; dwellings
  retained. Attrition at each step, with the ground-truth error band from V1.
- Dwellings served and unserved, as the **bracket** from V2 (proximity rule and
  meter-evidence rule), not a single figure.
- Settlements formed; noise points; micro-clusters recovered; genuinely isolated
  homesteads.
- **Table 4.1** — settlement clusters by typology: count, households, mean size,
  mean distance to MV, mean built density.
- **Figure 4.1a** — county map of settlements by typology.
- Clustering stability across ε × MinPts (V3): does the settlement count move,
  and — the question that matters — does the technology mix move with it?

## 4.3 Settlement demand *(Objective II)*

**Source:** `least_cost_technology.csv`; `run_summary.json`

To report: tier distribution across settlements; total county demand from
unelectrified settlements (GWh/yr) and aggregate peak (MW); demand by typology;
the non-residential share; and the demand uncertainty implied by the V1
household-count error.

## 4.4 Technology cost comparison *(Objective III)*

**Source:** `least_cost_technology.csv`

To report:

- **Table 4.2** — CAPEX, OPEX and LCOE by technology and typology: median and
  interquartile range, not means alone; the distribution is what matters.
- **Figure 4.1** — LCOE against distance to MV, by technology
  (`fig_lcoe_vs_distance.png`). **The central result.**
- **The crossover distances.** For each settlement size band, the distance at
  which grid extension ceases to be least-cost. This is the single most
  decision-relevant number the study produces and should be stated explicitly,
  with its uncertainty, not left for the reader to infer from a scatter.
- **Figure 4.3** — CAPEX composition (`fig_capex_breakdown.png`), showing what
  share of total capital is the connection fee.
- Cost per household and cost per connection by technology and typology.

## 4.5 Optimal pathway and viability *(Objective IV)*

**Source:** `least_cost_technology.csv`, `financial_viability.csv`,
`prioritised_electrification_plan.csv`

To report:

- The technology mix: settlements, households and capital by recommended
  technology.
- **Figure 4.2** — technology by typology (`fig_technology_mix.png`).
- **Decision reasons.** What share of settlements was decided by argmin, by
  micro-cluster comparison, and by the dispersed override? A plan resting heavily
  on the override rests on assumption, and the reader is entitled to know how
  heavily.
- **Table 4.3** — viability by perspective: settlements viable to the utility;
  viable to a developer; viable to neither; median IRR and payback for each.
- **Figure 4.4** — IRR against LCOE by perspective (`fig_viability.png`).
- **The subsidy gap**, in money, for the settlements no perspective will fund.
  This is the number a county budget submission needs.
- **Table 4.4** — the prioritised plan: top-ranked settlements, and the
  cumulative households reached against cumulative capital committed.
- **Figure 4.5** — households reached against capital committed, the marginal
  cost of access curve.

## 4.6 Sensitivity and scenarios

**Source:** `sensitivity_sweep.csv`, `scenario_comparison.csv`

To report: which parameters move the technology mix and which do not — the
former belong in the discussion, the latter in an appendix; the four scenarios
against baseline; and, specifically, the effect of the connection fee, which
Section 3.5.4 singles out as the decisive practical barrier.

## 4.7 Summary of findings

Each finding stated against the research question it answers, with its
uncertainty attached.

---

## Reporting rules for this chapter

1. **Every table and figure cites its run.** Quote the `run_summary.json`
   provenance — git revision, scenario, timestamp — so any number can be
   regenerated.
2. **Report distributions, not just central tendency.** A mean LCOE across a
   heterogeneous county conceals the very heterogeneity the study exists to
   expose.
3. **Report uncertainty with the number**, not in a separate section at the end.
4. **Report the inconvenient results**: settlements where nothing is viable,
   parameters where the mix is unstable, strata where the filter performs badly.
   The subsidy gap exists as an output so that "not viable" is a finding with a
   number rather than an omission.
