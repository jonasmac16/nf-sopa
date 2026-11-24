# Markdown, notebooks, Quarto, and R Markdown

Use when analysis documentation or interactive documents are part of the task.

- Preserve notebooks/documents when they are an established project interface.
- Avoid correctness that depends on undocumented cell/chunk execution order or hidden interactive state.
- Prefer reusable functions/modules for substantial logic that is shared or needs testing.
- Keep executable examples synchronized with actual project commands.
- Do not clear/regenerate outputs or execute an entire expensive document unless requested or needed for verification.
- For Quarto/R Markdown, inspect project configuration and execution engine before assuming Python vs R behavior.
