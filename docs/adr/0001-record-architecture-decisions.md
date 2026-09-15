# 1. Record architecture decisions

**Status:** Accepted · **Date:** 2026-03

## Context

This model underpins a dissertation that will be examined. Several
implementation choices are judgement calls that a reader of the proposal could
reasonably have made differently — and a judgement call that is invisible in the
code is indistinguishable, at viva, from an oversight.

## Decision

Record every architecturally or methodologically significant decision as a short
Architecture Decision Record in `docs/adr/`, numbered sequentially, stating
context, decision, and consequences including the ones we dislike.

An ADR is warranted when a choice (a) departs from a literal reading of the
proposal, (b) constrains future extension, or (c) would otherwise have to be
re-derived by anyone reading the code.

## Consequences

- Examiners and collaborators can see *why*, not only *what*.
- Deviations from the proposal text become explicit and defensible rather than
  silent.
- A small ongoing cost: a decision worth making is a decision worth writing down.
