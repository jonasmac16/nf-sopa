# Apptainer execution workflow

- Locate the project's documented image/reference and invocation before constructing a new command.
- Record image identity (path/reference plus digest/version when available), bind mounts, working directory, and relevant environment variables.
- Prefer executing through the documented container instead of changing the host environment.
- Do not rebuild an image or modify an external container-definition repository unless explicitly requested.
- If a language server runs on the host while analysis runs in a container, treat LSP diagnostics as advisory when package/library versions differ; container-based project checks are authoritative.
