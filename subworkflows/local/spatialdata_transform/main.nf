include { SPATIALDATA_TRANSFORM } from '../../../modules/local/spatialdata_transform'

workflow SPATIALDATA_TRANSFORM_STAGE {
    take:
    ch_input        // channel: [meta, sdata_path]
    stage           // string:  pipeline stage identifier
    operations_json // string: JSON-serialized operation configs for this stage
    technology      // string:  pipeline technology parameter

    main:
    def transform_module_dir = file("${projectDir}/modules/local/spatialdata_transform")
    SPATIALDATA_TRANSFORM(ch_input, stage, operations_json, technology, transform_module_dir)

    emit:
    sdata    = SPATIALDATA_TRANSFORM.out.sdata
    versions = SPATIALDATA_TRANSFORM.out.versions
}
