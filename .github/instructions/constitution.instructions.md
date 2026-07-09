---
description: "Constitutional principles governing all agent operations in this workspace — adapted for Python"
applyTo: '**'
---

# Constitution

Condensed self-install constitution for the autoharness dogfood harness. This is
the authoritative principle set referenced by `harness-architecture.instructions.md`
(Primitive 5). The full generative template lives at
`templates/foundation/constitution.instructions.md.tmpl`; policy sequencing detail
lives in `templates/policies/workflow-policies.md`.

## Core Principles

### I. Safety-First Python

Production code MUST be written in Python. Prefer the standard library and existing
project dependencies. Explicit error handling is required; silent failures are
forbidden.

**Rationale**: Explicit safety enforcement prevents data corruption and state loss
during unattended agent operation.

### II. Test-First Development (NON-NEGOTIABLE)

Every feature or chore MUST have tests written before implementation code. Tests in
`tests/` MUST pass before any code is merged. Steps: write test, confirm it fails
(red), implement, confirm it passes (green).

### III. Workspace Isolation and Security Boundaries

All file-system operations MUST resolve within the configured workspace root. Path
traversal attempts MUST be rejected. No secrets or credentials MUST appear in
committed files.

### IV. CLI Workspace Containment (NON-NEGOTIABLE)

In CLI mode, an agent MUST NOT create, modify, or delete any file or directory
outside the current working directory tree. Paths that resolve above or outside the
cwd — via absolute paths, `..` traversal, symlinks, or env-var expansion — MUST be
refused. The only exception is reading files explicitly provided as context.

### V. Structured Observability

All significant operations MUST produce traceable output through broadcasting,
commit messages, or structured reporting: build/test execution, file modifications,
quality-gate results, and error conditions.

### VI. Single Responsibility

New dependencies MUST be justified by a concrete requirement. Do not add libraries
speculatively. Optional capabilities SHOULD use feature flags or conditional
configuration.

### VII. Destructive Command Approval (NON-NEGOTIABLE)

All destructive terminal commands MUST require operator approval before execution,
regardless of permissive agent modes. Destructive = deletes/overwrites files,
modifies system config, alters version-control history, drops/truncates data,
installs/removes system packages, or executes untrusted code.

### VIII. Explicit Safety Modes for Elevated Risk

When work involves destructive commands, production-impacting changes, uncertain
root causes, or large blast radius, agents MUST switch into an explicit safety mode:
**careful** (enumerate risks, confirm intent), **freeze-scope** (constrain to a
declared boundary), or **investigate-first** (evidence before fixes).

### IX. Git-Friendly Persistence

Harness-managed workspace state MUST be serializable to human-readable,
Git-mergeable files. Markdown with YAML frontmatter is preferred. Writes SHOULD be
atomic and minimize merge conflicts through stable ordering.

### X. Agent Context Efficiency

Tools and data access MUST preserve agent context by returning minimal, targeted
data. When a structured query can replace directory scanning or bulk file reading,
agents MUST prefer the query.

### XI. Merge Commit History Preservation (NON-NEGOTIABLE)

All pull request merges MUST use merge commits. Squash merge and rebase merge are
expressly forbidden. The ship agent MUST verify the merge strategy before executing
any merge and MUST halt with a P-009 violation if squash or rebase merge is
detected.

## Capability Overlays

* **agent-intercom** — agents MUST use the configured intercom workflow for
  heartbeat, milestone broadcasting, destructive-operation approval routing, and
  operator steering waits. If intercom is unavailable, warn that remote visibility
  is degraded and do not silently bypass approval steps.
* **agent-engram** — agents MUST prefer engram MCP tools over file-based search for
  context discovery, verify/refresh stale index state before trusting results, and
  not hand-edit `.engram/` artifacts as a substitute for lifecycle or sync.
* **backlogit** — agents MUST use the configured backlogit workflow for queue
  selection, dependency management, token-efficient lookup, and traceability, and
  MUST refresh the index after out-of-band edits before trusting query output.

## Technical Constraints

| Concern | Constraint |
|---|---|
| Language | Python |
| Build | `pip install -e .` |
| Test | `pytest` (suite under `tests/`) |
| CI | GitHub Actions |
| Backlog | `.backlogit/` (backlogit) |

## Quality Gates

Run in order. Do not skip any gate.

```text
# Gate 1 — YAML frontmatter validity across all .tmpl and .md files
# Gate 2 — Markdown structure (heading hierarchy MD001/MD025/MD041, code fences, tables)
# Gate 3 — Variable completeness: no {{VARIABLE}} placeholders remain in installed output
# Gate 4 — Cross-reference integrity: all referenced files, skills, agents exist
```

## Governance

This constitution supersedes other development practices in this workspace. All
reviews and automated checks MUST verify compliance.

| Level | Meaning |
|---|---|
| **NON-NEGOTIABLE** | Agent MUST comply. Violations trigger P-005 telemetry and halt. |
| **MUST** | Agent MUST comply. Violations are flagged; self-correction expected. |
| **SHOULD** | Recommended. Deviations acceptable with documented rationale. |
| **MAY** | Optional at agent discretion. |

For NON-NEGOTIABLE principles without runtime enforcement, agents that observe
violations MUST broadcast a P-005 event and halt rather than proceed. Amendments to
this constitution require a version bump, rationale, and sync impact report.

**Version**: 1.0.0 | **Generated by**: autoharness
