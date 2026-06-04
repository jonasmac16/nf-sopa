process COMBINE_SEGMENTATION_CHANNELS {
    label "process_low"
    tag "${meta.sample}"

    conda "${moduleDir}/environment.yml"
    container "${workflow.containerEngine == 'apptainer' && !task.ext.singularity_pull_docker_container
        ? 'docker://quentinblampey/sopa:2.1.11'
        : 'docker.io/quentinblampey/sopa:2.1.11'}"

    input:
    tuple val(meta), path(sdata_path)
    val cli_arguments

    output:
    tuple val(meta), path(sdata_path)

    script:
    """
    python /opt/assets/monkey_patch_sopa_channels.py segmentation combine-channels ${sdata_path} ${cli_arguments}
    """
}
