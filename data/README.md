# Data

**No data is committed to this repository.** `.gitignore` excludes these
directories wholesale. Provenance is recorded in
[`../docs/DATA_SOURCES.md`](../docs/DATA_SOURCES.md); the data itself is not.

## Directories

| Directory | Contents |
|---|---|
| `raw/` | Inputs as obtained: building footprints, MV/LV lines, transformers, meters |
| `external/` | Third-party reference layers: county boundary, DEM, land cover, solar resource |
| `interim/` | Per-stage intermediates, written when `run.write_intermediates: true` |
| `processed/` | Cleaned, analysis-ready derivatives |
| `validation/` | Ground-truth samples and labelled data for the checks in `VALIDATION.md` |

## Getting data

**To try the model:** `lceo sample-data` writes a synthetic county to `raw/`.
It is fabricated. It exercises the code and says nothing about Kajiado.

**For real analysis:** follow [`../docs/DATA_SOURCES.md`](../docs/DATA_SOURCES.md).
Building footprints, DEM, land cover and solar resource are open. **KPLC and
REREC network and meter data require a data-sharing agreement.**

Expected schemas: [`../docs/DATA_DICTIONARY.md`](../docs/DATA_DICTIONARY.md).

## Handling rules

1. Strip every customer identifier from meter data **before** it enters this
   directory.
2. Never commit. Check `git status` before committing; a leaked extract cannot
   be un-published.
3. Record the vintage of every layer in the register in `DATA_SOURCES.md` — a
   2023 network extract will not show 2025 schemes, and a result that does not
   say which it used cannot be interpreted.
4. Delete on completion, per the data-sharing agreement terms.

See [`../docs/ETHICS_AND_DATA_GOVERNANCE.md`](../docs/ETHICS_AND_DATA_GOVERNANCE.md).
