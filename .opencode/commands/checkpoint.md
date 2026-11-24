---
description: Write concise transient resume state to .opencode/session-state.md
model: opencode-go/deepseek-v4.1-flash
---


Inspect the current conversation and project state. Update `.opencode/session-state.md` with only durable information needed to resume this work in a fresh OpenCode session.

Include only what is relevant and known:

- current objective and status;
- important analysis/scientific decisions and assumptions;
- files intentionally modified;
- DataLad dataset locations and exact revisions in use;
- input files/subsets obtained or consumed;
- Apptainer image/reference and invocation details;
- important parameters and random seeds;
- outputs generated or known to be stale;
- exact verification/tests/validation already performed and outcomes;
- unresolved issues/blockers;
- next concrete actions.

Do not copy conversational prose or large command output. Do not duplicate facts that are already obvious from `AGENTS.md`, `.opencode/project-profile.md`, committed documentation, or source files unless they are essential to resume. Keep the file concise (normally under 150 lines).
