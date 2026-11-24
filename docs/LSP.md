# OpenCode startup and LSP

## Standard startup

Start OpenCode from the project root with the standard command:

```sh
opencode
```

Use the host installation for routine work.

## Apptainer/container startup

When the documented environment is an Apptainer container, run OpenCode through the container instead of the host installation. The exact invocation depends on the image and entry point recorded in `.opencode/project-profile.md` or `AGENTS.md`, for example:

```sh
apptainer exec <image.sif> opencode
# or
apptainer run <image.sif> opencode
```

## LSP integration

Project LSP configuration is stored in `opencode.json`. OpenCode may use installed language servers for navigation and advisory diagnostics when `permission.lsp` is `allow`. Availability depends on the host/container environment and the relevant language runtime.

Do not rely on LSP as the sole form of verification. Treat project lint, type-check, test, and compiler commands as authoritative, particularly when a language server runs on the host while analysis executes inside Apptainer.
