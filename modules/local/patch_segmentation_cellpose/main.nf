process PATCH_SEGMENTATION_CELLPOSE {
    label "process_single"
    tag "${meta.sample}"

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
?         'oras://community.wave.seqera.io/library/sopa_cellpose:6416f5381a2b4d94'
:         'oras://community.wave.seqera.io/library/sopa_cellpose:6416f5381a2b4d94' }"

    input:
    tuple val(meta), path(sdata_path), val(cli_arguments), val(index), val(n_patches)

    output:
    tuple val(meta), path(sdata_path), path("${index}.parquet"), val(n_patches)

    script:
    """
    mkdir ./cellpose_cache
    export CELLPOSE_LOCAL_MODELS_PATH=./cellpose_cache

    sopa segmentation cellpose ${sdata_path} --patch-index ${index} ${cli_arguments}

    mv ${sdata_path}/.sopa_cache/cellpose_boundaries/${index}.parquet ${index}.parquet
    """
}
