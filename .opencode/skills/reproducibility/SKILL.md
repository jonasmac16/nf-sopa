---
name: reproducibility
description: Establish or preserve reproducible analysis execution, external-data provenance, and environment identity. Use when work involves DataLad datasets, Apptainer containers, exact reruns, random seeds/parameters, external repositories, provenance reporting, or handoff/resumption state.
---

# Reproducibility workflow

1. Identify exact inputs, code revision/state, parameters, and execution environment relevant to the result.
2. Keep external datasets read-only by default and record exact revisions.
3. Use the documented Apptainer/container execution path when present.
4. Make hidden state explicit: parameters, seeds, environment variables, binds, and manual prerequisites.
5. Distinguish project Git history from DataLad data provenance and from container-definition history.
6. Record what was actually executed and verified; never imply a full rerun when only a smoke/focused run occurred.

Load only relevant references:

- DataLad: `references/datalad.md`
- Apptainer: `references/apptainer.md`
- Git/provenance boundaries: `references/git-provenance.md`
- durable handoff state: `references/session-state.md`
