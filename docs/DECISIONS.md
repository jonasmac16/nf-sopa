# Analysis decisions

Record durable, non-obvious project decisions that future analysts and agents need to reproduce or interpret the work. Prefer decisions with consequences; do not duplicate ordinary code comments or Git history.

Use entries like:

## YYYY-MM-DD: Decision title

**Decision:** What was decided.

**Rationale:** Why this choice was made.

**Consequences:** What code, data processing, interpretation, or validation depends on it.

**Evidence/links:** Optional references to issues, papers, dataset revisions, or commands.

## 2026-11-26: Complete nf-core/sopa argument forwarding

**Decision:** Expose the nine applicable arguments from the pinned nf-core/sopa 1.0.2 interface (`cellpose_version`, `cellpose_kwargs`, `clahe_kernel_size`, `image_scale`, `patch_overlap_microns`, `unassigned_value`, `aggregate_genes`, `expand_radius_ratio`, `infer_presets`) and forward them directly through the existing local adapters.

**Rationale:**

- Direct forwarding keeps the local wrapper aligned with upstream Sopa CLI semantics without duplicating defaults or interpretation logic.
- `cellpose_version` controls container/environment selection only; it is not passed as a CLI flag.
- `aggregate_genes` defaults to `true` so existing profiles that only set `aggregate_channels` continue to produce a transcript-count table.
- CosMx aggregation requires `--gene-column target`; the adapter injects this automatically for `technology == 'cosmx'`.
- Proseg requires a single transcript patch, so `patch_width_microns` remains forced to `-1` for `use_proseg`.

**Consequences:**

- `modules/local/utils.nf` maps these parameters to their Sopa CLI flag names.
- `modules/local/parameter_validation.nf` enforces cross-parameter constraints (e.g., at least one aggregation mode enabled, valid Cellpose version, Boolean/numeric/string checks).
- `conf/modules.config` selects the pinned Cellpose 3 or Cellpose 4 CPU/GPU container for `DOWNLOAD_CELLPOSE_MODEL`, `PATCH_SEGMENTATION_CELLPOSE`, and `RESOLVE_CELLPOSE`.
- Tests in `tests/sopa_args.nf.test`, `tests/parameter_validation.nf.test`, and `tests/cellpose_container_*.nf.test` cover the mappings, validation, and container selection.

**Evidence/links:** Implementation in `modules/local/utils.nf`, `modules/local/parameter_validation.nf`, `conf/modules.config`, and `nextflow.config`.

## 2026-11-26: Dedicated segmentation image via `merge_channels`

**Decision:** Extend `merge_channels` so it can create a separate multiscale segmentation image with configured channel groups, leaving the source image unchanged.

**Rationale:**

- Some technologies (e.g., CosMx) provide a stitched source image with many channels, but Cellpose only needs a nuclear and a membrane channel. Creating a dedicated segmentation image avoids modifying or duplicating the full source image while giving Cellpose exactly the channels it expects.
- Single-source channel groups should be copied exactly; multi-source groups use the selected merge method (`max` or `prod`).
- Regenerating the pyramid from the merged full-resolution image guarantees that all scales are consistent with each other and with the source coordinate transformations, rather than merging each scale independently.
- Registering the new image under `sdata.attrs['cell_segmentation_image']` makes it transparently available to Sopa's patchification and segmentation CLI without adding new pipeline parameters for image selection.

**Consequences:**

- `merge_channels` now supports two modes: legacy append-to-source (`channels`/`output_channel`) and segmentation-image mode (`output_image_key`/`channel_groups`).
- In segmentation-image mode, `sdata.attrs['cell_segmentation_image']` is updated to `output_image_key`.
- The new `aggregate_image_key` pipeline parameter forwards `--image-key` to `sopa aggregate`, allowing aggregation over the original image while segmentation uses the new image.
- Tests in `modules/local/spatialdata_transform/tests/test_operations.py` verify source-image preservation, exact single-channel copying, multi-channel merging, pyramid regeneration, and the cell-segmentation attribute.

**Evidence/links:** Implementation in `modules/local/spatialdata_transform/operations.py`; Sopa image resolution via `sopa.utils.get_spatial_image` and `SopaAttrs.CELL_SEGMENTATION`.

## 2026-11-25: Specific SpatialData transformation operations

**Decision:** Implement three concrete operations through the generic Part 1 framework:

- `background_correction`: explicit-method, single-channel correction (methods: `subtract_constant`, `divide`, `gaussian`, `rolling_ball`, `tophat`); no implicit algorithm or threshold.
- `merge_channels`: append a combined channel using pixel-wise `max` or `prod`, matching the uint64-then-uint16 scaling rule from WEHI SODA Hub's `combine_channels.py`.
- `filter_cells`: declarative numeric filtering of a shapes element with a mandatory, exact unfiltered backup under a separate key.

**Rationale:**

- Background correction is scientifically consequential; the operation requires an explicit `method` and method-specific parameters and preserves all unselected channels, coordinates, transformations, and multiscale relationships.
- Channel merging reproduces the reference behavior so that existing segmentation recipes (e.g. `DAPI combined_membrane`) continue to work, while retaining all original channels and avoiding OME-TIFF-specific I/O.
- Cell-shape filtering must not silently destroy the original segmentation; the backup guarantees that the unfiltered boundaries remain available for inspection or downstream reruns.

**Consequences:**

- `modules/local/spatialdata_transform/operations.py` registers `background_correction`, `merge_channels`, and `filter_cells`.
- `modules/local/utils.nf::getSpatialDataStepOperationMetadata()` exposes the new operations to early Nextflow parameter validation.
- `merge_channels` carries a MIT license attribution to WEHI SODA Hub in `CITATIONS.md`.
- `filter_cells` at `after_cellpose` writes the filtered shapes back to `cellpose_boundaries` and the unfiltered backup to `cellpose_boundaries_unfiltered`; downstream transcript segmentation consumes the filtered prior.

**Evidence/links:** Implementation in `modules/local/spatialdata_transform/operations.py`; reference code at `https://github.com/WEHI-SODA-Hub/sp_segment/blob/02bc645a7c53fb3b73deb272963d7a7adf316c6c/bin/combine_channels.py`.

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
