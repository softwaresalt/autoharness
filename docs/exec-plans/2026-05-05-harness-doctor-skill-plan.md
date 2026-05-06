# Installation Health-Check Skill — Implementation Plan

**Date**: 2026-05-05
**Source stash entries**: `64D3E4BD` (atv-doctor pattern)
**Covering feature**: Harness Health-Check Skill
**Risk level**: Low — additive skill template only
**Requires plan hardening**: no

---

## Objective

Add a `harness-doctor` skill template that provides on-demand installation
health diagnostics for harness artifacts. This complements the existing
tune-harness drift detection with a user-invocable, graded health report.

## Source Material

- `atv-starterkit/pkg/scaffold/templates/skills/atv-doctor/SKILL.md`

---

## Task 1: Create harness-doctor skill template

**Files**: `templates/skills/harness-doctor/SKILL.md.tmpl` (new)
**Scope**: Create a health-check skill that performs:

- Phase 1: Detect install scope (harness manifest presence, artifact directories)
- Phase 2: Version check (installed harness version vs autoharness_home version)
- Phase 3: File integrity (manifest checksum verification)
- Phase 4: Cross-reference validation (all referenced files exist)
- Phase 5: MCP prerequisite check (verify declared tools are available)
- Phase 6: Template variable residue check (no unresolved `{{...}}`)
- Phase 7: Graded report output

Design requirements:

- Mode: `report` (default) or `fix` (attempt auto-repair for missing files)
- Uses `{{HARNESS_MANIFEST_PATH}}` for manifest location
- Uses `{{AUTOHARNESS_VERSION}}` for version comparison
- Reports per-category health grade (A-F)
- Aligns with existing stash item `13A43DDA` (MCP tool pre-flight checks)
- Environment-agnostic

**Acceptance**: Template produces coherent health-check workflow. Valid YAML
frontmatter. No unresolved variables in output.

## Task 2: Register harness-doctor variables in install-harness

**Files**: `.github/skills/install-harness/SKILL.md` (modify)
**Scope**: Add variables:

- `{{HARNESS_MANIFEST_PATH}}` — default: `.autoharness/harness-manifest.yaml`
- `{{AUTOHARNESS_VERSION}}` — resolved from autoharness_home metadata

**Acceptance**: Variables in resolution table.

---

## Dependency Graph

```
Task 1 (harness-doctor) → Task 2 (register variables)
```
