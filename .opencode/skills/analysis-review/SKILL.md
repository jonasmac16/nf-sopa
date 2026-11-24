---
name: analysis-review
description: Independently review data-analysis or data-processing changes for substantive correctness before merge, publication, release, or expensive reruns. Use to find data-integrity bugs, leakage, invalid transformations, statistical/scientific mismatches, reproducibility/provenance gaps, stale outputs, and missing verification.
---

# Analysis review

Review evidence, not intent. Prefer a few high-confidence substantive findings over stylistic commentary.

1. Establish the intended input -> transformation -> output behavior from code/tests/docs.
2. Inspect changed paths and their downstream implications.
3. Use `data-validation` concepts for keys, filters, joins, grouping, missingness, units, and output grain.
4. Consult `.opencode/project-profile.md` and use `scientific-analysis` when domain/design/model assumptions affect validity.
5. Check reproducibility boundaries: external DataLad revisions, container identity, parameters/seeds, and stale/cached outputs.
6. Check whether tests/validation actually exercise the risky behavior.
7. Use LSP for targeted navigation where available, but verify claims from source/project tooling.
8. Do not edit files during an independent review.

See `references/review-checklist.md` for a concise checklist.
