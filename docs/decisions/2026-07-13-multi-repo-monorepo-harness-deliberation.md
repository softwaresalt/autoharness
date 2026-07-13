---
title: "Multi-Repo and Monorepo Harness Capability"
date: "2026-07-13"
description: "Deliberation framing for making autoharness handle workspaces that span multiple repositories or monorepo units without violating workspace containment, discovery, install, tune, and backlog traceability boundaries."
topic: "Should autoharness support per-repo harnesses, workspace-spanning discovery, a monorepo-aware profile, or a federated model for multi-repo and monorepo workspaces?"
depth: "framing"
decision_status: "proposed"
doc_type: decision
source: docs/decisions/2026-07-13-multi-repo-monorepo-harness-deliberation.md
source_stash_ids:
  - "1270EC13"
backlog_items:
  - "080-F"
linked_artifacts:
  - "schemas/workspace-profile.schema.json"
  - ".github/skills/workspace-discovery/SKILL.md"
  - ".github/skills/install-harness/SKILL.md"
  - ".github/skills/tune-harness/SKILL.md"
tags:
  - "multi-repo"
  - "monorepo"
  - "workspace-discovery"
  - "install-harness"
  - "tune-harness"
  - "operator-decision"
---

# Multi-Repo and Monorepo Harness Capability

## Status

**PROPOSED — operator architecture decision required before implementation.** This
is framing only. No external multi-repo workspace was available in this session,
and Stage is not authorized to modify schemas, templates, workspace-discovery,
install, or tune artifacts while the operator is AFK.

## Problem (stash 1270EC13)

autoharness currently frames a target as one workspace root with one generated
harness surface, one workspace profile, one manifest, and one backlog registry.
The stash asks for harness capability where the working surface spans multiple
codebases or a monorepo. That can mean at least three different product shapes:

1. A developer has several sibling repositories that must be understood together.
2. A single git repository is a monorepo with multiple packages, languages, build
   systems, or deployment units.
3. A release unit spans multiple repositories with separate git histories and CI
   systems.

These are related but not identical. The architecture decision is which shape
autoharness should support first and what containment rules apply.

## Candidate approaches

### Option A — Per-repo harnesses only

Each repository gets an independent autoharness install/tune cycle. Cross-repo
coordination is documented manually or handled by an operator-level orchestration
layer.

* **Pros:** Preserves the current global-tool/local-output contract; simplest
  containment model; each repo owns its manifest, profile, CI, and backlog state.
* **Cons:** Weak for monorepo package boundaries and cross-repo release units;
  duplicates capability-pack configuration; no first-class way to express
  dependencies between repos.

### Option B — Workspace-spanning discovery root

A parent directory becomes the discovery target, and autoharness discovers all
child repos/packages beneath it as one workspace.

* **Pros:** Natural for a local solution directory with many repos; can reason
  about cross-repo dependencies and shared tooling.
* **Cons:** High containment risk: writes could accidentally target the wrong repo;
  git state and CI semantics differ per child; P-016 single-worktree policy becomes
  harder to evaluate. This is not safe to guess while AFK.

### Option C — Monorepo-aware workspace profile

Keep one git workspace root, but add first-class `workspace_units` / packages to
the profile. Each unit can declare language, build/test gates, capabilities,
owners, paths, and deployment surfaces.

* **Pros:** Fits true monorepos without breaking the single-root containment model;
  discovery can still write one harness, but tune/install can target units.
* **Cons:** Requires schema, discovery, install, tune, verification, and policy
  changes. Does not solve multi-git-repo release units by itself.

### Option D — Federated profiles

Each repo or monorepo unit keeps its own profile/manifest, and a lightweight
federation index describes cross-unit dependencies and orchestration constraints.

* **Pros:** Separates local ownership from cross-workspace reasoning; can support
  both sibling repos and monorepo units; avoids one giant profile becoming a
  dumping ground.
* **Cons:** Most complex. Needs a new federation artifact, conflict handling,
  cross-repo read/write authorization, and explicit merge/CI semantics per member.

## Impact on core workflows

| Surface | Impact to analyze before implementation |
|---|---|
| `workspace-discovery` | Must identify repo roots, package roots, language/toolchain per unit, shared vs unit-local gates, CI ownership, capability-pack signals, and dependency edges. |
| `install-harness` | Must decide whether to generate one shared harness, per-unit overlays, or per-repo outputs. Cross-references must remain valid from each unit's perspective. |
| `tune-harness` | Must detect drift per unit and avoid overwriting unrelated unit-specific customizations. Checksums may need a unit scope. |
| Backlogit | Work items may need `workspace_unit`, `repo`, or `package` metadata so Stage/Ship can scope tasks and avoid parallel implementation across units. |
| CI/local gates | Gate commands may be unit-specific; aggregation must say which units were affected and which gates are required. |
| Capability packs | Packs such as Engram, graphtor-docs, backlogit, and agent-intercom may be enabled globally or per unit. Retrieval routing must avoid mixing stale indexes across repos. |
| P-001/P-010/P-016 policy | Multi-root support must preserve P-001 single-release-unit sequencing, P-010 Stage/Ship role boundaries, and P-016 worktree topology. Stage may plan; Ship must still operate on one approved release unit at a time. |

## Tradeoffs

* **Containment vs convenience:** A workspace-spanning root is convenient but risks
  writing outside the intended repo. A monorepo-aware profile preserves one-root
  safety but does not solve every multi-repo case.
* **One harness vs many harnesses:** One shared harness reduces duplication but can
  become too generic; per-unit harnesses stay precise but need federation.
* **Discovery depth vs install speed:** Deep cross-repo discovery can be expensive
  and may require external access or credentials.
* **Backlog traceability:** Multi-unit work needs explicit metadata or Stage/Ship
  will lose the 2-hour, width-isolated task boundaries.

## Recommendation

Start with **Option C: monorepo-aware profile** as the safest first architecture,
then evaluate **Option D: federated profiles** if the operator needs true
multi-git-repo release units. Avoid Option B as a default until the operator
ratifies containment, write authorization, P-001 release-unit sequencing, P-010
role-boundary behavior, and P-016 worktree semantics for a parent workspace root.

## Operator Decision Required

The operator must decide **which multi-repo/monorepo product shape autoharness
should support first** and what write boundary is allowed: per-repo only,
monorepo units inside one git root, parent-directory workspace-spanning discovery,
or a federated multi-profile model. Implementation is blocked until that
architecture decision is made.

## Open questions

1. Is the primary target a true monorepo in one git root, or several independent
   repositories that ship together?
2. Should generated harness artifacts live only at the root, inside each unit, or
   in both places?
3. How should backlog items record affected repo/unit/package scope?
4. Can capability packs be enabled per unit, or only for the whole workspace?
5. What is the safe default when a task affects two units with different build
   gates and owners?
6. How should P-001 define one release unit when a change touches multiple repos
   or units?
7. How should P-010 role boundaries and P-016 worktree topology detect and block
   ambiguous parallel implementation in a multi-root environment?
