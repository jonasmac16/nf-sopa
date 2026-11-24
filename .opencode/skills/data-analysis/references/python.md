# Python analysis reference

Use only when Python is relevant.

## Detect the project conventions

Inspect `pyproject.toml`, lockfiles (`uv.lock`, Poetry/PDM files), requirements files, environment files, `src/`, tests, notebooks, Make/just/task files, and container documentation.

## Rules

- Use the project interpreter/environment rather than system Python.
- Prefer existing package/dependency tooling; do not introduce a second manager without need.
- Reuse project lint/type/test commands (for example Ruff, mypy/pyright, pytest) when configured.
- Keep important transformations and statistical logic out of duplicated notebook-only code when a reusable module fits the repository.
- Avoid implicit chained assignment, index-alignment assumptions, and dtype coercions in dataframe code; validate keys and shape around joins/reshapes.
- Do not install packages unless dependency modification is part of the task.
