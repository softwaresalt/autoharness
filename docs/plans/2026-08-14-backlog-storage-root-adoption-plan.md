---
title: "Implementation Plan — Adopt the backlogit `.backlog` storage root across the autoharness product surface"
date: "2026-08-14"
description: "Autoharness-side follower plan for backlogit 1.9.0's new .backlog storage root. Makes the product surface directory-agnostic with .backlog-first precedence, mirrors upstream both-exist fail-closed detection, and defaults new installs to .backlog. Explicitly excludes migrating this repository's own .backlogit directory, which stays an operator-gated action outside dark-mode automation."
doc_type: plan
source: docs/plans/2026-08-14-backlog-storage-root-adoption-plan.md
plan_id: "PLAN-BACKLOG-ROOT"
stash_ids: ["BED0DDED"]
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - ".backlogit/queue/018-DL.md"
  - "docs/plans/2026-08-14-backlog-storage-root-adoption-hardening.md"
  - "docs/reviews/2026-08-14-backlog-storage-root-adoption-review.md"
  - "docs/decisions/2026-08-07-backlogit-directory-rename-feasibility-deliberation.md"
---

# Implementation Plan — Adopt the backlogit `.backlog` storage root

## 1. Why this is now actionable

Stash `BED0DDED` was deferred twice (2026-08-07, 2026-08-09) as EXTERNAL-BLOCKED.
The recorded unblocker was: *"a backlogit release making the storage root
configurable with a .backlog default plus discovery precedence, migration, and
both-exist safe detection; only then does autoharness follow."*

That release has landed. Verified READ-ONLY against `C:\Source\GitHub\backlogit`
at **v1.9.0 / HEAD 39528a41** (repository NOT mutated):

| Unblocker element | Upstream evidence (v1.9.0) |
|---|---|
| `.backlog` default | `init` creates the `.backlog` storage root |
| Discovery precedence | `workspaceRootCandidates = [".backlog", ".backlogit"]` (`internal/core/workspace.go:25`) |
| Explicit override | `BACKLOGIT_WORKSPACE_DIR` (`workspace.go:27`, validated in `validateWorkspaceDirOverride`) |
| Legacy support | `ResolveStorageRoot` falls back to `.backlogit`; `WorkspaceStorageRoot` retains the legacy default |
| Both-exist safe detection | `ResolveStorageRoot` returns `AmbiguousWorkspaceRootError` when both roots match (`workspace.go:310-316`) — fails closed, never picks one |
| Migration | `backlogit migrate --workspace-dir` with `--dry-run` and `--rollback` (`internal/core/migrate_workspace_dir.go`) |
| Upstream regression cover | `workspace_dualroot_test.go`, `workspace_root_conflict_test.go`, `workspace_literal_guard_test.go`, `migrate_workspace_dir_test.go` |

The silent backlog-state **SPLIT** hazard that justified both prior deferrals is
therefore gone: the engine itself now resolves either root and refuses to guess
when both are present.

## 2. Scope

### In scope — the autoharness FOLLOWER surface

A read-only inventory found ~29 hardcoded `.backlogit` references plus the
registry default:

* **Schemas (3)** — `schemas/backlog-tool-registry.schema.json:25`,
  `schemas/harness-config.schema.json:111`, `schemas/workspace-profile.schema.json:224`
* **Templates (4)** — `templates/ci/ci-topology-check.sh.tmpl` (2),
  `templates/ci/ci.yml.tmpl`, `templates/instructions/backlogit.instructions.md.tmpl` (2)
* **Installed harness surface (7)** — `.github/instructions/backlogit.instructions.md` (2),
  `.github/instructions/constitution.instructions.md:114`,
  `.github/agents/_orchestrator.agent.md` (2), `.github/agents/_ship.agent.md` (2),
  `.github/agents/_stage.agent.md:95`, `.github/agents/auto-mergeinstall.agent.md:84`
  (already dual-root aware — use as the reference pattern)
