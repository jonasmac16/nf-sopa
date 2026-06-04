{ pkgs ? import <nixpkgs> {} }:

let
  mambaRoot = builtins.toString ./.mamba;
in (pkgs.buildFHSEnv {
  name = "nf-sopa-dev";
  targetPkgs = pkgs: with pkgs; [ micromamba apptainer ];
  profile = ''
    export MAMBA_ROOT_PREFIX="${mambaRoot}"
    export MAMBA_NO_BANNER=1

    export NXF_APPTAINER_CACHEDIR="$PWD/.apptainer"
    export NXF_APPTAINER_LIBRARYDIR="$PWD/.apptainer"
    mkdir -p "$NXF_APPTAINER_CACHEDIR"

    eval "$(micromamba shell hook --shell=bash)"

    if [ ! -d "${mambaRoot}/envs/nf-sopa" ]; then
      echo "Creating mamba environment 'nf-sopa' ..."
      micromamba create -n nf-sopa \
        -c conda-forge -c bioconda \
        nextflow python pip nf-core \
        -y
    fi

    micromamba activate nf-sopa
    echo ""
    echo "Micromamba environment 'nf-sopa' active."
    echo "Run: nextflow run . -profile apptainer --outdir results"
  '';
  runScript = "bash";
}).env
