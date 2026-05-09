---
id: compound-016-s-community-template-registry
title: "Community Template Registry: dual-checksum design for drift detection"
problem_type: schema-design
category: autoharness-templates
root_cause: "A single checksum field cannot serve both local modification detection and upstream source drift detection because resolved artifacts differ from their source .tmpl files."
tags: [community-templates, registry, checksum, drift-detection, schema-design, verify-workspace]
created: 2026-05-09
shipment: 016-S
merge_sha: 7bcac324bbae569373d2c923e9c9aa6d166d0455
---

# Community Template Registry: dual-checksum design for drift detection

## Problem

Community templates are installed from .tmpl source files but the installed
artifact contains resolved {{VARIABLE}} content. A single checksum cannot
distinguish "user modified the installed file" from "the source .tmpl was
updated upstream" because the .tmpl and the resolved artifact always have
different content.

## Solution

Use two separate checksums in the harness manifest:

* `installed_checksum` — SHA-256 of the resolved installed artifact. Detects
  local modifications (user edited the file after installation).
* `source_checksum` — SHA-256 of the source .tmpl file at install time.
  Detects upstream updates (autoharness was updated with a new version of the
  template).

The verifier compares:
1. Installed file bytes → installed_checksum (local modification check)
2. Current .tmpl in autoharness_home → source_checksum (upstream drift check)

These two checksums are never compared to each other.

## Path Validation

Community template verification must validate that both `installed_path` and
`template_path` are relative paths without parent traversal (`..`) before
reading any bytes, to prevent reading files outside the expected roots.

## Registry Design

The registry (templates/community/registry.yaml) is a YAML catalog with
structured metadata per entry. The installer reads it to match templates
against workspace profiles. Key fields: template_id, artifact_type,
applicable_profiles, prerequisite_packs, tags, primitives_deepened.

Community templates are never auto-installed — always operator opt-in.
