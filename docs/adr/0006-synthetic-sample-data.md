# 6. Ship synthetic sample data

**Status:** Accepted · **Date:** 2026-03

## Context

The model's real inputs include KPLC and REREC MV/LV network, transformer and
meter data, obtained under a data-sharing agreement and not redistributable.
Building footprints and raster layers are large and separately licensed.

Without a substitute, nobody — examiner, collaborator, or the author on a new
machine — can run this repository. Tests would need fixtures anyway, and
fixtures invented ad hoc per test drift away from the structure of the real
problem.

## Decision

Ship `kajiado_lceo.sample`, which fabricates a county with the *structural*
properties the model must handle: a dense peri-urban corridor on the existing
network; mid-sized villages at varying distance from it; dispersed pastoralist
homesteads in the southern rangelands; and ancillary structures inside
compounds. Seeded, so it is reproducible.

Label it as synthetic in the generator docstring, in the CLI output, in the
README and in this ADR.

## Consequences

**Good.** `pip install -e . && lceo sample-data && lceo run` works for anyone,
immediately. CI can run the full pipeline end to end. Tests share one realistic
fixture rather than many ad hoc ones. The code paths that matter — noise points,
micro-clusters, ancillary filtering, the grid/off-grid crossover — are all
exercised.

**Bad.** A real risk of synthetic output being mistaken for a finding about
Kajiado. Mitigated by labelling at every point of contact, but the risk is not
zero and the labelling must stay.

**Bad.** Synthetic data can flatter the model: it contains exactly the structure
the model expects, with no digitisation errors, no missing network segments and
no misaligned footprints. Passing on synthetic data says the code is correct,
not that the method is valid.
