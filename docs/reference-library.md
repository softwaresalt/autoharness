---
title: Reference Library
description: "Guide to the community agent and skill reference repositories indexed from references/ — how to browse, refresh, and use them for template curation"
---

# Reference Library

The `references/` directory contains a lightweight index of external
repositories that serve as source material for curating community templates in
`templates/community/`.

These repositories are **never deployed to target workspaces** and are
**not included in the autoharness PyPI wheel** (they are not listed in
`pyproject.toml` distribution targets). End-users who install from PyPI with
`python -m pip install autoharness` never encounter the submodule trees.

The submodules are registered in `.gitmodules` and can be initialised
individually by maintainers when deeper exploration of a reference repository
is needed:

```sh
git submodule update --init references/<name>
```

For example, to initialise the `awesome-copilot` reference locally:

```sh
git submodule update --init references/awesome-copilot
```

Leave submodules uninitialised in day-to-day autoharness development; init
only the specific reference you are actively reading.

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

### `references/mattpocock-eng-skills`

**Source**: [mattpocock/skills](https://github.com/mattpocock/skills)

General-purpose skill implementations and patterns collected in a dedicated
`skills/` repository.

**Best for**: Additional composable skill examples and lightweight workflow
patterns suitable for adaptation.

---

### `references/atv-starterkit`

**Source**: [All-The-Vibes/ATV-StarterKit](https://github.com/All-The-Vibes/ATV-StarterKit)

Starter-kit assets spanning plugins, command surfaces, documentation, and
supporting packages for agent-oriented workflows.

**Best for**: Broader end-to-end reference patterns that combine skills with
supporting tooling and repository structure.

---

## Keeping references current

The submodule registrations in `.gitmodules` are the index of record for these
external repositories. This document (`docs/reference-library.md`) is the
human-readable catalog.

To update the library:

1. Edit `.gitmodules` to add, remove, or rename upstream submodule entries.
2. Run `git submodule sync` after editing `.gitmodules`.
3. Update this document's **Repositories** section to reflect catalog changes.
4. When curating a template, record the exact upstream repository, path, and
   commit or release you used in the curated template metadata.

## How to use references for template curation

1. **Open** the relevant reference submodule path (e.g., `references/awesome-copilot/`) for
   patterns that solve a real harness need. First initialise the submodule:
   `git submodule update --init references/<name>`

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
| `source_repo` / `source_path` | Attribution to the upstream reference repository and original file |
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
* Do not vendor large upstream repositories into `references/` via copied
  trees — only register them as submodules so they remain excluded from the
  PyPI wheel and end-users never encounter large checkout trees.
  The `references/` submodules are intentionally in-repo developer references;
  they are excluded from PyPI distribution targets and end-users install from
  PyPI without ever traversing the submodule trees.
* Do not treat `references/` as a mirror — it is an index of upstream sources,
  not a vendored content store.
* Do not add `references/` content to `pyproject.toml` distribution targets —
  these files must never be packaged into the autoharness wheel or distribution.
