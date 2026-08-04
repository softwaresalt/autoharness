---
title: "Size + Complexity validation checklist"
description: "Reviewer checklist asserting size and complexity enum validation, provenance-completeness, and non-conflation across Stage decomposition surfaces."
ms.date: 2026-08-03
ms.topic: reference
keywords:
  - autoharness
  - backlogit
  - size
  - complexity
  - non-conflation
  - stage
  - harvest
---

> **Navigation**: [README](../README.md) · [Size + Complexity Reference](size-complexity-reference.md) · [Telemetry Reference](telemetry-reference.md) · [Gates Reference](gates-reference.md)

## Overview

Use this checklist when reviewing changes to Stage decomposition surfaces
(`templates/agents/_stage.agent.md.tmpl`, the installed
`.github/agents/_stage.agent.md`, and `templates/skills/harvest/SKILL.md.tmpl`)
that touch task-level `size` or `complexity` metadata. It exists to catch
regressions of the non-conflation contract defined in
[`docs/size-complexity-reference.md`](size-complexity-reference.md) — a
degraded, checklist-only fixture per plan advisory P2-c, since this workspace
has no in-repo fixture harness for markdown-authored planning-metadata
assertions and this task does not introduce one.

## Checklist

- [ ] **Both enums are validated before write.** `size` is restricted to
  `XS|S|M|L|XL` and `complexity` to `trivial|low|medium|high`. Invalid values
  are rejected fail-closed (halt), never silently coerced, truncated, or
  defaulted.
- [ ] **Size provenance-completeness is enforced.** A non-empty `size_source`
  never appears without a non-empty `size_ruleset_version` (and vice versa).
  Stage-authored tasks use `size_source: agent` and
  `size_ruleset_version: ah-stage-sizing-v1`.
- [ ] **No single scalar combines the two axes.** `size` and `complexity` are
  two structurally distinct fields. No document, template, or skill derives
  one axis from the other, averages them, or folds them into one combined
  label/score.
- [ ] **The two-axis 2-hour/granularity gate is applied independently.** A
  `size` estimate implying more than 2 hours of human-equivalent effort forces
  a split regardless of `complexity`. A `complexity: high` task forces a split
  or de-risking step (spike, further decomposition, or additional
  deliberation) regardless of `size`.
- [ ] **Cross-reference integrity.** Every file referenced by the touched
  surfaces exists in the repository:
  - `docs/size-complexity-reference.md` (this checklist's companion doc)
  - `templates/agents/_stage.agent.md.tmpl`
  - `.github/agents/_stage.agent.md`
  - `templates/skills/harvest/SKILL.md.tmpl`
  - `.autoharness/harness-manifest.yaml` (checksum entry for the installed
    dogfood agent)
- [ ] **Dogfood mirror parity.** When the change is behavioral (affects what
  Stage does, not just prose formatting), the same behavioral requirement is
  present in both `templates/agents/_stage.agent.md.tmpl` and the installed
  `.github/agents/_stage.agent.md`, and the `.autoharness/harness-manifest.yaml`
  checksum for the installed copy matches the file's current SHA-256.
- [ ] **YAML frontmatter and variable completeness.** Frontmatter in every
  touched `.md`/`.md.tmpl` file parses; no unresolved `{{...}}` placeholders
  remain in installed (non-template) output.

## Non-conflation regression examples (do not do this)

- Defining a single `effort_risk` field that blends size and complexity.
- Deriving `complexity: high` automatically whenever `size: XL` (or the
  reverse) instead of requiring an independent judgment call.
- Skipping the granularity/split check for a `complexity: high` task because
  its `size` is `XS` or `S`.
- Recording `size_source` without `size_ruleset_version` (or the reverse).

## Cross-references

- [`docs/size-complexity-reference.md`](size-complexity-reference.md) — the
  authoritative semantics, enum tables, two-axis gate, and provenance rule.
- [`templates/skills/harvest/SKILL.md.tmpl`](../templates/skills/harvest/SKILL.md.tmpl)
  — emits size + complexity on every harvested work item.
- [`templates/agents/_stage.agent.md.tmpl`](../templates/agents/_stage.agent.md.tmpl)
  and [`.github/agents/_stage.agent.md`](../.github/agents/_stage.agent.md) —
  mandate size + complexity at task-creation time.
