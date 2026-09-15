# 4. Keep grid extension in the micro-cluster comparison by default

**Status:** Accepted · **Date:** 2026-03

## Context

Section 3.5.4 describes the dispersed-settlement treatment: noise points default
to standalone PV, but before that default is finalised the model re-clusters
them at a relaxed 300–500 m radius, and where a micro-cluster exists it
"computes and compares LCOE_mg,c for a short, single-line micro-mini-grid
serving that micro-cluster against the aggregated SHS cost for the same
households, and assigns whichever technology is least-cost."

Read literally, that is a two-way comparison: mini-grid versus SHS, with grid
extension excluded.

During development the literal reading produced a clearly wrong answer on the
synthetic county. A group of ~147 dwellings, fragmented by DBSCAN at 75 m and
reassembled by the relaxed pass at 400 m, sat **70 metres** from an existing MV
line. Grid extension was by far the cheapest option — LCOE 0.28 against 0.54 for
mini-grid — and the literal rule denied it by category.

The rationale for excluding grid from that comparison is that extension to
genuinely dispersed points is prohibitive. But that rationale rests on distance
and density, which the LCOE already prices; it does not rest on the label the
clustering pass happened to attach.

## Decision

By default, keep grid extension in the micro-cluster comparison and let the
Equation 10 argmin decide, subject to the usual feasibility limit
(`max_extension_distance_km`).

Expose `clustering.micro_cluster_allows_grid` to reproduce the literal two-way
comparison, and test both branches.

This is what Section 3.5.4 itself asks for when it requires the
dispersed-settlement treatment to be "a tested outcome of the least-cost
framework, rather than an untested assumption". Excluding the cheapest option by
category is the untested assumption the section warns against.

## Consequences

**Good.** No settlement is denied its cheapest option by classification. The
rule stays a genuine argmin. The behaviour only ever changes the answer where
grid is actually cheapest.

**Bad.** A deliberate departure from a literal reading of the proposal text,
which must be declared in the dissertation's methodology chapter rather than
left in the code.

**Neutral.** A genuinely isolated homestead — no micro-cluster partner — still
takes the standalone default without comparison, exactly as Section 3.5.4
specifies. Its `decision_reason` records this as `dispersed_override`, so the
share of the plan resting on the override is reportable.
