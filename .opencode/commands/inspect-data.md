---
description: Inspect dataset schema, dimensions, missingness, and scientific grain locally
agent: local-inspector
model: ollama/qwen3-coder-32k:14b
subtask: true
---


Inspect $ARGUMENTS as a data-analysis input, intermediate, or output.

Use the `data-validation` skill, the `scientific-analysis` skill when biological/statistical semantics matter, and, for external DataLad inputs, the `reproducibility` skill. Consult `.opencode/project-profile.md` when initialized. Establish only what can be checked safely and cheaply: shape/schema, identifiers, duplicates, missingness, ranges/levels, units/encodings when documented, and relevant join/grouping assumptions.

Do not retrieve an entire external dataset, mutate source data, write derived outputs, or run an expensive full analysis merely to inspect it. Return concise findings and any checks that remain necessary.
