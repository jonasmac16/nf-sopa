---
description: Initialize project scientific identity, language specialization, and domain references
agent: plan
model: opencode-go/kimi-k3.1-pro
subtask: false
---


Initialize the scientific/data-analysis profile for this repository before the built-in `/init` step.

If arguments were supplied, treat them only as hints: $ARGUMENTS

Work from repository evidence first. Ignore template implementation under `.opencode/` when inferring which programming languages the analysis itself uses. Do not infer project languages merely because this template contains Python/R/Julia reference files.

## 1. Inspect and infer

Determine, where evidence supports it:

- scientific domain(s), for example bioinformatics, computational biology, mathematical biology, biostatistics, systems biology, or related quantitative biology;
- analysis type and intended scientific output;
- languages actually used by project code, classified as **primary**, **supporting**, or **unused** among Python, R, and Julia;
- Markdown/notebook/Quarto/R Markdown use separately from programming-language choice;
- unit of observation and, when distinct, unit of inference;
- subject/sample/biological-replicate/technical-replicate/visit/run or analogous hierarchy;
- study/experimental design, including paired, repeated, longitudinal, clustered, batch, or train/validation/test structure where relevant;
- versioned scientific references such as genome build, annotation release, ontology, database, coordinate convention, pathway/network source, or model parameter source;
- external DataLad inputs and expected Apptainer execution model;
- important statistical, biological, mathematical, or numerical assumptions that downstream agents must not silently change.

Use code, configuration, README/docs, schemas, metadata, and pipeline definitions as evidence. Do not guess scientific semantics from names alone.

## 2. Resolve consequential ambiguity with the user

Before deleting or disabling language/domain support, show the inferred profile briefly and ask the user to confirm or correct:

- primary language(s);
- supporting language(s);
- unused language(s) to prune;
- scientific domain reference(s) to retain;
- any unresolved scientific fact whose wrong interpretation could invalidate the analysis.

Do not ask questions whose answers are already unambiguous from repository evidence. Do not prune a language or domain merely because it has not yet appeared in a newly empty repository; obtain explicit user confirmation first.

## 3. Write the canonical scientific profile

Replace `.opencode/project-profile.md` with a concise project-specific profile. Prefer short sections such as:

- Domain and analysis type
- Languages
- Scientific design
- Reference resources
- Reproducibility/environment
- Critical invariants

Record unknown items as `Unknown` or omit them rather than inventing values. Keep the file normally under 100 lines. Put rationale/history in `docs/DECISIONS.md`, not here.

## 4. Specialize language support after confirmation

For each confirmed unused language among Python, R, and Julia:

- remove its `.opencode/skills/data-analysis/references/<language>.md` file;
- remove the corresponding language bullet from `.opencode/skills/data-analysis/SKILL.md`;
- remove project-local LSP configuration that exists only for that language from `opencode.json`;
- ensure `.opencode/bin/check-environment.sh` will no longer warn about that language. The baseline checker is designed to infer enabled language support from the remaining language reference files, so do not hard-code a new language list there.

Do not remove shell or Markdown/documentation support. Do not add a new programming language just because an agent prefers it.

If a language is retained as **supporting**, state its allowed role in `.opencode/project-profile.md` so later agents do not casually move analysis logic into it.

## 5. Specialize scientific-domain references after confirmation

Always retain `general-scientific-computing.md`.

Retain only applicable domain references under `.opencode/skills/scientific-analysis/references/` from:

- `bioinformatics.md`
- `computational-biology.md`
- `mathematical-biology.md`
- `biostatistics.md`

Remove confirmed irrelevant domain references and remove their bullets from `.opencode/skills/scientific-analysis/SKILL.md`. If the domain is unresolved or genuinely cross-disciplinary, retain the plausible references rather than pruning aggressively.

## 6. Verify specialization

Before finishing:

- validate edited JSON files;
- verify every reference named by a retained `SKILL.md` exists;
- verify no retained project-local configuration points to a pruned language reference;
- report exactly which language/domain support was retained and removed.

Do not run the built-in `/init` yourself. Finish by telling the user that `/init-analysis` is complete and that the next step is `/init`, followed optionally by `/review-init`.
