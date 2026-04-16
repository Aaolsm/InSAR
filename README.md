# InSAR

Graduation project workspace for InSAR data processing, analysis, and documentation.

## Structure

- `data/raw`: raw input data
- `data/interim`: intermediate results
- `data/processed`: cleaned or final analysis-ready data
- `data/external`: external reference data
- `src`: source code
- `notebooks`: experiments and analysis notebooks
- `outputs/figures`: exported figures
- `outputs/tables`: exported tables
- `outputs/maps`: exported maps
- `docs/taskbook`: task planning and execution records
- `docs/notes`: progress notes and working logs
- `tests`: test code

## Working Notes

- Keep raw data read-only whenever possible.
- Put reusable logic in `src` instead of notebooks.
- Track plans in `docs/taskbook` and daily progress in `docs/notes`.

## Key Docs

- `docs/taskbook/master_taskbook.md`
- `docs/taskbook/stage_plan.md`
- `docs/notes/progress_log.md`
