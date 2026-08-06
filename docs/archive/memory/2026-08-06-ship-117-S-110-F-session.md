---
type: operational-closure
shipment: 117-S
feature: 110-F
tasks:
  - 110.001-T
  - 110.003-T
  - 110.002-T
title: "Operational Closure — read-only DAG readiness/critical-path reporting (110-F)"
status: READY
feature_pr: 305
feature_merge_commit: 24b488f675de0f2d0af13e5ee4c18a1b969de8c9
reviewed_head: df847fcde11e1b4374ba1f2f5e9fa97faaf09221
closed_at: 2026-08-06T17:53:28Z
stash_preserved: preserve-unrelated-before-117-S-pipeline
next_cursor: 118-S
doc_type: memory
source: docs/memory/117-S-closure.md
tags:
  - p-017
  - dark-factory
  - dag-readiness
  - topology-gate
  - copilot-review
  - p-018
  - p-015
  - ci-infra-flake
  - closure
---

# Operational Closure — 117-S

## Shipment

Task-only shipment covering feature **110-F**: Phase 1 of the deferred
DAG-visibility follow-up from spike `001-SP` (stash `33CC445C`). Adds a
READ-ONLY reporting command (`autoharness gate dag-readiness [--json]`)
surfacing the ready-set (live `queued` shipments only, every predecessor
genuinely terminal-closed `shipped`/`done`; `queued`/`active` predecessors
block; `abandoned`/malformed/unknown predecessors fail closed), the critical
path (longest chain via topological order + DP), and full downstream
transitive dependents — over backlogit's existing shipment-blocks DAG
already read by the pipeline-topology gate. No scheduler, no mutation, no
parallelism; P-001/P-016 single-active semantics unaffected. Executed under
an operator-approved bounded P-017 dark-factory contract (merge + admin
fallback pre-approved, scope strictly 117-S — first of serial chain
117-S → 118-S → 119-S; 118-S was **not** claimed).

## What shipped

Feature PR **#305** → merged to `main` as merge commit
`24b488f675de0f2d0af13e5ee4c18a1b969de8c9` (**P-009 merge-commit satisfied**;
repo `allow_merge_commit=true`, `allow_squash_merge=false`,
`allow_rebase_merge=false`; merge commit verified with 2 parents). Reviewed
HEAD at merge: `df847fcde11e1b4374ba1f2f5e9fa97faaf09221`.

- **110.001-T** — `src/autoharness/gates/topology.py`: `DagReadinessResult`
  dataclass + `compute_dag_readiness()` and helpers (`_dag_successors`,
  `_dag_detect_cycle` — cycle detection owned entirely by the new analyzer,
  not the reused reader — `_dag_all_predecessors_finished`,
  `_dag_longest_chain`, `_dag_downstream_dependents`). Reuses
  `ShipmentState`/`FilesystemTopologyReaders`/`_is_shipped_terminal`/
  `_has_ambiguous_shipment_records`/`_normalized_live_status` from the
  existing pipeline-topology reader (109-F). 23 unit tests
  (`tests/test_gates_dag_readiness.py`).
- **110.003-T** — `src/autoharness/cli.py`: new `autoharness gate
  dag-readiness [--workspace <path>] [--json]` subcommand, existence-guarded
  (empty → `status: "empty"`, exit 0) and DEGRADED-non-fatal on
  `BacklogUnavailableError`. 10 unit tests
  (`tests/test_gate_dag_readiness_cli.py`).
- **110.002-T** — `docs/dag-readiness-gate.md` reference doc + cross-refs
  from `docs/gates-reference.md` and `docs/pipeline-topology-gate.md`.

## Local review (code-review task agent, 2 rounds)

- **Round 1**: one legitimate P1 — ready-set/predecessor-finished logic
  failed open on shipments with ambiguous/duplicated live+archive
  provenance (the sibling pipeline-topology gate already fails closed on
  this via `_has_ambiguous_shipment_records`, but the new analyzer never
  checked it). Fixed in `3fe6fac` (added the ambiguity check to both the
  predecessor-role and candidate's-own-role call sites, corrected an
  inaccurate docstring, +2 regression tests).
- **Round 2**: verdict **READY**, zero P0/P1. One non-blocking P2
  (longest-chain tie-break determinism relies on implicit traversal order)
  — addressed immediately with a clarifying code comment in `df847fc`.

## CI (infra flakes, no code remediation needed)

The initial CI run (`31119082435`) hit a genuine GitHub Actions
infrastructure degradation — `Failed to resolve action download info` /
`Service Unavailable` while fetching pinned actions — across **both** the
`detect code changes` and `pipeline-topology (ambient)` jobs, and separately
caused the auto-triggered "Running Copilot Code Review" workflow to fail
before producing a real review (see Copilot section below). This was not a
code/test failure. Rerunning the failed jobs (`gh run rerun --failed`,
escalating to a full `gh run rerun` after the run settled) eventually
produced a clean pass once the underlying GitHub-side action-resolution
degradation cleared: `detect code changes`, `test`, `pipeline-topology
(ambient)`, `ci gate` all **pass** on run `31119082435`'s final attempt.

## Copilot review (P-018)

