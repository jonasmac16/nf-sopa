# Scientific project profile

Status: initialized

## Domain and analysis type

nf-core/sopa: a Nextflow pipeline for technology-invariant processing of image-based spatial omics at single-cell resolution (spatial transcriptomics and multiplex imaging). It ingests vendor outputs (Xenium, Visium HD, MERSCOPE, CosMx, PhenoCycler, MACSima, Molecular Cartography, OME-TIFF), optionally performs tissue and cell segmentation, aggregates transcripts or channel intensities to cells, optionally annotates/preprocesses them, and writes a SpatialData `.zarr` object and an `.explorer` directory for visualization.

This repository is the workflow implementation; downstream statistical inference or cohort-level analysis is outside the pipeline's scope and is not encoded here.

## Languages

- **Primary:** Nextflow/Groovy.
- **Supporting:** Python — only for existing Sopa/SpatialData/Scanpy/ComSeg/Cellpose/Stardist interfaces, version introspection, Python-dict parameter strings, the narrowly-scoped SpatialData transformation helpers under `modules/local/spatialdata_transform/`, and downstream output analysis. Keep pipeline orchestration in Nextflow/Groovy unless explicitly requested.
- **Unused:** R and Julia.
- **Documentation:** Markdown; no project notebooks, Quarto, or R Markdown found.

## Scientific design

- **Unit of observation:** raw transcripts and imaging-channel measurements; segmented cells are derived observations.
- **Unit of inference:** not defined by this pipeline. Per-sample outputs are produced; any cohort-level inference is the responsibility of downstream analysis.
- **Hierarchy:** a samplesheet row corresponds to one biological sample/region (or one Visium HD slide). Subject relationships, biological/technical replicates, pairing, conditions, batches, or longitudinal structure are not modeled in the samplesheet or schema.
- **Patches:** image and transcript patches are computational subdivisions for scalable segmentation. They are not biological or technical replicates and must not be treated as independent observations in inference.

## Reference resources

Versioned resources that affect results and must be matched to the assay/species:

- **Visium HD:** Space Ranger reference transcriptome. Default is `refdata-gex-GRCh38-2020-A.tar.gz`; `spaceranger_probeset` is user-specified. Do not silently use the human default for mouse or other references.
- **Sopa Python package:** currently 2.2.12 (per module `environment.yml` files).
- **Python runtime:** 3.12 in module environments.
- **Cellpose:** major version 3 (Cellpose 3.1.1.3) is the default; version 4 (Cellpose 4.2.1.1) can be selected with `--cellpose_version 4`. The `gpu` profile selects the matching pytorch/CUDA container image. Effective container images are recorded in `conf/modules.config` and `docs/UPSTREAM.md`.
- **Segmentation models:** Cellpose/Stardist model names/types and priors are user-specified per predefined profile or CLI parameters.
- **Spatial coordinates, micron-to-pixel transformations, image scales, and channel/transcript identifiers** must be preserved exactly; changing them changes biological interpretation.

## Reproducibility and environment

- **Orchestration:** Nextflow >=25.10.4; pipeline version 1.0.2.
- **Execution:** container/Conda per process. Docker and Singularity are recommended by nf-core; Apptainer is supported via the `apptainer` profile. There is no project-specific Apptainer image or required container invocation.
- **External inputs:** no DataLad inputs are part of this repository. User samplesheet paths point to local or mounted raw data; treat source data as immutable.
- **Caching/resumption:** `-resume` depends on file contents, not just names. Changing Cellpose version or segmentation arguments requires a fresh work directory because `.sopa_cache` is reused in place and not automatically invalidated.
- **Provenance:** when Cellpose version matters, record the effective container/Conda environment identity; the selected image is version- and profile-dependent.

## Critical invariants

1. Do not treat patch-level outputs or individual cells as independent biological replicates.
2. Do not apply the default GRCh38 Space Ranger reference to non-human data.
3. Preserve sample identity from samplesheet to output directory; output folders are `{sample}.zarr` and `{sample}.explorer`.
4. Segmentation choices and their parameters (Cellpose, Baysor, Proseg, Comseg, Stardist, priors) are scientifically consequential; do not change them silently.
5. Coordinate systems, transformations, and units (microns vs pixels) must remain consistent across patches and output objects.
