# Scientific project initialization

## Recommended order

```text
/init-analysis
/init
/review-init    # optional
```

## `/init-analysis`

Purpose: establish scientific identity and remove generic template choices that do not belong to this project.

It should infer from repository evidence first, then obtain user confirmation before pruning language/domain support. Its durable output is `.opencode/project-profile.md` plus specialized project-local skills/configuration.

Do not treat absence of code in a newly created/empty repository as evidence that a language is unused. Ask the user before pruning.

## `/init`

Purpose: discover repository-specific implementation facts and keep `AGENTS.md` concise and operational.

It should not restate the scientific profile. Instead it should capture commands, architecture, entry points, validation/testing, execution environment, data locations, outputs, expensive operations, and operational gotchas.

## `/review-init`

Purpose: independent consistency check after both initialization passes. It reports contradictions, accidental reintroduction of pruned languages, duplicated/drifting profile facts, missing commands, and scientifically consequential unresolved ambiguity.
