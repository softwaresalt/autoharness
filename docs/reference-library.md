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

Submodules are pinned to a specific commit at clone time. Each submodule has
an explicit `branch` entry in `.gitmodules` (matching its repository's default
branch: `main` or `master` as appropriate). `git submodule update --remote`
follows this `branch` setting to advance the pinned commit.

To update all submodules to their latest tracked branch HEAD:

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

3. **Check the license** — verify the license of the specific reference repo
   and pinned commit you are drawing from. Licenses can vary and change over
   time. Record the license in the curated template's YAML frontmatter
   alongside the source attribution.

4. **Adapt** — replace hard-coded values with `{{VARIABLE}}` placeholders.
   Technology-specific content must be extracted into variables or removed.

5. **Place** the adapted template in `templates/community/` following the
   naming convention documented in `templates/community/README.md`.

6. **Register** any new template variables in the variable resolution table
   in `.github/skills/install-harness/SKILL.md`.

7. **Validate** by resolving all variables manually against at least three
   technology profiles (Rust, Go, Python/TypeScript) and confirming the
   output is valid Markdown with no unresolved `{{...}}`.

8. **Register in the community template registry** — add an entry to
   `templates/community/registry.yaml` with the template's metadata so
   install and tune workflows can discover it. See the
   [Community Template Registry](#community-template-registry) section below.

## Community Template Registry

The registry at `templates/community/registry.yaml` catalogs every curated
community template with structured metadata. It enables the installer and
tuner to select relevant templates by matching entries against the workspace
profile — without scanning raw template file content.

**Schema**: `schemas/community-template-registry.schema.json`

### What the registry provides

Each entry contains:

| Field | Purpose |
|---|---|
| `template_id` | Unique kebab-case slug (e.g., `code-review-checklist`) |
| `artifact_type` | `agent`, `skill`, `instruction`, or `prompt` |
| `title` / `description` | Human-readable summary detailed enough for the installer to assess relevance |
| `source_repo` / `source_path` | Attribution to the `references/` submodule and original file |
| `license` | License of the source repository |
| `template_path` | Path to the `.tmpl` file relative to `autoharness_home` |
| `applicable_profiles` | Technology profile tags this template applies to (e.g., `any`, `python`, `web-app`) |
| `prerequisite_packs` | Capability packs required for the template to be useful |
| `tags` | Freeform tags for categorization and search |
| `variables_introduced` | New `{{VARIABLE}}` names beyond the standard set |
| `primitives_deepened` | Which of the 10 primitives this template relates to |

### How the installer uses it

During Step 1.3a of the install-harness skill, the installer:

1. Reads the registry from `autoharness_home`
2. Filters entries by `applicable_profiles` and `prerequisite_packs`
3. Ranks matches by profile overlap and primitive relevance
4. Presents the ranked list to the operator for opt-in selection
5. Records installed community templates in the harness manifest

Community templates are **never auto-installed** — the operator always
chooses which to include.

### How the tuner uses it

During Step 1.6 of the tune-harness skill, the tuner checks for community
template drift: templates removed from the registry, new matches for the
workspace profile, prerequisite packs no longer satisfied, and checksum
changes from upstream updates.

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
