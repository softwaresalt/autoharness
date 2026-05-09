---
title: Reference Library
description: "Guide to the community agent and skill reference repositories in references/ — how to browse, refresh, and use them for template curation"
---

# Reference Library

The `references/` directory contains read-only git submodules that serve as
source material for curating community templates in `templates/community/`.

These repositories are **never deployed to target workspaces**. They exist
solely within the autoharness development workspace to give template authors
direct file-system access to community patterns.

## Repositories

### `references/awesome-copilot`

**Source**: [github/awesome-copilot](https://github.com/github/awesome-copilot)

The richest reference in the library. Contains production-proven harness
artifacts across all major categories:

| Directory | Contents |
|---|---|
| `agents/` | Agent definition files (`.agent.md`) |
| `skills/` | Skill workflow files (`SKILL.md`) |
| `instructions/` | Instruction files (`.instructions.md`) |
| `hooks/` | Git hook scripts |
| `workflows/` | GitHub Actions workflows |
| `cookbook/` | Annotated examples and patterns |
| `plugins/` | Editor integration plugins |

**Best for**: Discovering established agent and skill patterns maintained by
the GitHub Copilot team.

---

### `references/awesome-agent-skills`

**Source**: [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills)

A curated index of agent skill patterns.

**Best for**: Discovering skill patterns for specific problem domains.

---

### `references/awesome-claude-skills`

**Source**: [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)

Claude-focused skill implementations with composable, action-oriented
patterns. Contains working skill directories organized by domain.

**Best for**: Claude-specific skill patterns and composition approaches.

---

### `references/ai-skills`

**Source**: [iliaal/ai-skills](https://github.com/iliaal/ai-skills)

General-purpose AI skill patterns in a `skills/` directory layout.

**Best for**: Model-agnostic skill implementations suitable for broad
adaptation.

---

### `references/awesome-agents`

**Source**: [kyrolabs/awesome-agents](https://github.com/kyrolabs/awesome-agents)

A curated index of agent frameworks, tools, and patterns from across the
ecosystem.

**Best for**: Discovery and research — identifying frameworks and patterns
worth evaluating for template curation.

---

### `references/agent-skills`

**Source**: [CommandCodeAI/agent-skills](https://github.com/CommandCodeAI/agent-skills)

Composable agent skill implementations organized under a `skills/` directory.

**Best for**: Concrete, composable skill implementations ready for adaptation.

---

## Keeping references current

Submodules are pinned to a specific commit at clone time. To update all
submodules to the latest remote HEAD:

```sh
git submodule update --remote
git add references/
git commit -m "chore: update community reference submodules to latest HEAD"
```

To update a single submodule:

```sh
git submodule update --remote references/awesome-copilot
git add references/awesome-copilot
git commit -m "chore: update references/awesome-copilot to latest HEAD"
```

To inspect the current pinned commit for each submodule:

```sh
git submodule status
```

## How to use references for template curation

1. **Browse** the relevant `references/` subdirectory for patterns that
   solve a real harness need.

2. **Read the source file** to understand the pattern's assumptions, inputs,
   and outputs.

3. **Check the license** — all 6 reference repos use permissive licenses
   (MIT or similar). Attribute the source in the template's YAML frontmatter.

4. **Adapt** — replace hard-coded values with `{{VARIABLE}}` placeholders.
   Technology-specific content must be extracted into variables or removed.

5. **Place** the adapted template in `templates/community/` following the
   naming convention documented in `templates/community/README.md`.

6. **Register** any new template variables in the variable resolution table
   in `.github/skills/install-harness/SKILL.md`.

7. **Validate** by resolving all variables manually against at least three
   technology profiles (Rust, Go, Python/TypeScript) and confirming the
   output is valid Markdown with no unresolved `{{...}}`.

## What NOT to do

* Do not copy files from `references/` directly into `templates/` without
  adapting them — unparameterized templates will install technology-specific
  content into every target workspace.
* Do not run build tools inside submodule directories — they are read-only
  references.
* Do not commit changes to files inside `references/` — submodule directories
  are read-only from the parent repo's perspective.
* Do not add `references/` content to `pyproject.toml` distribution targets —
  these files must never be packaged into the autoharness wheel or distribution.
