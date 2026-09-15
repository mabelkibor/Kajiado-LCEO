# Dissertation chapters

Markdown working drafts, tracking the structure of the approved proposal. The
submitted document is produced from these; this directory is where the writing
happens alongside the code, so that a result and the text describing it move
together.

| File | Chapter | Status |
|---|---|---|
| [`00-front-matter.md`](00-front-matter.md) | Title, declaration, abstract, lists | Drafted (proposal) |
| [`01-introduction.md`](01-introduction.md) | Background, problem, objectives, scope | Drafted (proposal) |
| [`02-literature-review.md`](02-literature-review.md) | Theory, empirical review, gaps | Drafted (proposal) |
| [`03-methodology.md`](03-methodology.md) | Design, data, equations, software | Drafted (proposal) + implementation notes |
| [`04-results.md`](04-results.md) | Findings | Outline — awaiting real data |
| [`05-discussion.md`](05-discussion.md) | Interpretation | Outline |
| [`06-conclusion.md`](06-conclusion.md) | Conclusions and recommendations | Outline |
| [`references.bib`](references.bib) | Bibliography | In progress |

## Working rules

1. **Chapters 1–3 restate the approved proposal.** Where the implementation is
   more explicit than the proposal text, say so in the chapter and cite the ADR
   — do not quietly rewrite the approved method.
2. **Every number in Chapter 4 traces to a run.** Quote the `run_summary.json`
   provenance block (git revision, scenario, timestamp) for each table and
   figure, so any figure can be regenerated.
3. **Do not paste synthetic results.** Until the real layers are ingested, the
   numbers in this repository describe a fabricated county.
4. **Figures are generated, not drawn.** `lceo figures` produces them; a figure
   that cannot be regenerated cannot be defended.
