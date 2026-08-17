---
title: Backlogit self-migration plan hardening
description: P-006 hardening pass over the self-migration plan; adversarial guards for a live workspace-state migration
doc_type: plan
source: docs/plans/2026-08-17-backlogit-self-migration-hardening.md
status: hardened
date: 2026-08-17
stash_source: BED0DDED
plan: docs/plans/2026-08-17-backlogit-self-migration-plan.md
route: claude-opus-5/anthropic/high
---

# Backlogit self-migration plan hardening (P-006)

Hardening is **required**: this plan mutates live workspace state that every
agent depends on, renames 1613 git-tracked files, and edits checksum-governed
configuration. Blast radius is repository-wide and includes an availability
failure mode.

## H1 — The idle gate is a hard precondition, not advice

`T004` MUST verify: exactly one worktree, no `backlogit.exe` process, zero
active checkpoints, and no active shipment other than this one. Any failure
**halts the shipment** — it does not downgrade to a warning. The migration is
authorized only in normal sequential mode with the operator present.

Rationale: the entire safety argument rests on there being no concurrent
writer. If that premise is unverified, nothing else in this plan holds.

## H2 — Process locks are a blocking precondition (empirically proven)

Three `backlogit.exe` processes currently hold **exclusive** Windows handles on
`backlogit.db`, `-wal` and `-shm` (verified by `FileShare.None` probe). A
directory rename cannot succeed against an open handle on Windows.

`T005` MUST stop every such process by explicit PID and MUST re-prove release
by re-running the exclusive-open probe **successfully** before `T006` runs.
A `Get-Process` check alone is insufficient — it does not prove handle release,
which the OS completes asynchronously after process exit. Allow a bounded
retry (e.g. 5 attempts, 2 s apart) and **halt** if the probe still fails.

The dry-run in `T005` itself opens the workspace in a fresh process. The
exclusive-open probe MUST therefore be re-run **after** the dry-run and
immediately **before** `T006`, not only after the process stop.

## H3 — Superset-before-switch ordering invariant

Commit A MUST land before Commit B, and Commit A MUST be a **superset**
(covering both roots), never a switch. At no point may the repository be in a
state where `.gitignore` or the CI path filter names a root that differs from
the directory on disk.

This is what makes a single PR safe. Violating the ordering re-introduces the
14 MB database-leak hazard (**E3**).

## H4 — The backup MUST live outside the repository working tree

`T004`'s backup MUST be written outside the repo (e.g. under `$env:TEMP`). An
in-tree backup — including under `docs/`, `.autoharness/` or any dotted path —
is **forbidden**: it risks creating a second discoverable storage root,
committing 14 MB of binary state, or both.

The backup MUST be verified by file count against the source inventory before
`T005` proceeds. An unverified backup is not a rollback capability.

## H5 — Narrowing (not overriding) the 2026-08-14 H5 exclusion

The prior hardening `H5` excluded this migration from **automation**, on the
stated rationale that the Orchestrator, Stage and Ship are *"concurrently
reading and writing during a dark-factory run."*

That exclusion **remains fully in force** for dark-factory runs, unattended
automation, and any run with concurrent agents. It is narrowed here only for
the explicitly gated case: normal sequential mode, single worktree, zero active
shipments/checkpoints, operator present and directing, all H1 checks passing.

No agent may infer from this narrowing that the migration is generally
automatable. If the H1 gate cannot be satisfied, the original exclusion applies
unchanged.

## H6 — Post-migration ref-transition prohibition (residue hazard)

Once the Commit B rename exists, checking out any **pre-migration** ref leaves
`.backlog/` on disk containing ignored database residue while restoring
`.backlogit/` — producing a dual-root state that fails closed in
`src/autoharness/backlog_root.py` and `scripts/ci-topology-check.sh` (both test
bare directory existence).

Therefore, after Commit B:

* No `git checkout`, `git switch`, `git stash`, or worktree operation that
  lands on a pre-migration ref.
* To sync `main` after merge, use `git fetch origin` then
  `git checkout -B main origin/main` — **never** `git checkout main` followed
  by a pull, which transits stale pre-migration `main`.
* If residue occurs: set `BACKLOGIT_WORKSPACE_DIR` to restore tooling
  immediately, then delete the residual root only after confirming which root
  holds the authoritative `config.yaml`.

## H7 — MCP-only operations must be scheduled around the outage window

Between `T005` (stop) and `T009` (restart), no backlogit MCP tool is available.
The registry declares CLI fallbacks for `move`, `shipment claim/ship/get/list`,
`sync`, `dep`, `checkpoint`, `query`, `search` and `track_commit`, but **not**
for `add_to_shipment`, `append_comment`, `save_memory`, `create_checkpoint`,
`archive_item`, or hook poll/ack.

