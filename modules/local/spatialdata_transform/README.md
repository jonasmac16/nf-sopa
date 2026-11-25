# Generic SpatialData transformation framework

This directory implements the generic, ordered, declarative SpatialData transformation framework for nf-core/sopa. It lets registered operations modify the pipeline-generated SpatialData object at fixed pipeline boundaries without adding operation-specific branches to `workflows/sopa.nf`.

## Operation contract

Every operation must define:

- `name`: a unique operation identifier.
- `supported_stages`: list of stage identifiers the operation may run at (empty means all stages).
- `affected_element_types`: subset of `images`, `shapes`, `points`, `tables` that the operation may touch.
- `validate(context, sdata)`: validate arguments and required SpatialData elements before execution.
- `apply(sdata, context) -> (sdata, report)`: perform the modification and return a JSON-serializable report dict.

The shared context passed to each operation contains:

- `sample`: sample identifier.
- `technology`: pipeline technology parameter.
- `stage`: current pipeline stage identifier.
- `args`: validated operation-specific arguments.

Operations must:

- perform only their declared modification;
- preserve sample identity, spatial axes, coordinate transformations, scales, units, and identifiers unless an intentional change is declared;
- return serializable metrics;
- raise clear errors for invalid input or output.

Operations must **not** read arbitrary pipeline-global parameters, invoke Nextflow, or publish outputs themselves.

## Built-in operations

- `noop`: identity operation. Useful for testing the framework wiring.
- `assert_element`: validates that a given SpatialData element exists. Useful for stage-wiring tests.
  - args: `element_type` (one of `images`, `shapes`, `points`, `tables`), `element_key` (string).
- `add_test_shapes`: test-only operation that adds a minimal shapes element with one dummy polygon. Useful for verifying that a mutation is persisted and consumed downstream.
  - args: `shapes_key` (string).
- `background_correction`: single-channel background correction on an image.
  - args: `image_key` (string), `channel` (string), `method` (string).
  - Supported methods and their required parameters:
    - `subtract_constant`: `value` (number).
    - `divide`: `value` (number, non-zero).
    - `gaussian`: `sigma` (number > 0).
    - `rolling_ball`: `radius` (integer >= 0).
    - `tophat`: `radius` (integer >= 0), optional `selem` (`disk` or `square`, default `disk`).
- `merge_channels`: append a combined channel to an image using pixel-wise `max` or `prod`.
  - args: `image_key` (string), `channels` (ordered list of strings), `output_channel` (string, default `combined_membrane`), `method` (`max` or `prod`, default `max`).
- `filter_cells`: filter shapes using declarative numeric predicates and keep an unfiltered backup.
  - args: `source` (string, default `cellpose_boundaries`), `backup_key` (string, default `cellpose_boundaries_unfiltered`), `filters` (list of predicate maps).
  - Each predicate map contains: `column` (string), optional `min` (number), optional `max` (number), optional `keep_nulls` (boolean).
  - `column` may be any numeric GeoDataFrame column or a geometry-derived property (`area`, `perimeter`, `bounds_minx`, `bounds_miny`, `bounds_maxx`, `bounds_maxy`).

## Stages

The exact stage identifiers and their pipeline positions are:

| Stage                           | Position                                                                                         |
| ------------------------------- | ------------------------------------------------------------------------------------------------ |
| `after_conversion`              | After `TO_SPATIALDATA` and `EXPLORER_RAW`, before downstream modification/segmentation           |
| `before_image_segmentation`     | After optional tissue segmentation and before `MAKE_IMAGE_PATCHES`                               |
| `after_cellpose`                | After `RESOLVE_CELLPOSE`, before transcript patching or downstream transcript-based segmentation |
| `after_stardist`                | After Stardist resolution                                                                        |
| `after_transcript_segmentation` | After Baysor, Comseg, or Proseg                                                                  |
| `before_aggregation`            | Immediately before `AGGREGATE`                                                                   |
| `after_aggregation`             | Immediately after `AGGREGATE`                                                                    |
| `before_output`                 | After optional annotation/preprocessing and before final explorer/report generation              |

## Adding a new operation

1. Create a Python class in `operations.py` (or a new file imported by the registry) subclassing `Operation`.
2. Register it in `REGISTRY`.
3. Add the operation metadata to `modules/local/utils.nf::getSpatialDataStepOperationMetadata()` so that early parameter validation accepts it and can check supported stages / required arguments.
4. Add tests and documentation as appropriate.

Do not add operation-specific branches to `workflows/sopa.nf`.

## Configuration

Pipeline users configure transformations via `spatialdata_steps`:

```yaml
spatialdata_steps:
  - name: noop
    stage: after_conversion
    args: {}
```

The list order is preserved. An empty list adds no transform tasks and leaves existing pipeline behavior unchanged.

## Manifests

Each executed stage writes a JSON manifest to:

```text
pipeline_info/spatialdata_steps/{sample}/{stage}.json
```

Manifests contain:

- sample, stage, and technology;
- ordered operations and their complete sanitized arguments;
- affected element types;
- before/after SpatialData summaries (element keys);
- operation-specific reports.

Manifests intentionally exclude unstable timestamps or nondeterministic values.

## Implementation notes

- `SPATIALDATA_TRANSFORM` is a single Nextflow process that applies the operations for one sample/stage.
- `SPATIALDATA_TRANSFORM_STAGE` is a thin subworkflow in `subworkflows/local/spatialdata_transform/` that invokes the process and returns both the transformed `[meta, sdata_path]` channel and a `versions.yml` channel. `workflows/sopa.nf` calls this subworkflow at each configured hook.
- The process copies the input `.zarr` into its work directory before applying operations, so `EXPLORER_RAW` (which reads the unmodified converted object) cannot race a mutating transform.
- The `transform_module_dir` input hashes the Python implementation files, ensuring `-resume` invalidates cached transform tasks when operation code changes.
