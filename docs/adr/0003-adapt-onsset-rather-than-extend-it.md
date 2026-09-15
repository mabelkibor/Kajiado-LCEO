# 3. Adapt OnSSET parameters in Python rather than extend OnSSET

**Status:** Accepted · **Date:** 2026-03

## Context

OnSSET is the peer-reviewed reference implementation for geospatial least-cost
electrification, validated across many Sub-Saharan African countries. Using it
would buy credibility and comparability.

But OnSSET's native implementation, in its standard form, does not:

- ingest building-footprint vector data (it works on raster cells);
- apply structure filtering to separate dwellings from ancillary buildings;
- carry DBSCAN noise points forward as dispersed settlements, or run the
  Equation 10 override and micro-cluster test;
- perform a dual-perspective discounted cash flow (Equations 11–14).

Options: (1) fork OnSSET and add these; (2) use OnSSET as-is and accept the
resolution; (3) implement the equations directly and import OnSSET's cost
modules and parameter defaults.

## Decision

Option 3. Implement the governing equations directly in Python, and selectively
adopt OnSSET cost modules and default parameter tables where they improve
comparability with the reviewed literature.

## Consequences

**Good.** The four functions OnSSET does not natively support are implemented
where they belong, rather than bolted onto a raster pipeline. The economics stay
comparable because the cost parameters are shared. This is consistent with
OnSSET's own framing as an open, flexible tool rather than a black box.

**Bad.** The equations are re-implemented, so they can be re-implemented
*wrongly*. Mitigated by testing at the level of equation values — CRF against
the textbook annuity factor, the two LCOE forms against each other, IRR against
the rate that zeroes NPV — rather than merely testing that the code runs.

**Bad.** OnSSET improvements do not arrive for free; parameter tables must be
re-synced by hand when upstream defaults change.
