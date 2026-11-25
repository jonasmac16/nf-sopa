# Agent instructions for nf-core/sopa

This is the **nf-core/sopa** Nextflow pipeline for spatial-omics preprocessing at single-cell resolution. The canonical scientific/language profile is `.opencode/project-profile.md`; consult that before interpreting biological design, reference resources, or language choices.

## Architecture and key files

- **Entry point:** `main.nf` → `workflows/sopa.nf` → `subworkflows/local/` → `modules/local/`.
- **Owned code:** `modules/local/` and `subworkflows/local/`. Treat `modules/nf-core/` and `subworkflows/nf-core/` as vendored; avoid editing them in place.
- **Parameters:** declared in `nextflow.config`; documented in `nextflow_schema.json`.
- **Samplesheet schema:** `assets/schema_input.json`.
- **Predefined technology profiles:** `conf/predefined/*.config`.
- **Resource labels:** `conf/base.config`.
- **Module options / publishing:** `conf/modules.config`.

## Languages

- **Nextflow/Groovy** is the primary implementation language.
- **Python** is supporting only: it is used through the Sopa/SpatialData/Scanpy/Cellpose/ComSeg/Stardist command-line interfaces, small `python -c` version checks, and the narrowly-scoped SpatialData transformation helpers under `modules/local/spatialdata_transform/`.
- **R and Julia** are not project languages.

## Common commands

Run a minimal smoke test:
```bash
nextflow run . -profile test,docker --outdir results
```

Run with a real technology profile:
```bash
nextflow run . -profile docker,xenium_cellpose --input samplesheet.csv --outdir results
```

Run the test suite (matches CI):
```bash
nf-test test --tag test --profile +docker --verbose
```

Run one test configuration:
```bash
nf-test test tests/default.nf.test --profile +docker --verbose
```

Update test snapshots after intentional output changes:
```bash
nf-test test --tag test --profile +docker --verbose --update-snapshots
```

Lint the pipeline (use `--release` on `main`/`master`):
```bash
nf-core pipelines lint .
```

Rebuild the JSON schema after parameter changes:
```bash
nf-core pipelines schema build
```

Run pre-commit checks locally:
```bash
pre-commit run --all-files
```

## Testing and CI gotchas

- `nf-test.config` sources `tests/nextflow.config` and uses the `test` profile by default; it ignores vendored nf-core module tests.
- Test data is fetched from `nf-core/test-datasets/sopa/` and `nf-core/test-datasets/modules/`.
- CI tests run with Docker, Singularity, and Conda; Conda and Singularity are only required to pass on PRs targeting `main`/`master`. Nextflow `latest-everything` is allowed to fail.
- Snapshots capture stable paths and contents; unstable outputs are excluded via `tests/.nftignore`.
- The pre-commit hook `.hooks/block_pipeline_outdir.sh` blocks any commit that includes a `pipeline_info` output directory. Do not commit pipeline test outputs to the repository.

## Environment and containers

- Devcontainer: `nfcore/devcontainer:latest` (see `.devcontainer/devcontainer.json`).
- Host tooling needed: Nextflow `>=25.10.4`, nf-test, nf-core tools (version pinned in `.nf-core.yml`, currently `4.2.1`), plus Docker/Singularity/Apptainer or Conda.
- `SPACERANGER_COUNT` does **not** support Conda; Visium HD paths must use Docker/Singularity/Apptainer.
- Cellpose has dynamic environments/containers: `cellpose_version=4` and the `gpu` profile select alternate Conda envs/images in `conf/modules.config`. Do not hardcode a single Cellpose environment path.
- Apptainer is supported via the `apptainer` profile but is not the sole required execution model.

## Parameter and code conventions

- Add new parameters to both `nextflow.config` and `nextflow_schema.json`; use `nf-core pipelines schema build` to keep them in sync.
- Define default resource requirements for new local processes with labels in `conf/base.config`.
- Pass tool-specific arguments via `ext.args` in `conf/modules.config` rather than editing module scripts.
- Segmentation constraints (enforced at runtime):
  - At least one method must be enabled.
  - Only one transcript-based method (`use_baysor`, `use_comseg`, `use_proseg`).
  - Only one staining-based method (`use_cellpose`, `use_stardist`).
  - Imaging-only technologies (`macsima`, `phenocycler`, `hyperion`, `ome_tif`) cannot use transcript-based methods.

## Data, provenance, and safety

- Treat raw source data as immutable. Do not move, rename, delete, or commit external dataset content to this repository.
- This pipeline has no project DataLad inputs; user samplesheet paths point to local or mounted raw data.
- Default Visium HD Space Ranger reference is **human GRCh38-2020-A**. Override `spaceranger_reference` and `spaceranger_probeset` for mouse or other references.
- Preserve sample identity, spatial coordinate systems, micron-to-pixel transformations, image scales, and channel/transcript identifiers across patches and outputs.
- Record exact parameter files, pipeline version, and container/Conda environment identities when reproducibility matters.

## Documentation

- Update `docs/usage.md` and `docs/output.md` when parameters, inputs, outputs, or behavior change.
- Update `CITATIONS.md` when adding or removing tools.
- Keep durable scientific rationale in `docs/DECISIONS.md`, not in `AGENTS.md` or `.opencode/project-profile.md`.
