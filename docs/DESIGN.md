# Design

This repository is intentionally project-local. It does not require or modify `~/.config/opencode/`.

## 1. Two-stage initialization

Initialization has two owners:

- `/init-analysis` owns `.opencode/project-profile.md` plus language/domain specialization.
- built-in `/init` owns/refines `AGENTS.md` with repository-operational facts.

Run `/init-analysis` first so scientific identity, units/design, and language choices exist before `/init` compresses repository instructions.

The files intentionally do not duplicate each other. `project-profile.md` answers "what scientific/computational project is this?" while `AGENTS.md` answers "how should work be performed safely in this repository?"

## 2. Scientific project profile

`.opencode/project-profile.md` is concise canonical state for:

- scientific domain and analysis type;
- primary/supporting languages;
- unit of observation/inference and identifier hierarchy;
- study/experimental/model structure;
- versioned scientific reference resources;
- critical biological/statistical/mathematical/numerical assumptions;
- project-level DataLad/Apptainer provenance model.

Durable rationale belongs in `docs/DECISIONS.md` instead.

V1 loads the profile through the project `instructions` config. Current V2 does not resolve configured instruction files, so its project-local plugin injects the profile into primary/compaction context.

## 3. Conditional workflows

Five core skills are discoverable within this repository:

- `data-analysis`
- `data-validation`
- `reproducibility`
- `analysis-review`
- `scientific-analysis`

Their bodies load on demand. Language/tool and scientific-domain details are separate lazy references.

## 4. Specialization rather than permanent generic support

The template begins with Python, R, and Julia support because it must serve different projects. `/init-analysis` asks for confirmation before removing unused language support. It can also remove irrelevant scientific-domain references.

This reduces ambiguity and prevents an agent from treating every template-supported language as an equally legitimate implementation choice.

## 5. Durable vs transient state

- `.opencode/project-profile.md`: concise current scientific/language identity.
- `docs/DECISIONS.md`: version-controlled, non-obvious scientific/analysis rationale and decisions.
- `.opencode/session-state.md`: transient resume state written by `/checkpoint` and ignored by Git.
- Git: code/project history.
- DataLad: dataset identity/content provenance.
- Apptainer/container repository: execution-environment identity.

This avoids introducing a generic memory database as a second source of truth.

## 6. Context reduction

- automatic OpenCode compaction;
- analysis-aware compaction hook;
- concise project profile;
- lazy skill/reference loading;
- physical pruning of irrelevant language/domain references;
- isolated review/data-inspection/init-review commands;
- LSP-assisted targeted navigation where supported;
- no MCP servers enabled by default.

## 7. Configuration scope

`opencode.json`, `.opencode/agents`, `.opencode/commands`, `.opencode/plugins`, `.opencode/skills`, and `.opencode/project-profile.md` are stored in the analysis repository. The template never edits global OpenCode files.

## 8. Helper namespace

OpenCode-specific helper executables and inactive profile sources live under `.opencode/`. Top-level `bin/` remains available for downstream analysis commands. Migration utilities live only on the companion `migration-tools` branch.
