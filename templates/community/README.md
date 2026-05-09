---
title: Community Templates
description: "Curated agent and skill templates distilled from community reference libraries in references/"
---

# Community Templates

This directory holds curated autoharness templates distilled from community
agent and skill libraries. Templates here follow all autoharness conventions
and are ready for installation into target workspaces.

## What belongs here

A template belongs in `templates/community/` when it:

1. Originates from a reference library in `references/` (see below)
2. Has been adapted to use `{{VARIABLE}}` placeholders for all
   customization points
3. Is technology-agnostic — no framework, language, or tool assumptions
   baked in
4. Has been validated against at least 3 technology profiles (Rust, Go,
   Python/TypeScript)
5. Produces valid Markdown with no unresolved `{{...}}` after variable
   substitution

## Naming convention

Community templates use the same conventions as first-party templates:

| Artifact type | File pattern |
|---|---|
| Agent definition | `{name}.agent.md.tmpl` |
| Skill workflow | `{skill-name}/SKILL.md.tmpl` |
| Instruction file | `{name}.instructions.md.tmpl` |
| Prompt file | `{name}.prompt.md.tmpl` |

## Curation workflow

1. **Browse** — identify a promising pattern in `references/` (see
   `docs/reference-library.md` for per-repo inventory)
2. **Evaluate** — assess against the curation criteria above; consult the
   source repo's README and license
3. **Adapt** — replace hard-coded values with `{{VARIABLE}}` placeholders;
   document new variables in `install-harness/SKILL.md`
4. **Test** — resolve variables manually against a Rust profile, a Go
   profile, and a Python or TypeScript profile; confirm valid Markdown output
5. **Place** — add the `.tmpl` file here under the appropriate subdirectory
6. **Register** — if the template introduces new capability pack behavior,
   update the schemas and `install-harness/SKILL.md` per the pack integration
   pattern in `docs/harness-architecture.instructions.md`

## Source attribution

Each template file should include a comment in its YAML frontmatter
identifying the community source:

```yaml
---
# Source: references/awesome-copilot/agents/example.agent.md
# License: MIT
title: Example Agent
---
```

## Reference libraries

| Directory | Repository | Content type |
|---|---|---|
| `references/awesome-copilot` | [github/awesome-copilot](https://github.com/github/awesome-copilot) | Agents, skills, instructions, prompts, hooks, workflows |
| `references/awesome-agent-skills` | [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | Curated agent skill patterns |
| `references/awesome-claude-skills` | [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | Claude-focused skill implementations |
| `references/ai-skills` | [iliaal/ai-skills](https://github.com/iliaal/ai-skills) | General AI skill patterns |
| `references/awesome-agents` | [kyrolabs/awesome-agents](https://github.com/kyrolabs/awesome-agents) | Curated agent frameworks and patterns |
| `references/agent-skills` | [CommandCodeAI/agent-skills](https://github.com/CommandCodeAI/agent-skills) | Composable agent skill implementations |
