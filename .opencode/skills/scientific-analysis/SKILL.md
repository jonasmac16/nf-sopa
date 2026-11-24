---
name: scientific-analysis
description: Apply scientific-validity checks to quantitative biological research, including bioinformatics, computational biology, mathematical biology, biostatistics, systems biology, genomics, omics, and related scientific computing. Use when analysis correctness depends on experimental units, biological identifiers, reference resources, statistical inference, mathematical models, numerical solvers, or scientific interpretation rather than software execution alone.
---

# Scientific analysis workflow

Treat scientific validity as distinct from software correctness.

1. Read `.opencode/project-profile.md` when it exists and is initialized; treat it as the canonical project-specific scientific profile.
2. Establish the scientific question, unit of observation/inference, study or model structure, and scientifically meaningful identifiers before interpreting transformations or results.
3. Always load `references/general-scientific-computing.md` for substantive scientific-analysis work.
4. Load only retained domain references that apply:
   - bioinformatics/genomics/omics: `references/bioinformatics.md`
   - computational/systems biology: `references/computational-biology.md`
   - mechanistic/mathematical modeling: `references/mathematical-biology.md`
   - statistical inference/experimental design: `references/biostatistics.md`
5. Distinguish computational correctness, numerical correctness, statistical validity, and scientific validity. Passing tests or completing a run establishes only part of that chain.
6. Do not infer biological or mathematical semantics from variable names when metadata, documentation, equations, schemas, or study design can establish them.
7. Record durable non-obvious scientific decisions and rationale in `docs/DECISIONS.md`; keep the project profile concise.
