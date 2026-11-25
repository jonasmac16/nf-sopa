process SPATIALDATA_TRANSFORM {
    label "process_medium"
    tag "${meta.sample}:${stage}"

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container
        ? 'https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/41/41ba11ed68351d07343e61d1aacaf95b61af20a9bb943e2b3c1829507d970dd7/data'
        : 'community.wave.seqera.io/library/python_sopa:56fd765d45ba1fcc' }"

    publishDir [
        path: { "${params.outdir}/pipeline_info/spatialdata_steps/${meta.sample}" },
        mode: params.publish_dir_mode,
        saveAs: { filename -> filename == 'manifest.json' ? "${stage}.json" : null },
    ]

    input:
    tuple val(meta), path(sdata_path)
    val stage
    val operations_json
    val technology
    path transform_module_dir

    output:
    tuple val(meta), path("${meta.sdata_dir}"), emit: sdata
    path "manifest.json", emit: manifest
    path "versions.yml", emit: versions

    script:
    // Serialize only the fields the Python executor needs, avoiding potential
    // recursion from Nextflow meta-map values.
    def meta_json = groovy.json.JsonOutput.toJson([
        sample: meta.sample,
        sdata_dir: meta.sdata_dir,
        explorer_dir: meta.explorer_dir,
        technology: technology,
    ])
    """
    cat <<'OPJSON' > operations.json
    ${operations_json}
    OPJSON

    cat <<'METAJSON' > meta.json
    ${meta_json}
    METAJSON

    # Work on a copy so that upstream readers (e.g. EXPLORER_RAW) cannot race
    # a mutating transform on the same zarr directory. The staged input already
    # uses ${meta.sdata_dir}, so copy to a temporary name first and then replace
    # the staged directory with the transformed copy.
    cp -rL ${sdata_path} transformed.zarr

    python ${transform_module_dir}/transform.py \
        --sdata-path transformed.zarr \
        --stage ${stage} \
        --operations operations.json \
        --meta-file meta.json \
        --manifest manifest.json

    rm -rf ${sdata_path}
    mv transformed.zarr ${meta.sdata_dir}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        sopa: \$(sopa --version)
        spatialdata: \$(python -c "import spatialdata; print(spatialdata.__version__)" 2> /dev/null)
    END_VERSIONS
    """
}
