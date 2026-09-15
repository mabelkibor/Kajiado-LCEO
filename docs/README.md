# Documentation index

## Start here

| If you want to… | Read |
|---|---|
| Understand what this is and run it | [`../README.md`](../README.md) |
| Know what problem it solves and for whom | [`PRD.md`](PRD.md) |
| Check the mathematics | [`METHODOLOGY.md`](METHODOLOGY.md) |
| Integrate with it or extend it | [`SPEC.md`](SPEC.md), [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Know what a number means | [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) |
| Know how far to trust a result | [`ASSUMPTIONS.md`](ASSUMPTIONS.md), [`VALIDATION.md`](VALIDATION.md) |
| Look up a term | [`GLOSSARY.md`](GLOSSARY.md) |

## All documents

### Product and method
- [`PRD.md`](PRD.md) — problem, users, requirements, scope, risks, milestones
- [`METHODOLOGY.md`](METHODOLOGY.md) — Equations 1–14, with every implementation
  note where the code is more explicit than the proposal text
- [`SPEC.md`](SPEC.md) — interfaces, data contracts, configuration, algorithms,
  numerical conventions, known limitations
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — module structure, dependency flow,
  extension points

### Data
- [`DATA_SOURCES.md`](DATA_SOURCES.md) — Table 3.2 sources, access routes,
  caveats, layer register
- [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) — every input and output column
- [`ETHICS_AND_DATA_GOVERNANCE.md`](ETHICS_AND_DATA_GOVERNANCE.md) — Section 3.9:
  approvals, privacy, integrity, dissemination

### Quality
- [`ASSUMPTIONS.md`](ASSUMPTIONS.md) — every numeric assumption, its status and
  its replacement source
- [`VALIDATION.md`](VALIDATION.md) — Section 3.8: the eight validation checks and
  their record

### Decisions
- [`adr/`](adr/) — architecture decision records, including every deliberate
  departure from a literal reading of the proposal

### Planning
- [`ROADMAP.md`](ROADMAP.md) — what is next and why
- [`GLOSSARY.md`](GLOSSARY.md) — abbreviations and terms

### Dissertation
- [`dissertation/`](dissertation/) — chapter drafts in Markdown, tracking the
  proposal structure

## Conventions

- **Equation numbers** always refer to Section 3.5.3 of the proposal, in code,
  docs and commit messages alike.
- **Section numbers** (e.g. 3.4.3) refer to the proposal.
- A **deliberate departure** from the proposal text is always an ADR, never a
  code comment alone.
- A **provisional parameter** is marked 🔴 in `ASSUMPTIONS.md` and carries a
  source comment in `config/`.
