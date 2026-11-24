# R analysis reference

Use only when R is relevant.

## Detect the project conventions

Inspect `DESCRIPTION`, `NAMESPACE`, `renv.lock`, `.Rprofile`, `.Rproj`, `R/`, `tests/testthat/`, `_targets.R`, Quarto/R Markdown files, Make/just/task files, `.lintr`, and container documentation.

## Rules

- Prefer reproducible non-interactive execution through existing scripts/targets/project commands.
- Respect `renv` or other project dependency conventions when present.
- Avoid relying on `.GlobalEnv`, manually created objects, or execution order from a previous interactive session.
- Do not use `setwd()` as a substitute for project path conventions unless the repository deliberately uses it.
- Keep reusable transformation/statistical logic in functions/packages when consistent with project structure.
- For dplyr/data.table joins and grouping, explicitly verify key uniqueness/cardinality and grouping state where mistakes can change results.
- Use existing `testthat`, `lintr`, `styler`, targets, or other configured checks rather than inventing parallel tooling.
- Do not install packages unless dependency modification is part of the task.
