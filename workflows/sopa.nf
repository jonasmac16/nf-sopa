/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { paramsSummaryMap        } from 'plugin/nf-schema'
include { softwareVersionsToYAML  } from '../subworkflows/nf-core/utils_nfcore_pipeline'
include { methodsDescriptionText  } from '../subworkflows/local/utils_nfcore_sopa_pipeline'

include { TO_SPATIALDATA          } from '../modules/local/to_spatialdata'
include { MAKE_IMAGE_PATCHES      } from '../modules/local/make_image_patches'
include { MAKE_TRANSCRIPT_PATCHES } from '../modules/local/make_transcript_patches'
include { TISSUE_SEGMENTATION     } from '../modules/local/tissue_segmentation'
include { AGGREGATE               } from '../modules/local/aggregate'
include { EXPLORER                } from '../modules/local/explorer'
include { EXPLORER_RAW            } from '../modules/local/explorer_raw'
include { SCANPY_PREPROCESS       } from '../modules/local/scanpy_preprocess'
include { REPORT                  } from '../modules/local/report'
include { FLUO_ANNOTATION         } from '../modules/local/fluo_annotation'
include { SPACERANGER             } from '../subworkflows/local/spaceranger'
include { INPUT_CHECK             } from '../subworkflows/local/input_check'
include { CELLPOSE                } from '../subworkflows/local/cellpose'
include { STARDIST                } from '../subworkflows/local/stardist'
include { PROSEG                  } from '../subworkflows/local/proseg'
include { COMSEG                  } from '../subworkflows/local/comseg'
include { BAYSOR                  } from '../subworkflows/local/baysor'


include { argsCLI                       } from '../modules/local/utils'
include { extractOutsDir                  } from '../modules/local/utils'
include { SPATIALDATA_TRANSFORM_STAGE as SPATIALDATA_TRANSFORM_AFTER_CONVERSION;
          SPATIALDATA_TRANSFORM_STAGE as SPATIALDATA_TRANSFORM_BEFORE_IMAGE_SEGMENTATION;
          SPATIALDATA_TRANSFORM_STAGE as SPATIALDATA_TRANSFORM_AFTER_CELLPOSE;
          SPATIALDATA_TRANSFORM_STAGE as SPATIALDATA_TRANSFORM_AFTER_STARDIST;
          SPATIALDATA_TRANSFORM_STAGE as SPATIALDATA_TRANSFORM_AFTER_TRANSCRIPT_SEGMENTATION;
          SPATIALDATA_TRANSFORM_STAGE as SPATIALDATA_TRANSFORM_BEFORE_AGGREGATION;
          SPATIALDATA_TRANSFORM_STAGE as SPATIALDATA_TRANSFORM_AFTER_AGGREGATION;
          SPATIALDATA_TRANSFORM_STAGE as SPATIALDATA_TRANSFORM_BEFORE_OUTPUT } from '../subworkflows/local/spatialdata_transform'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    SPATIALDATA TRANSFORMATION HELPERS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

def get_spatialdata_steps() {
    return params.spatialdata_steps ?: []
}

def stage_operations_json(String stage) {
    def ops = get_spatialdata_steps().findAll { it.stage == stage }
    return groovy.json.JsonOutput.toJson(ops)
}

