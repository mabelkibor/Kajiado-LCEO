# 2. DBSCAN on building footprints, not raster population

**Status:** Accepted · **Date:** 2026-03

## Context

Established spatial electrification models — OnSSET as applied by Mentis et al.
and Falchetta et al. — work on population rasters at roughly 1 km resolution.
That resolution suits national trade-offs. It does not suit a county
procurement decision, and in Kajiado specifically it erases the object of study:
a *manyatta* of three dwellings disappears into a cell whose population is
attributed to the nearest town.

Alternatives considered:

1. **Population raster + threshold**, as OnSSET does. Comparable to the
   literature, but cannot see dispersed homesteads at all.
2. **Administrative units** (sub-locations). Available and clean, but a
   sub-location in Kajiado spans both a peri-urban corridor and open rangeland,
   which is exactly the heterogeneity this study exists to resolve.
3. **DBSCAN on building footprints.** Resolves individual structures, and its
   noise label has a direct physical meaning here.

## Decision

Cluster AI-derived building footprints with DBSCAN under the haversine metric,
at ε of 50–100 m and MinPts of 3–5.

Critically: **treat noise points as data, not as error.** A DBSCAN noise point
is a dwelling whose spacing exceeds the clustering radius — which in Kajiado is
the definition of a dispersed pastoralist homestead. Those homesteads are a
large share of the unelectrified population and the reason the county's
last-mile clusters are invisible to budget cycles.

## Consequences

**Good.** Settlement units are real settlements. Dispersed homesteads are
first-class results with their own technology recommendation. Household counts
come from structures rather than from population downscaling.

**Bad.** Results are sensitive to ε: the same county yields materially different
settlement counts at 50 m and at 100 m. Mitigated by making ε a swept
sensitivity parameter, never a buried constant.

**Bad.** Footprint datasets do not distinguish dwellings from stores, which
forces the Section 3.4.3 filter and its residual error into the method.

**Bad.** Direct comparison with published OnSSET results is weakened, since the
spatial unit differs. Mitigated by adopting OnSSET cost modules and parameter
defaults so the *economics* stay comparable (ADR 0003).
