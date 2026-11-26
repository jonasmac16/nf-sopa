# Upstream references and maintenance notes

Checked: 2026-11-26.

## Cellpose version environments

The pinned nf-core/sopa 1.0.2 interface provides distinct Cellpose 3 and Cellpose 4 Conda environments and container images. The local configuration mirrors these pins:

- Cellpose 3 CPU: `modules/local/patch_segmentation_cellpose/environment.yml`.
- Cellpose 3 GPU: `modules/local/patch_segmentation_cellpose/environment_gpu_v3.yml`.
- Cellpose 4 CPU: `modules/local/patch_segmentation_cellpose/environment_v4.yml`.
- Cellpose 4 GPU: `modules/local/patch_segmentation_cellpose/environment_gpu_v4.yml`.

Container selection for `DOWNLOAD_CELLPOSE_MODEL`, `PATCH_SEGMENTATION_CELLPOSE`, and `RESOLVE_CELLPOSE` is made in `conf/modules.config`:

- Cellpose 3 CPU (Docker): `community.wave.seqera.io/library/python_sopa_cellpose:b504a8c810aa7c01`
- Cellpose 3 CPU (Singularity): `sha256:1c06334f438946057dc2acdc6580080d740a9b416f479035302c898f055fda8b`
- Cellpose 3 GPU (Docker): `community.wave.seqera.io/library/python_sopa_cellpose_pytorch-gpu_cuda-version:07f6e8d7a26a8935`
- Cellpose 3 GPU (Singularity): `sha256:9dcbf194acd8fea8cd4f87d39944de3b25f4049b5fea53d4c83391b62d5637c9`
- Cellpose 4 CPU (Docker): `community.wave.seqera.io/library/python_sopa_pytorch_torchvision_pruned:105f9f4d5bd0c6cc`
- Cellpose 4 CPU (Singularity): `sha256:e0ebeba05ff8e00654ebee2f7632c241c4160437bbae13e88e554333d9d4bba6`
- Cellpose 4 GPU (Docker): `community.wave.seqera.io/library/python_sopa_pytorch-gpu_cuda-version_pruned:380adfda61f590c9`
- Cellpose 4 GPU (Singularity): `sha256:660aed8b01c93e32fd010ba5e8475ef86f657fdd5aa83d687dd0069c18ec402f`

The active `gpu` profile selects the GPU image of the requested major version. Users can still override any process container via an explicit, immutable SHA-256-addressed reference in a custom config.

## General upstream references

Checked: 2026-09-08.

- Project config and precedence: https://opencode.ai/docs/config/
- Instructions and `AGENTS.md`: https://opencode.ai/docs/rules/
- Project skills: https://opencode.ai/docs/skills/
- Project commands: https://opencode.ai/docs/commands/
- Project agents: https://opencode.ai/docs/agents/
- Project plugins: https://opencode.ai/docs/plugins/
- V1/current LSP tool and servers: https://opencode.ai/docs/tools/ and https://opencode.ai/docs/lsp/
- V2 instructions: https://opencode.ai/v2/docs/instructions
- V2 compaction: https://opencode.ai/v2/docs/compaction
- V2 LSP status: https://opencode.ai/v2/docs/lsp
- V2 plugin API/context hooks: https://opencode.ai/v2/docs/build/plugins/
- R languageserver: https://github.com/REditorSupport/languageserver

When upgrading OpenCode, re-check especially:

1. compaction field names;
2. whether V2 starts resolving `instructions` paths (if it does, avoid double-injecting the project profile);
3. V2 LSP runtime status;
4. command `subagent`/legacy `subtask` fields;
5. skill discovery/frontmatter behavior;
6. V2 plugin hook naming/API stability.