def has_stage_ops(String stage) {
    return get_spatialdata_steps().any { it.stage == stage }
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow SOPA {
    take:
    ch_samplesheet // channel: samplesheet read in from --input
    outdir

    main:

    def ch_versions = channel.empty()

    if (params.technology == "visium_hd") {
        INPUT_CHECK(ch_samplesheet)
        (ch_input_spatialdata, versions) = SPACERANGER(INPUT_CHECK.out.ch_spaceranger_input, INPUT_CHECK.out.ch_versions)

        ch_input_spatialdata = ch_input_spatialdata.map { meta, out -> [meta, extractOutsDir(out[0]), meta.image] }

        ch_versions = ch_versions.mix(versions)
    }
    else {
        ch_input_spatialdata = ch_samplesheet.map { meta -> [meta, meta.data_dir, []] }
    }

    (ch_spatialdata, versions) = TO_SPATIALDATA(ch_input_spatialdata)
    ch_versions = ch_versions.mix(versions)

    ch_explorer_raw = ch_spatialdata.map { meta, sdata_path -> [meta, sdata_path, params.technology == "xenium" ? meta.data_dir : []] }
    EXPLORER_RAW(ch_explorer_raw)

    if (has_stage_ops('after_conversion')) {
        (ch_after_conversion, versions) = SPATIALDATA_TRANSFORM_AFTER_CONVERSION(ch_spatialdata.map { meta, sdata_path -> [meta, sdata_path] }, 'after_conversion', stage_operations_json('after_conversion'), params.technology)
        ch_versions = ch_versions.mix(versions)
    } else {
        ch_after_conversion = ch_spatialdata
    }

    if (params.use_tissue_segmentation) {
        ch_tissue_seg = TISSUE_SEGMENTATION(ch_after_conversion, argsCLI("tissue_segmentation"))
    }
    else {
        ch_tissue_seg = ch_after_conversion
    }

    if (has_stage_ops('before_image_segmentation')) {
        (ch_before_image_segmentation, versions) = SPATIALDATA_TRANSFORM_BEFORE_IMAGE_SEGMENTATION(ch_tissue_seg.map { meta, sdata_path -> [meta, sdata_path] }, 'before_image_segmentation', stage_operations_json('before_image_segmentation'), params.technology)
        ch_versions = ch_versions.mix(versions)
    } else {
        ch_before_image_segmentation = ch_tissue_seg
    }

    if (params.use_cellpose) {
        ch_image_patches = MAKE_IMAGE_PATCHES(ch_before_image_segmentation, argsCLI("image_patches"))
        (ch_resolved, versions) = CELLPOSE(ch_image_patches)

        ch_versions = ch_versions.mix(versions)

        if (has_stage_ops('after_cellpose')) {
            (ch_after_cellpose, versions) = SPATIALDATA_TRANSFORM_AFTER_CELLPOSE(ch_resolved.map { meta, sdata_path -> [meta, sdata_path] }, 'after_cellpose', stage_operations_json('after_cellpose'), params.technology)
            ch_versions = ch_versions.mix(versions)
        } else {
            ch_after_cellpose = ch_resolved
        }
        ch_after_staining = ch_after_cellpose
        ch_resolved = ch_after_staining
    }
    else if (params.use_stardist) {
        ch_image_patches = MAKE_IMAGE_PATCHES(ch_before_image_segmentation, argsCLI("image_patches"))
        (ch_resolved, versions) = STARDIST(ch_image_patches)

        ch_versions = ch_versions.mix(versions)

        if (has_stage_ops('after_stardist')) {
            (ch_after_stardist, versions) = SPATIALDATA_TRANSFORM_AFTER_STARDIST(ch_resolved.map { meta, sdata_path -> [meta, sdata_path] }, 'after_stardist', stage_operations_json('after_stardist'), params.technology)
            ch_versions = ch_versions.mix(versions)
        } else {
            ch_after_stardist = ch_resolved
        }
        ch_after_staining = ch_after_stardist
        ch_resolved = ch_after_staining
    }
    else {
        ch_after_staining = ch_before_image_segmentation
        ch_resolved = ch_after_staining
    }

    if (params.use_baysor) {
        ch_transcripts_patches = MAKE_TRANSCRIPT_PATCHES(ch_after_staining, argsCLI("transcript_patches"))
        (ch_resolved, versions) = BAYSOR(ch_transcripts_patches)

        ch_versions = ch_versions.mix(versions)
    }

    if (params.use_comseg) {
        ch_transcripts_patches = MAKE_TRANSCRIPT_PATCHES(ch_after_staining, argsCLI("transcript_patches") + " --write-cells-centroids")
        (ch_resolved, versions) = COMSEG(ch_transcripts_patches)

        ch_versions = ch_versions.mix(versions)
    }

    if (params.use_proseg) {
        if (params.technology == "visium_hd") {
            ch_input_proseg = ch_after_staining.map { meta, sdata_path -> [meta, sdata_path, []] }
        } else {
            ch_input_proseg = MAKE_TRANSCRIPT_PATCHES(ch_after_staining, argsCLI("transcript_patches"))
        }

        (ch_resolved, versions) = PROSEG(ch_input_proseg)

        ch_versions = ch_versions.mix(versions)
    }

    if (has_stage_ops('after_transcript_segmentation')) {
        (ch_after_transcript_segmentation, versions) = SPATIALDATA_TRANSFORM_AFTER_TRANSCRIPT_SEGMENTATION(ch_resolved.map { meta, sdata_path -> [meta, sdata_path] }, 'after_transcript_segmentation', stage_operations_json('after_transcript_segmentation'), params.technology)
        ch_versions = ch_versions.mix(versions)
    } else {
        ch_after_transcript_segmentation = ch_resolved
    }

    if (has_stage_ops('before_aggregation')) {
        (ch_before_aggregation, versions) = SPATIALDATA_TRANSFORM_BEFORE_AGGREGATION(ch_after_transcript_segmentation.map { meta, sdata_path -> [meta, sdata_path] }, 'before_aggregation', stage_operations_json('before_aggregation'), params.technology)
        ch_versions = ch_versions.mix(versions)
    } else {
        ch_before_aggregation = ch_after_transcript_segmentation
    }

    ch_aggregated = AGGREGATE(ch_before_aggregation, argsCLI("aggregate"))

    if (has_stage_ops('after_aggregation')) {
        (ch_after_aggregation, versions) = SPATIALDATA_TRANSFORM_AFTER_AGGREGATION(ch_aggregated.map { meta, sdata_path -> [meta, sdata_path] }, 'after_aggregation', stage_operations_json('after_aggregation'), params.technology)
        ch_versions = ch_versions.mix(versions)
    } else {
        ch_after_aggregation = ch_aggregated
    }

    if (params.use_fluorescence_annotation) {
        (ch_annotated, versions) = FLUO_ANNOTATION(ch_after_aggregation, argsCLI("fluorescence_annotation"))
        ch_versions = ch_versions.mix(versions)
    }
    else {
        ch_annotated = ch_after_aggregation
    }

    if (params.use_scanpy_preprocessing) {
        (ch_preprocessed, versions) = SCANPY_PREPROCESS(ch_annotated, argsCLI("scanpy_preprocessing"))
        ch_versions = ch_versions.mix(versions)
    }
    else {
        ch_preprocessed = ch_annotated
    }

    if (has_stage_ops('before_output')) {
        (ch_before_output, versions) = SPATIALDATA_TRANSFORM_BEFORE_OUTPUT(ch_preprocessed.map { meta, sdata_path -> [meta, sdata_path] }, 'before_output', stage_operations_json('before_output'), params.technology)
        ch_versions = ch_versions.mix(versions)
    } else {
        ch_before_output = ch_preprocessed
    }

    EXPLORER(ch_before_output, argsCLI("explorer"))

    REPORT(ch_before_output)

    //
    // Collate and save software versions
    //
    def topic_versions = channel.topic("versions")
        .distinct()
        .branch { entry ->
            versions_file: entry instanceof Path
            versions_tuple: true
        }

    def topic_versions_string = topic_versions.versions_tuple
        .map { process, tool, version ->
            [ process[process.lastIndexOf(':')+1..-1], "  ${tool}: ${version}" ]
        }
        .groupTuple(by:0)
        .map { process, tool_versions ->
            tool_versions.unique().sort()
            "${process}:\n${tool_versions.join('\n')}"
        }

    def ch_collated_versions = softwareVersionsToYAML(ch_versions.mix(topic_versions.versions_file))
        .mix(topic_versions_string)
        .collectFile(
            storeDir: "${outdir}/pipeline_info",
            name: 'nf_core_'  +  'sopa_software_'  + 'versions.yml',
            sort: true,
            newLine: true
        )
    emit:
    versions       = ch_versions                 // channel: [ path(versions.yml) ]
}