* **Scripts (1)** — `scripts/ci-topology-check.sh` (2)
* **CLI (1)** — `src/autoharness/cli.py:467` help text
* **Docs (13)** — `docs/backlog-integration.md`, `docs/backlogit-operating-model.md`,
  `docs/dag-readiness-gate.md`, `docs/gates-reference.md`,
  `docs/pipeline-topology-gate.md`, `docs/pipeline-topology-gate-ci-rollout.md`,
  `docs/primitives.md`, `docs/size-complexity-reference.md`
* **Registry** — `.autoharness/backlog-registry.yaml` `directory:` field

### Explicitly OUT of scope (NON-NEGOTIABLE)

1. **Migrating this repository's own `.backlogit` directory.** That is a separate,
   operator-invoked action (`backlogit migrate --workspace-dir`). It MUST NOT be
   performed by any task in this plan, MUST NOT be added to any shipment in this
   chain, and MUST NOT run under dark-mode automation. Renaming the live storage
   root while the pipeline is reading and writing it has no safe mid-run recovery.
2. **Changing `.autoharness/backlog-registry.yaml`'s `directory:` value for THIS
   repository.** The registry describes the workspace as it actually is. Flipping
   it ahead of the physical directory would make the registry lie.
3. **Any change to `C:\Source\GitHub\backlogit`.** External, read-only.
4. **Auto-running migration from tune-harness.** Detect and report only.

## 3. Approach — treat the root as resolved data, not a literal

Chosen direction from `018-DL` (Option 3, directory-agnostic follower):

**T1 — Inventory + resolver contract.** Produce the authoritative inventory of
every autoharness read/write of the storage root and classify each as
*resolver-routable* or *literal-required* (e.g. prose examples). This gates the
schema change: no literal may be flipped before it is classified.

**T2 — Shared resolution helper.** Add one helper in `src/autoharness` that
mirrors upstream precedence **exactly**: `BACKLOGIT_WORKSPACE_DIR` -> `.backlog`
-> `.backlogit`, returning a fail-closed ambiguity error when both roots exist.
Divergence from upstream precedence is the primary correctness risk, so the
helper's ordering is asserted against the upstream table in tests.

**T3 — Schema acceptance.** Update the three schemas to accept and prefer
`.backlog` while continuing to validate legacy `.backlogit` values. Follows
`docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`:
a changed validation contract needs a versioned identifier and a preserved legacy
interpretation — no in-place semantic mutation without a version bump.

**T4 — Template + instruction family.** Update the template and instruction
families so generated workspaces stop asserting a single hardcoded root and name
`.backlog` as the default for new installs. `auto-mergeinstall.agent.md:84`
already says "`.backlog/` or `.backlogit/` — detected backlog directory" and is
the reference wording.

**T5 — CI topology scripts.** `scripts/ci-topology-check.sh` and its template
resolve the root instead of hardcoding it, preserving the repo-root-relative read.

**T6 — Tune drift rule (detect-and-report only).** tune-harness gains a rule that
flags a legacy-rooted target workspace and points the operator at
`backlogit migrate --workspace-dir --dry-run`. It never performs the rename.

**T7 — Docs.** Update the 13 doc references to the dual-root reality and document
the operator-gated migration procedure, including the both-exist failure mode.

## 4. Sequencing

`T1 -> T2 -> {T3, T5} -> T4 -> T6 -> T7`. T1 gates everything (no flip before
classification). T2 gates T3/T5 (consumers need the resolver first). T7 last so
docs describe shipped behavior.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Resolver diverges from upstream precedence | T2 asserts ordering against the upstream candidate table; any divergence is a P0 |
| A literal flip lands before classification | T1 gates T3; hardening H1 |
| Both-exist state reached mid-run | Mirror upstream fail-closed `AmbiguousWorkspaceRootError`; never auto-pick |
| Scope creep into the live repo rename | Out-of-scope item 1 is restated in every task's acceptance criteria |
| Registry desynchronised from reality | Out-of-scope item 2; registry stays `.backlogit` until the operator migrates |

## 6. Plan Hardening conclusion

**Requires plan hardening: yes.** Reason: elevated blast radius — the change
spans JSON schemas, the CLI, multiple template families and CI scripts
simultaneously, and it touches the resolution of the backlog storage root, which
is the substrate every agent in the pipeline depends on. A wrong precedence order
or a premature literal flip could split backlog state across two directories.
