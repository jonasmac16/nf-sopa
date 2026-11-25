---
name: data-analysis
description: Implement, modify, debug, or understand data-analysis and data-processing code in Python, R, Julia, Markdown/notebooks, or mixed-language repositories. Use for analysis logic, pipeline changes, code navigation, language-specific execution/testing, or repository intake. Load only the language/tool references relevant to the current project and task.
---

# Data analysis workflow

1. Inspect repository evidence and `.opencode/project-profile.md` when initialized before choosing a language/tool workflow.
2. Identify the relevant input -> transformation -> output path and the narrowest executable entry point.
3. Load only the reference files needed for the current task:
   - Python: `references/python.md`
   - Markdown/notebooks/Quarto/R Markdown: `references/markdown-notebooks.md`
   - LSP navigation/diagnostics: `references/lsp.md`
4. Follow the project's existing dependency, formatting, testing, and execution conventions.
5. Keep reusable analysis logic in testable functions/modules when consistent with repository structure.
6. Prefer focused/small-input execution before expensive full-data work.
7. Use `data-validation` for transformations whose correctness depends on schema, identifiers, filtering, joins, grouping, or output contracts.
8. Use `reproducibility` when external DataLad inputs, Apptainer environments, provenance, or exact rerunability matter.
9. Use `scientific-analysis` when biological identity, study design, statistical inference, mathematical models, numerical validity, or scientific interpretation affects correctness.

Do not load guidance for languages or tools absent from the current task. After `/init-analysis`, do not introduce a language classified as unused merely for implementation convenience.
