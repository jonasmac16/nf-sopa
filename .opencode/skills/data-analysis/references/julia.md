# Julia analysis reference

Use only when Julia is relevant.

## Detect the project conventions

Inspect `Project.toml`, `Manifest.toml`, `src/`, `test/runtests.jl`, scripts, notebooks, Make/just/task files, and container documentation.

## Rules

- Activate the project environment explicitly and respect `Project.toml`/`Manifest.toml` when present.
- Do not use an unrelated global Julia environment for project work.
- Keep reusable analysis logic in functions/modules when appropriate.
- Be attentive to type stability, mutation/aliasing, missing values, categorical representations, and dataframe join/grouping semantics when they affect correctness.
- Use the project's existing tests/formatters/static-analysis commands.
- Do not add packages or mutate the environment unless dependency modification is part of the task.
