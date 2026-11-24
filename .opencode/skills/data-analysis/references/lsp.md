# LSP usage

Use LSP as a navigation and diagnostic accelerator, not as the sole source of truth.

When available, prefer targeted operations such as definition, references, hover, document/workspace symbols, implementation, and call hierarchy over broad file reads.

Expected baseline servers:

- Python: OpenCode built-in Pyright integration when supported and `pyright` is installed/configured.
- Julia: OpenCode built-in JuliaLS integration when supported and Julia + LanguageServer.jl are available.
- R: custom `R --no-echo -e 'languageserver::run()'` server when the R `languageserver` package is installed.

OpenCode runtime support differs by generation/version. If the LSP tool/runtime is unavailable, fall back to repository grep/search plus the project's lint/type/compiler/test commands. Treat those project commands as authoritative verification even when LSP is active.
