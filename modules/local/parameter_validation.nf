/*
 * Parameter validation helpers for nf-core/sopa.
 *
 * These checks complement the JSON schema validation performed by the
 * nf-schema plugin. They enforce cross-parameter constraints and CosMx-
 * specific contracts that the schema cannot express.
 */

/**
 * Return the set of pipeline-owned parameter names consumed by the local
 * adapters. This list is used to distinguish first-class parameters from
 * vendor/forwarded parameters and ensures every declared parameter is
 * intentionally handled.
 */
def projectParameterNames() {
    return [
        // Input/output
        'input',
        'outdir',
        // Reader
        'technology',
        'visium_hd_imread_page',
        'reader_kwargs',
        // Patches
        'patch_width_pixel',
        'patch_overlap_pixel',
        'image_scale',
        'patch_width_microns',
        'patch_overlap_microns',
        'prior_shapes_key',
        'unassigned_value',
        // Image preprocessing
        'gaussian_sigma',
        'clip_limit',
        'clahe_kernel_size',
        // Tissue segmentation
        'use_tissue_segmentation',
        'level',
        'mode',
        'tissue_segmentation_kwargs',
        // Proseg
        'use_proseg',
        'command_line_suffix',
        'infer_presets',
        'visium_hd_prior_shapes_key',
        // Baysor
        'use_baysor',
        'baysor_scale',
        'baysor_scale_std',
        'prior_segmentation_confidence',
        'min_molecules_per_cell',
        'min_molecules_per_gene',
        'min_molecules_per_segment',
        'confidence_nn_id',
        'force_2d',
        // Comseg
        'use_comseg',
        'mean_cell_diameter',
        'max_cell_radius',
        'alpha',
        'min_rna_per_cell',
        'allow_disconnected_polygon',
        'norm_vector',
        // Cellpose
        'use_cellpose',
        'cellpose_diameter',
        'cellpose_channels',
        'flow_threshold',
        'cellprob_threshold',
        'cellpose_model_type',
        'pretrained_model',
        'cellpose_version',
        'cellpose_kwargs',
        // Stardist
        'use_stardist',
        'stardist_model_type',
        'prob_thresh',
        'nms_thresh',
        'stardist_channels',
        'stardist_kwargs',
        // SpatialData transformation
        'spatialdata_steps',
        // Fluorescence annotation
        'use_fluorescence_annotation',
        'fluorescence_cell_type_key',
        'marker_cell_dict',
        // Filtering
        'min_area_pixels2',
        'min_area_microns2',
        'min_transcripts',
        'min_intensity_ratio',
        // Aggregation
        'aggregate_genes',
        'aggregate_channels',
        'expand_radius_ratio',
        'aggregate_image_key',
        // Scanpy preprocessing
        'use_scanpy_preprocessing',
        'resolution',
        'check_counts',
        'hvg',
        // Explorer
        'ram_threshold_gb',
        'pixel_size',
        'lazy',
        // Spaceranger
        'spaceranger_reference',
        'spaceranger_probeset',
    ] as Set
}

/**
 * Validate that `cellpose_version`, when provided, is 3 or 4.
 */
def validateCellposeVersion(value) {
    if (value == null) {
        return
    }
    def versionString = value.toString()
    if (versionString !in ['3', '4']) {
        exit 1, "Invalid cellpose_version '${value}'. Only 3 or 4 are supported."
    }
}

/**
 * Validate that a parameter is a Boolean when it is not null.
 */
def validateBoolean(String name, value) {
    if (value != null && !(value instanceof Boolean)) {
        exit 1, "Parameter '${name}' must be a boolean, got ${value.getClass().getSimpleName()}."
    }
}

/**
 * Validate that a parameter is a non-negative number when it is not null.
 */
def validateNonNegativeNumber(String name, value) {
    if (value == null) {
        return
    }
    if (!(value instanceof Number)) {
        exit 1, "Parameter '${name}' must be a number, got ${value.getClass().getSimpleName()}."
    }
    if (value < 0) {
        exit 1, "Parameter '${name}' must be >= 0, got ${value}."
    }
}

/**
 * Validate that a parameter is a positive number when it is not null.
 */
def validatePositiveNumber(String name, value) {
    if (value == null) {
        return
    }
    if (!(value instanceof Number)) {
        exit 1, "Parameter '${name}' must be a number, got ${value.getClass().getSimpleName()}."
    }
    if (value <= 0) {
        exit 1, "Parameter '${name}' must be > 0, got ${value}."
    }
}

/**
 * Validate that an optional string parameter is nonblank and single-line.
 */
def validateNonBlankString(String name, value) {
    if (value == null) {
        return
    }
    if (!(value instanceof CharSequence)) {
        exit 1, "Parameter '${name}' must be a string, got ${value.getClass().getSimpleName()}."
    }
    if (value.toString().trim().isEmpty()) {
        exit 1, "Parameter '${name}' cannot be blank."
    }
    if (value.toString().contains('\n') || value.toString().contains('\r')) {
        exit 1, "Parameter '${name}' must be a single-line string."
    }
}

/**
 * Validate that at least one aggregation mode is enabled. Local finalization
 * and downstream reporting require an aggregated table.
 */
def validateAggregation(Boolean aggregateGenes, Boolean aggregateChannels) {
    if (!aggregateGenes && !aggregateChannels) {
        exit 1, "At least one of 'aggregate_genes' or 'aggregate_channels' must be true."
    }
}

/**
 * Run all synchronous parameter validations.
 */
def validateParameters() {
    validateCellposeVersion(params.cellpose_version)

    validateBoolean('aggregate_genes', params.aggregate_genes)
    validateBoolean('aggregate_channels', params.aggregate_channels)
    validateBoolean('infer_presets', params.infer_presets)

    validateNonNegativeNumber('patch_overlap_microns', params.patch_overlap_microns)
    validateNonNegativeNumber('patch_overlap_pixel', params.patch_overlap_pixel)
    validatePositiveNumber('clahe_kernel_size', params.clahe_kernel_size)
    validateNonNegativeNumber('expand_radius_ratio', params.expand_radius_ratio)

    validateNonBlankString('cellpose_kwargs', params.cellpose_kwargs)
    validateNonBlankString('stardist_kwargs', params.stardist_kwargs)
    validateNonBlankString('reader_kwargs', params.reader_kwargs)
    validateNonBlankString('tissue_segmentation_kwargs', params.tissue_segmentation_kwargs)
    validateNonBlankString('unassigned_value', params.unassigned_value)

    validateAggregation(
        params.aggregate_genes == null ? true : params.aggregate_genes,
        params.aggregate_channels == null ? false : params.aggregate_channels,
    )
}
