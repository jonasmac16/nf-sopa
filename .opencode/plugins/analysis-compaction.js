import { readFile } from "node:fs/promises"
import { join } from "node:path"
import { Plugin } from "@opencode-ai/plugin"

const continuationContext = `
## Data-analysis continuation requirements

When these facts are known and still relevant, preserve them in the compaction checkpoint. Do not invent missing values.

### Objective and scientific state
- Current analysis question/objective and status.
- Project-specific scientific/language constraints from the canonical project profile when relevant to resuming correctly; do not invent or reinterpret them.
- Important scientific/statistical assumptions and decisions.
- Filtering, exclusion, grouping, weighting, unit, and join-cardinality decisions.
- Random seeds and important parameters that affect results.

### Input provenance
- External DataLad dataset paths or documented sources.
- Exact dataset revisions/commits used.
- Specific input files/subsets obtained or consumed.
- Whether required annexed content is locally available.

### Execution environment
- Apptainer image/path/reference and digest/version if known.
- Relevant bind mounts, environment variables, working directory, and invocation command.
- Whether commands ran in the intended container or on the host.

### Code and output state
- Files intentionally modified and important entry points/functions involved.
- Intermediate/final outputs produced, invalidated, stale, or pending.
- Decisions not obvious from committed code, AGENTS.md, or the canonical project profile.

### Verification
- Exact checks/tests/linters/type checks/data validations run and outcomes.
- Checks still outstanding or blocked, including why.
- Known blockers, unresolved anomalies, and next concrete actions.

Prefer compact factual bullets. Do not preserve conversational filler, repeated tool output, or facts already obvious from durable project files unless needed to resume correctly.
`

export default Plugin.define({
  id: "analysis-compaction",
  async setup(ctx) {
    const root = ctx.location?.project?.directory ?? ctx.location?.directory ?? process.cwd()
    const profilePath = join(root, ".opencode", "project-profile.md")

    const registration = await ctx.session.hook("context", async (event) => {
      if (event.kind === "primary" || event.kind === "compaction") {
        try {
          const profile = (await readFile(profilePath, "utf8")).trim()
          if (profile) {
            event.system.push({
              text: `## Canonical scientific project profile\n\n${profile}`,
            })
          }
        } catch {
          // The profile is optional while a template is being initialized.
        }
      }

      if (event.kind === "compaction") {
        event.system.push({ text: continuationContext })
      }
    })

    return () => registration.dispose()
  },
})
