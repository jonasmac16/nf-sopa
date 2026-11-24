# Project-local OpenCode configuration profiles

All profile operations are project-local. None modifies `~/.config/opencode/`.

Inactive profile sources live under `.opencode/profiles/`. Only root `opencode.json` and `.opencode/plugins/analysis-compaction.js` are active at runtime.

## V1/current profile (checked-in default)

`.opencode/profiles/opencode.v1.json` enables:

- automatic compaction;
- old-tool-output pruning;
- a 20k reserved buffer;
- project skill/external-directory/LSP permissions;
- custom R language-server declaration in the unspecialized template;
- `.opencode/project-profile.md` through the `instructions` array.

`.opencode/profiles/plugins/v1/analysis-compaction.js` uses the V1 `experimental.session.compacting` hook.

Select/reset V1 for this repository with:

```sh
./.opencode/bin/select-profile.sh v1
```

## V2 beta profile

`.opencode/profiles/opencode.v2.json` enables checkpoint compaction with a 12k recent-context tail and 20k buffer. V2 accepts the LSP declaration but currently has no LSP runtime.

Current V2 also parses but does not resolve configured `instructions` paths. Therefore its profile intentionally omits the `instructions` array and `.opencode/profiles/plugins/v2/analysis-compaction.js` injects `.opencode/project-profile.md` into primary and compaction model context through the V2 context hook.

Select V2 for this repository with:

```sh
./.opencode/bin/select-profile.sh v2
```

## Language specialization

`/init-analysis` may remove language-specific support after user confirmation. When it removes a language-only LSP configuration, it must update:

```text
./opencode.json
./.opencode/profiles/opencode.v1.json
./.opencode/profiles/opencode.v2.json
```

so switching profiles later does not re-enable a pruned language.

## What the selector changes

The selector changes only:

```text
./opencode.json
./.opencode/plugins/analysis-compaction.js
```

It first copies previous local files into ignored `.opencode/backups/`. Profile source files themselves are not auto-discovered by OpenCode.
