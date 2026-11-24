---
description: Audit analysis code and outputs across computational, numerical, statistical, and scientific validity
agent: analysis-reviewer
model: openai/o4-mini
subtask: true
---


Review the current analysis/processing changes. If arguments are supplied, focus on: $ARGUMENTS

Use the `analysis-review`, `data-validation`, and `scientific-analysis` skills when relevant. Consult `.opencode/project-profile.md` for project-specific scientific constraints. Report actionable correctness/reproducibility findings first. Do not edit files.
