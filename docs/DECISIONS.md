# Analysis decisions

Record durable, non-obvious project decisions that future analysts and agents need to reproduce or interpret the work. Prefer decisions with consequences; do not duplicate ordinary code comments or Git history.

Use entries like:

## YYYY-MM-DD: Decision title

**Decision:** What was decided.

**Rationale:** Why this choice was made.

**Consequences:** What code, data processing, interpretation, or validation depends on it.

**Evidence/links:** Optional references to issues, papers, dataset revisions, or commands.

## 2026-11-24: Generic SpatialData transformation framework

**Decision:** Add a reusable Nextflow process (`SPATIALDATA_TRANSFORM`) and a thin subworkflow (`SPATIALDATA_TRANSFORM_STAGE`) that apply a configured, ordered list of registered Python operations to the pipeline-generated SpatialData object at eight fixed pipeline boundaries. The process copies the input `.zarr` into its work directory before mutating it, so `EXPLORER_RAW` always reads the unmodified converted object and cannot race a transform.

**Rationale:**
- A common operation contract and registry lets future operations be added without new branches in `workflows/sopa.nf`.
- Copying the `.zarr` inside the transform task provides safe isolation between the raw explorer reader and mutating transforms without requiring an explicit ordering dependency or reworking the existing module cache model.
- Passing the `transform_module_dir` as a process input ensures Nextflow hashes the operation implementation files and invalidates cached transform tasks when code changes.
- Empty configuration (`spatialdata_steps: []`) must leave current pipeline behavior unchanged.

**Consequences:**
- `workflows/sopa.nf` now calls `SPATIALDATA_TRANSFORM_STAGE` at `after_conversion`, `before_image_segmentation`, `after_cellpose`, `after_stardist`, `after_transcript_segmentation`, `before_aggregation`, `after_aggregation`, and `before_output`.
- New operations are added by subclassing `Operation` in `modules/local/spatialdata_transform/operations.py`, registering the class, and adding the name to `getSpatialDataStepOperationNames()` in `modules/local/utils.nf`.
- Each executed stage writes a deterministic JSON manifest under `pipeline_info/spatialdata_steps/{sample}/{stage}.json`.
- `EXPLORER_RAW` continues to run immediately after `TO_SPATIALDATA` and reads the original converted object.

**Evidence/links:** Implementation in `modules/local/spatialdata_transform/` and `workflows/sopa.nf`.
