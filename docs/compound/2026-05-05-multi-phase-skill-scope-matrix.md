---
problem_type: template-authoring
category: skill-design
root_cause: scope-matrix-phase-gating
tags: [skill, scope, phase-gating, security-audit, multi-phase]
created: 2026-05-05
shipment: 006-S
---

# Multi-Phase Skill Scope Matrix Design

## Problem

When a skill has multiple phases (e.g., Discovery → Config → OWASP → STRIDE → Score → Output → Persist), authors tend to gate phases with a single top-level condition such as "skip unless `scope:full`". This silently breaks `scope:<path>` and topic-scoped invocations: the agent runs Phase 1 discovery then stops, producing no useful output.

## Root Cause

The scope matrix was defined as a table (scope values → phase columns), but the phase skip conditions in the workflow text were not kept in sync with the matrix. The skip condition on Phase 1 accidentally excluded it when a non-`full` scope was passed.

## Solution

**Phase 1 (Discovery) always runs.** Its behavior adapts to the scope:

| Scope | Phase 1 narrows to |
|---|---|
| `scope:full` | All surfaces |
| `scope:config` | Agentic config surfaces only |
| `scope:owasp` or `scope:stride` | Application source entry points only |
| `scope:<path>` | Files under the specified path only |

Each subsequent phase carries its own explicit skip condition referencing the scope matrix. Example:

```
### Phase 2: Config Tier 1

**Skip condition**: Skip unless `scope:full` or `scope:config` or `scope:<path>` where the path intersects config surfaces.
```

## Rule

> In multi-phase skill templates with a scope matrix, every phase (including Phase 1) must carry an explicit skip condition. Phase 1 must always run. Never use a single top-level gate for all phases.

## Applied In

- `templates/skills/security-audit/SKILL.md.tmpl`
