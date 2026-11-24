---
description: Check consistency between project-profile.md, AGENTS.md, and pruned repository configuration
model: opencode-go/kimi-k2.7-code
subtask: true
---


Review repository initialization after `/init-analysis` and `/init`.

Compare `AGENTS.md`, `.opencode/project-profile.md`, active `opencode.json`, retained skills/references, and repository evidence.

Check for:

- contradictions between `AGENTS.md` and the scientific project profile;
- scientific/profile facts unnecessarily duplicated into `AGENTS.md` in a way likely to drift;
- language instructions or LSP configuration for languages pruned by `/init-analysis`;
- missing operational commands, entry points, tests, validation steps, DataLad inputs, Apptainer invocation, or expensive-operation warnings that `/init` should have captured;
- accidental loss of baseline safety, data-integrity, provenance, or reproducibility constraints;
- scientifically consequential assumptions that remain ambiguous.

Do not edit files. Return concise actionable findings. If no conflict is found, say that the initialization layers are coherent and identify any remaining unknowns the user should resolve.
