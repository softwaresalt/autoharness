---
problem_type: schema_field_confusion
category: harness_manifest
root_cause: The harness manifest has two distinct fields named similarly — `artifacts` (the installed-file list) and `entries_added` (a VS Code settings sub-field) — which are easy to conflate.
tags: [harness-manifest, schema, artifacts, entries-added, vscode-settings]
shipment: 008-S
date: 2026-05-06
---

# Harness Manifest: `artifacts` vs `entries_added`

## Problem

When authoring harness-doctor or any skill that inspects the harness manifest
(`harness-manifest.yaml`), it is tempting to reference `entries_added` as the
field that lists installed artifact paths. This is wrong.

## Root Cause

The manifest schema (`schemas/harness-manifest.schema.json`) defines:

* **`artifacts`** — top-level array at line 95. Each entry has shape:
  `{path, checksum, primitive, template, artifact_type}`. This is the canonical
  list of every file the installer placed in the workspace.

* **`entries_added`** — nested field at line 155, inside `vscode_settings`.
  It records which VS Code settings keys were added during install (e.g.,
  `chat.agentFilesLocations`). Scope is VS Code config only.

Using `entries_added` to enumerate installed harness files will silently return
nothing useful; the correct field is `artifacts[*].path`.

## Fix

In any skill or template that reads the manifest:

```yaml
# Correct — iterate installed artifact paths
artifacts:
  - path: .github/agents/stage.agent.md
    checksum: ...
    primitive: "4"
    template: agents/stage.agent.md.tmpl
    artifact_type: agent

# Wrong — this only covers VS Code settings additions
vscode_settings:
  entries_added:
    - chat.agentFilesLocations
```

In harness-doctor Phase 1, use:
```
manifest.artifacts[*].path
```
not `manifest.entries_added` or `manifest.vscode_settings.entries_added`.

## Verification

`schemas/harness-manifest.schema.json` lines 95–126 define `artifacts`;
lines 155–159 define `vscode_settings.entries_added`.