Consequences, binding on Ship:

* Stage completes **all** shipment assembly before handoff, so Ship never needs
  `add_to_shipment` during the outage.
* Ship MUST take its resumption checkpoint **before** `T005`.
* Ship MUST NOT attempt `ship_shipment`/archive/closure during the outage;
  closure occurs after `T009` restores MCP, or in a fresh post-merge session.

## H8 — Historical record is immutable

Approximately 150 of the 188 files referencing `.backlogit` are historical:
`docs/archive/`, `docs/memory/`, `docs/closure/`, `docs/compound/`,
`docs/decisions/`, prior plans/reviews, and the `note:` prose at
`harness-manifest.yaml` L166/L171.

These MUST NOT be rewritten. They record what was true at the time. A
find-and-replace across `docs/` is an explicit failure of this plan. `T007`'s
diff MUST touch exactly five files.

## H9 — No reliance on unverified upstream behavior

`backlogit migrate` was **not** executed in any form during staging, including
`--dry-run`, per the session contract. Therefore:

* `--rollback` semantics are **unverified** and MUST NOT be the primary
  recovery path (H4's backup is).
* `T005`'s dry-run output MUST be read and reconciled against the plan's
  expectations before `T006`. If the dry-run reports anything other than a
  `.backlogit` → `.backlog` rename, **halt** and return to Stage.
* No agent may fabricate migrate behavior not observed in its own dry-run.

## H10 — Dual-root state fails closed; never "pick one"

If both roots ever exist, no agent may guess, merge, or delete a root to
"resolve" it. The mandated response is: set `BACKLOGIT_WORKSPACE_DIR` to
restore tooling, then execute the runbook recovery. Silent disambiguation is
exactly the backlog-state-split hazard `BED0DDED` has forbidden since 2026-08-07.

## H11 — The database must never enter git

`.backlog/backlogit.db` (8.09 MB) and `-wal` (6.26 MB) MUST never be staged.
`T001` closes this in advance; `T009` MUST additionally assert
`git status --porcelain` shows no DB/WAL/SHM path at either root before Commit B
is finalized. Use explicit path staging, not blind `git add -A`, in Commit B.

## H12 — Role boundary preserved

Stage authored the deliberation, plan, hardening, review and backlog structure
only. Stage did not and must not execute the migration, edit
`.autoharness/backlog-registry.yaml`, run builds, claim the shipment, or open
the PR. Every guard above is binding on **Ship**, which owns execution.

## H13 — The SQLite index is derived state, not the source of truth

`backlogit sync` rehydrates the index **from the Markdown source files**. The
authoritative backlog state is therefore the ~1613 tracked Markdown/JSONL
artifacts, not `backlogit.db`.

Consequences that materially reduce risk:

* Corruption or loss of `backlogit.db`/`-wal`/`-shm` during the move is a
  **rebuild**, not data loss — `T009` rebuilds the index unconditionally.
* Parity verification in `T006` MUST assert on the Markdown/JSONL inventory.
  A byte-difference in the `.db`/`-wal` files is expected and is **not** a
  failure signal.
* Conversely, any missing `queue/`, `archive/`, `checkpoints/`, `logs/`,
  `templates/`, `stash.jsonl`, `telemetry.jsonl` or `memories.json` artifact
  **is** unrecoverable-by-rebuild and MUST halt the shipment.

## H14 — The migration PR runs the full test gate; it must be green before merge

The changed-file set (`.gitignore`, `.engram/registry.yaml`, `tests/**`) makes
the fail-closed `changes` filter report `code == 'true'`, so the expensive
unittest gate **will** run on this PR. That is desirable and MUST NOT be
suppressed.

`T002` exists specifically because of this: the single live-root test binding
in `tests/test_gates_sizing.py` would otherwise fail post-migration and block
the merge at the worst possible moment — after the irreversible step. Routing
it through the resolver in **Commit A** means the gate is green both before and
after the rename.

## H15 — Backup disposal is operator-gated

The out-of-tree backup contains the full backlog history including
`telemetry.jsonl` and `memories.json`. It MUST NOT be deleted automatically on
success. Ship reports its path; the operator decides when to remove it, and
never before the PR is merged and `T009` verification has passed.

**HARDENED.** H1-H15 applied. The plan's irreversible step (`T006`) is
preceded by a verified backup (H4), a proven-released lock (H2), a reviewed
dry-run (H9) and a committed rollback runbook (`T003`), and is followed by a
fail-closed single-root assertion (H10).
