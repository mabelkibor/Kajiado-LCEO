# Notebooks

Exploratory analysis. **Nothing here is part of the model** — findings that
matter move into `src/`, with tests.

| Notebook | Purpose |
|---|---|
| `01-data-exploration.ipynb` | Inspect input layers: coverage, completeness, obvious errors |
| `02-clustering-sensitivity.ipynb` | Sweep ε and MinPts; visualise how the settlement set moves (validation check V3) |
| `03-cost-crossover.ipynb` | Explore the grid/off-grid crossover by settlement size — the study's central result |
| `04-results-exploration.ipynb` | Interrogate a completed run before drafting Chapter 4 |

## Rules

1. **Outputs are stripped on commit** (`nbstripout` via pre-commit). Notebooks
   record method, not results; results belong in `outputs/`, regenerable.
2. **Import from the package**, never copy code into a cell. A calculation that
   exists only in a notebook is untested and unreproducible.
3. **Promote or delete.** A notebook that has served its purpose either becomes
   a tested module or goes away. Stale notebooks drift out of step with the
   model and mislead.

```python
from kajiado_lceo import load_config
from kajiado_lceo.pipeline import run

config = load_config("../config", scenario="baseline")
result = run(config, write_outputs=False)
result.settlements.head()
```
