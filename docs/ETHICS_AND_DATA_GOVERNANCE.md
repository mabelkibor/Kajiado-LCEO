# Ethics and data governance

Implements Section 3.9 of the proposal.

## Approvals

| Requirement | Status |
|---|---|
| Strathmore University Institutional Ethics Review Committee | To be confirmed before data collection |
| NACOSTI research permit | Required for primary data collection in Kenya |
| KPLC data-sharing agreement | Required for network and meter data |
| REREC data-sharing agreement | Required for scheme and planned-extension data |

## Privacy

**No personally identifiable information enters this repository, at any stage.**

Meter data is the sensitive layer: a meter record can identify a household, its
consumption and its payment behaviour. Controls:

1. **Request the minimum.** Meter *locations* only. Not names, account numbers,
   consumption histories or payment records.
2. **Strip identifiers at source**, before the data reaches `data/`. If a
   supplied extract carries account numbers, remove them and document that the
   removal happened.
3. **Aggregate before publication.** Reported figures are settlement-level.
   Individual building coordinates are never published, in any figure, table or
   map, at a resolution that identifies a household.
4. **Never commit data.** `.gitignore` excludes `data/` wholesale. Check
   `git status` before every commit; a leaked extract cannot be un-published.
5. **Delete on completion**, per the terms of the data-sharing agreement.

Building footprints are derived from open satellite imagery and carry no
attached identity. They still locate dwellings, so the aggregation rule (3)
applies to them too.

## Integrity

- Findings are reported as computed. A result that contradicts an existing
  policy position is reported and discussed, not adjusted.
- Every parameter is declared in `config/` and registered in
  [`ASSUMPTIONS.md`](ASSUMPTIONS.md). Provisional values are flagged as
  provisional in the repository *and* in any output derived from them.
- Deviations from the proposal's method are recorded as ADRs, not left implicit
  in code.
- Negative and inconvenient results — settlements where no option is viable,
  parameters where the technology mix is unstable — are reported. The subsidy
  gap exists as an output precisely so that "not commercially viable" is a
  finding with a number attached rather than an omission.

## Social impact

The study rests on universal, equitable energy access as a foundation of
Kajiado County's development. Two consequences follow for how it is conducted:

**Dispersed homesteads are not rounded away.** Treating DBSCAN noise as error
would erase, from the analysis, precisely the pastoralist households least
likely to be served. Keeping them is an ethical choice as much as a
methodological one.

**The connection fee is modelled explicitly.** A framework that assumed
connection at no household cost would conclude that grid-adjacent settlements
are already solved. They are not: the fee is a decisive barrier, and it is
carried as its own term so its incidence can be examined rather than assumed
away.

## Limitations disclosed to users

Any dissemination of results — to the County Government, REREC, KPLC or
developers — carries these statements:

1. Results are a **screening and prioritisation** tool, not an engineering
   design. A recommended scheme still requires detailed design and survey.
2. Cost parameters carry the uncertainty documented in `ASSUMPTIONS.md`. Where
   they remain provisional, that is stated on the output.
3. Household counts carry the structure-filter error measured in
   [`VALIDATION.md`](VALIDATION.md).
4. The model optimises **cost**. It does not model equity weighting, political
   commitments, or existing scheme pipelines — all of which legitimately enter a
   real investment decision and none of which this model claims to supersede.

## Dissemination (Section 3.10)

| Audience | Form | Governance |
|---|---|---|
| Academic | Dissertation; potential peer-reviewed article | Settlement-level aggregation only |
| Policy — Kajiado County, REREC, KPLC | Summary report; spatial decision-support dashboard | No building-level coordinates; provisional parameters flagged |
| Industry — RE developers | Viability findings, pre-screened pipeline | Aggregated; no household data |

Code is released under MIT so the method can be audited and reused. Input data
is **not** released; it remains under its providers' terms.