The auto-triggered Copilot review errored due to the same infra
degradation and posted `state: COMMENTED` with body "Copilot encountered an
error and was unable to review this pull request... re-request a review" —
**zero inline review threads** were created. Per the documented completion
signal (any Copilot-authored review with `state != PENDING` counts as
complete) and zero unresolved threads, `autoharness gate copilot-review 305`
returned **SATISFIED** both when first checked and again immediately before
merge (HEAD unchanged at `df847fc`). No repository-approved re-request
wrapper is configured (no MCP `mcp_github_request_copilot_review` tool in
this session, and `gh pr edit --add-reviewer` is explicitly disclaimed as an
unreliable fallback per
`.github/instructions/github-pr-automation.instructions.md`), so per
protocol this was recorded as-is rather than forced. **Zero Copilot inline
comments existed, so the "fix/commit/push/reply/resolve each" requirement
was vacuously satisfied** — there was nothing to fix or resolve.

## Verification

- Full suite (`tests/`): 1294 passed, 11 skipped, 403 subtests (final
  pre-PR run). Pre-existing unrelated collection errors under `references/`
  are out of scope (not caused by this work).
- Full local build: `uv pip install -e . --offline` succeeded (cached deps;
  this sandboxed workspace has no live PyPI reachability — `uv pip install
  -e .` alone fails with `HandshakeFailure`). Post-build smoke:
  `uv run autoharness --help` and `uv run autoharness gate dag-readiness`.
- §1.9 readiness gate: all 5 checks passed for HEAD `df847fc` (Local Review
  Readiness block present, outcome `READY`, P0=0/P1=0, full local build
  evidence, no unresolved follow-ups).
- P-018 copilot-review gate: `SATISFIED` at HEAD `df847fc` (checked twice —
  once before presenting for merge, once immediately before the merge
  command, unconditionally per protocol).

## Releasability

**READY.** Operator-approved (P-017 bounded dark-factory contract, scope
strictly 117-S) merge completed as merge commit `24b488f6` (P-009). No
blocking findings (P0=0, P1=0). No runtime-surface or rollout-sensitive
behavior touched (read-only reporting gate; `runtime-verification` /
validator handoff not applicable).

## Backlog closure (P-015 single-artifact ops)

Task-only shipment — manifest `custom_fields.items` = `110.001-T,
110.003-T, 110.002-T` ONLY. Protected set = covering feature **110-F**
(no sibling tasks outside the manifest — 110-F is genuinely fully covered
by this shipment, confirmed no other `110.*` children exist).

- Pre-mode: all 3 manifest tasks found already physically relocated to
  `.backlogit/archive/` (task-loop `move --status done` side effect);
  shipment record `status: active` → `record-consistent`; no orphans →
  `recommendation: PROCEED`.
- **Pre-flight status-field check (per
  `docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md`,
  5th recorded occurrence)**: grepped the `status:` field of all 3
  "pre-archived-looking" task files **before** accepting the skip
  classification — all 3 showed `status: done`, **not** `status: archived`.
  Explicitly ran `backlogit archive <id>` for each of `110.001-T`,
  `110.002-T`, `110.003-T`; verified `status: archived` +
  `archived_status: done` afterward. This is the fifth recorded occurrence
  of the same gap across shipments 111-S/112-S/113-S/117-S (112-S caught it
  proactively too; 111-S/113-S needed an external/adjacent trigger) — logged
  as a reinforcing entry in the compound doc; the scripted hard-check
  hardening follow-up from 111-S/112-S remains open.
- `117-S` shipment record: `backlogit move --status shipped` → verified live
  `status: shipped` → `backlogit archive` → verified `archived_status:
  shipped`. **Never** `backlogit shipment ship` (cascade would requeue/detach
  and is P-015-forbidden).
- Protected-set re-verify after each step: `110-F` remained in
  `.backlogit/queue/` throughout (git status clean baseline, no
  unintended `archive/` additions) until its own deliberate closure below.
- **Feature 110-F explicit closure** (fully covered by 117-S, a deliberate
  step beyond the default protected-set-untouched safe-close outcome):
  `backlogit move 110-F --status done` → verified `status: done` →
  `backlogit archive 110-F` → verified `archived_status: done`.
- Backlog index resynced (`backlogit sync` → 725 artifacts indexed).
- Named stash `preserve-unrelated-before-117-S-pipeline` confirmed present
  and untouched (`git stash list` → `stash@{0}`) throughout the entire
  session; never popped or dropped.

## Compound learning

Reinforced (5th occurrence) in
`docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md`: a
manifest task physically relocated to `.backlogit/archive/` by
`move --status done` still shows `status: done`, not `status: archived`,
until `backlogit archive <id>` is explicitly run — file location is not
proof of archive-provenance. The recurring hardening follow-up (a scripted,
unconditional pre-flight `status:` check in the Step 5 Closure Tasks
procedure / `shipment-reconcile` safe-close classification, rather than
relying on an agent re-reading the compound doc) remains open.

## Next cursor

**118-S** — next in the serial chain 117-S → 118-S → 119-S. **Not claimed**
this session per the explicit scope constraint.

## Follow-ups

None new. No P-001/P-007/P-009/P-011/P-015/P-016/P-018 issues outstanding.
The open cross-shipment hardening item (scripted pre-flight archive-status
check) is tracked narratively in the compound doc, not as a new backlog
item — Ship's role boundary does not permit creating backlog items.
