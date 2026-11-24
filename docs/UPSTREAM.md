# Upstream references and maintenance notes

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
