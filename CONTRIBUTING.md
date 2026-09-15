# Contributing

This repository underpins a dissertation that will be examined. That shapes how
changes are made: **every result must be reproducible and every judgement call
must be defensible**.

## Setup

```bash
python -m pip install -e ".[dev]"
pre-commit install
lceo sample-data && lceo run     # confirm the pipeline works before changing it
```

## The rules that matter

### 1. Every equation cites its number

A function implementing a governing equation names it in its docstring, in the
form used by the proposal ("Equation 5 — grid extension CAPEX"). A reader
holding the proposal must be able to find the code for any equation without
searching.

### 2. No numeric parameter in `src/`

Every cost, threshold, rate and coefficient lives in `config/`. If you need a
new one, add it to the appropriate config file **with a source comment**, add a
row to `docs/ASSUMPTIONS.md` with its status, and read it via
`config.require(...)`. A parameter that is required and missing must raise, not
silently default — that is what makes a run fully described by
(config, scenario, data).

### 3. Test the value, not just the call

A test that asserts a function returns a number is nearly worthless here. Assert
against something independent: a textbook value, a closed-form solution, a hand
calculation, an analytic limit, or an invariant. See
`test_crf_matches_the_textbook_value` and
`test_the_two_lcoe_forms_agree_without_replacements_or_salvage` for the standard.

### 4. Departures from the proposal get an ADR

Where the implementation is more explicit than, or differs from, a literal
reading of the proposal, write an ADR in `docs/adr/`. Code comments are not
enough: a judgement call invisible outside the source is indistinguishable, at
viva, from an oversight. See
[ADR 0004](docs/adr/0004-micro-cluster-grid-eligibility.md) for the pattern.

### 5. Never commit data

`.gitignore` excludes `data/` wholesale. KPLC and REREC layers are supplied under
a data-sharing agreement and may not be redistributed. Check `git status` before
every commit — a leaked extract cannot be un-published.

### 6. Stages are pure

Every stage takes a DataFrame and a `Config` and returns a **new** DataFrame.
Nothing mutates its input. This is what lets stages be tested alone and re-run
under varied parameters.

## Workflow

1. Branch from `main`.
2. Make the change, with tests.
3. `make test && make lint`.
4. Update documentation in the same commit as the code — `METHODOLOGY.md` for an
   equation, `ASSUMPTIONS.md` for a parameter, `SPEC.md` for an interface, an
   ADR for a judgement call.
5. Open a PR using the template, stating the effect on model output.

## Commit messages

Say what changed and why, and cite the equation or section where relevant:

```
Fix Equation 4 peak demand units

(E_c/365)/LF yields kWh/day, not kW. Divide additionally by 24 h so
plant sizing receives power. Adds the load-factor identity test.
```

## Code style

`ruff` (line length 100) and `mypy`. Equation symbols keep their published
casing — `E_c`, `H_c`, `P_c` — so `N803`/`N806` are disabled deliberately. Do
not rename the mathematics to satisfy a linter.

Comments explain **why**, not what. The code says what it does; the comment says
why it does it that way, especially where a reader might reasonably expect
something else.

## Reporting a methodology concern

Open an issue with the `methodology` template. Concerns about whether the method
is *right* are more valuable than bug reports, and are welcome from anyone.
