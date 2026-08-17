---
title: Backlogit self-migration implementation plan
description: Granular, sub-2h task plan to migrate this repository's live Backlogit storage root from .backlogit to .backlog in one shipment
doc_type: plan
source: docs/plans/2026-08-17-backlogit-self-migration-plan.md
status: hardened
date: 2026-08-17
stash_source: BED0DDED
deliberation: docs/decisions/2026-08-17-backlogit-self-migration-choreography-deliberation.md
route: claude-opus-5/anthropic/high
requires_plan_hardening: yes
---

# Backlogit self-migration implementation plan

## Scope

Migrate this repository's live Backlogit storage root from `.backlogit` to
`.backlog`, and bring every operative follower reference into agreement.

**In scope:** the operational directory move, the 1613-file git rename, the
`.gitignore`/CI path-filter superset, four config surfaces, three manifest
checksums, verification and rollback.

**Out of scope:** the shipped `126-F` product surface (resolver, templates,
schemas, tests, installer/tuner) — complete and must not be re-touched;
historical `docs/` prose mentioning `.backlogit` (immutable record); stale lock
residue cleanup; any change to the external `backlogit` repository.

## Requires plan hardening

**yes** — live workspace-state migration with repository-wide blast radius.
See `docs/plans/2026-08-17-backlogit-self-migration-hardening.md`.

## Commit structure

Two ordered commits on one branch, one PR, one shipment.

* **Commit A** — root-agnostic superset prep. Correct before *and* after the
  rename; creates no ordering hazard.
* **Commit B** — the atomic switch: move, config flip, checksum refresh,
  verification.

## Preconditions (all must hold before Commit B)

| # | Precondition | Check |
|---|---|---|
| P1 | Exactly one worktree, on the shipment branch | `git worktree list` returns 1 |
| P2 | Working tree clean apart from intended changes | `git status --porcelain` |
| P3 | No other agent session active | Operator confirmation; no active shipment other than this one |
| P4 | Zero active checkpoints | `backlogit checkpoint list` |
| P5 | No `backlogit.exe` process running | `Get-Process backlogit` returns none |
| P6 | `.backlog` does **not** exist | `Test-Path .backlog` is `False` |
| P7 | Out-of-tree backup exists and is verified | Backup manifest file-count matches source |

## Tasks

### T001 — Make `.gitignore` and CI path filters root-agnostic (Commit A)

Rewrite the four path-literal ignore rules to cover **both** roots, and add
`- '!.backlog/**'` alongside the existing `- '!.backlogit/**'` in
`.github/workflows/ci.yml`'s `paths-filter` denylist.

```gitignore
.backlogit/*.db
.backlogit/*.db-shm
.backlogit/*.db-wal
.backlogit/hooks_queue.jsonl
.backlog/*.db
.backlog/*.db-shm
.backlog/*.db-wal
.backlog/hooks_queue.jsonl
```

**Acceptance:** `git check-ignore -v .backlog/backlogit.db` resolves once
`.backlog` exists; `git status --porcelain` shows no new untracked DB files at
either path; the `code:` filter still excludes backlog state under both names.
Commit A is self-contained and mergeable on its own.

*Size XS · Complexity low · ~30 min*

### T002 — Route the live-root test binding through the resolver (Commit A)

`tests/test_gates_sizing.py` line 72 binds to the **live repository root** with
a hardcoded literal:

```python
header_def = yaml.safe_load((_REPO_ROOT / ".backlogit" / "header-def.yaml").read_text())
```

This is the only such binding in the entire repository (verified across
`tests/`, `src/autoharness/`, `src/autoharness/gates/` and `scripts/`). After
migration it raises `FileNotFoundError` and **turns the migration PR red**,
because the PR's changed files (`.gitignore`, `.engram/registry.yaml`,
`tests/**`) make the fail-closed `changes` filter report `code == 'true'` and
run the full unittest gate.

Replace the literal with the shipped resolver:

```python
from autoharness.backlog_root import resolve_backlog_root
header_def = yaml.safe_load((resolve_backlog_root(_REPO_ROOT) / "header-def.yaml").read_text())
```

This is the same resolver-routing fix applied to
`topology.py FilesystemTopologyReaders.backlog_dir` in `126-F`, and it is
correct **before and after** the migration — so it belongs in Commit A.

**Acceptance:** `python -m unittest tests.test_gates_sizing -v` passes on the
current `.backlogit` root; no hardcoded live-root literal remains; the repo-wide
scan for `_REPO_ROOT / ".backlogit"` returns zero hits.

*Size XS · Complexity low · ~30 min*

### T003 — Author the migration runbook and rollback procedure

Create `docs/runbooks/2026-08-17-backlogit-storage-root-migration.md`
containing: the ordered command sequence, the preconditions table, the
single-root assertion, the parity-verification method, the **E9 residue**
prohibition and recovery, and the `BACKLOGIT_WORKSPACE_DIR` escape hatch.

**This document MUST exist and be committed before T006 executes.** A rollback
procedure authored after the irreversible step is not a rollback procedure.

**Acceptance:** runbook committed; contains an explicit "if both roots exist"
recovery section; states that out-of-tree backup restore is the **primary**
recovery mechanism and `migrate --rollback` is secondary and unverified.

*Size S · Complexity low · ~45 min*

### T004 — Pre-flight gate, inventory snapshot, out-of-tree backup

Verify P1–P4 and P6. Capture a snapshot to a path **outside the repository**
(e.g. `$env:TEMP\backlogit-premigration-<timestamp>\`):

* full recursive relative-path + size inventory of `.backlogit` (expect 1656
  files),
* `backlogit list` / `query_sql` counts by `artifact_type` + `status`,
* `backlogit checkpoint list` count (expect 32) and stash entry count,
* a byte-for-byte **copy** of the entire `.backlogit` tree.

**The backup MUST NOT be written inside the repository working tree** — a copy
at any in-tree path risks creating a second discoverable root or polluting git.

**Acceptance:** backup directory exists outside the repo; its file count equals
the source inventory count; snapshot JSON/text committed under
`docs/runbooks/` or attached to the task record.

*Size S · Complexity medium · ~45 min*

### T005 — Stop backlogit processes and execute the dry-run

Stop every `backlogit.exe` process by explicit PID (`Stop-Process -Id`). Re-verify
P5. Then run:

```powershell
backlogit migrate --workspace-dir --dry-run --format json
```

Review the report. Confirm it reports a `.backlogit` → `.backlog` rename and
does **not** report unexpected deletions or source-import behavior.

**Acceptance:** zero `backlogit.exe` processes remain; the exclusive-open probe
on `.backlogit/backlogit.db` now **succeeds** (proving no lock remains); dry-run
report captured verbatim in the task record; no mutation performed.

*Size S · Complexity medium · ~40 min*

### T006 — Execute the migration and assert a single root

Run `backlogit migrate --workspace-dir`. Immediately assert:

* `Test-Path .backlog` is `True`
* `Test-Path .backlogit` is `False`  ← **fail-closed dual-root detection**

If **both** exist, STOP: do not commit, do not continue. Set
`BACKLOGIT_WORKSPACE_DIR` to restore tooling, then execute the runbook
recovery from the out-of-tree backup.

Then verify parity against the T004 inventory: every relative path and size
present under `.backlog`, file count equal, and specifically that
`queue/`, `archive/` (820 files), `checkpoints/`, `logs/`, `templates/`,
`stash.jsonl`, `telemetry.jsonl`, `memories.json`, `hooks.yaml`,
`migration.yaml`, `registry.yaml`, `header-def.yaml`, `config.yaml` all survive.

**Acceptance:** exactly one root exists; parity diff is empty; no file lost.

*Size S · Complexity high · ~45 min*

### T007 — Flip the operative config surfaces

Update, in one commit-scoped edit set:

| File | Change |
|---|---|
| `.autoharness/backlog-registry.yaml` | `directory: ".backlogit"` → `".backlog"` |
| `.autoharness/config.yaml` | L28 `directory:` → `".backlog"` |
| `.autoharness/workspace-profile.yaml` | L142, L145, L236, L240 |
| `.engram/registry.yaml` | L16 `path: .backlogit` → `.backlog` |
| `.autoharness/harness-manifest.yaml` | L307 `BACKLOG_DIRECTORY: ".backlog"` |

**Do NOT modify** the historical `note:` prose at `harness-manifest.yaml` L166
and L171, or any file under `docs/archive/`, `docs/memory/`, `docs/closure/`,
`docs/compound/`. Those are immutable record.

**Acceptance:** no operative surface still names `.backlogit`; historical prose
byte-identical; `git diff` touches only the five files above.

*Size S · Complexity low · ~40 min*

### T008 — Refresh the three recorded manifest checksums

`harness-manifest.yaml` records checksums for `backlog-registry.yaml`,
`config.yaml` and `workspace-profile.yaml`, all edited by T007. Recompute each
from the **LF-normalized committed git blob** via
`git cat-file -p :<path> | sha256`, per the procedure established in 115-S —
not from the CRLF working-tree file.

**Acceptance:** all three checksums updated; each recomputed from the staged
blob; a verify pass reports no checksum drift.

*Size S · Complexity medium · ~40 min*

### T009 — Post-migration verification and index rebuild

1. `backlogit --cwd . list` resolves `storage_root=...\.backlog`.
2. `backlogit sync` rebuilds the index; indexed count matches the T004
   snapshot (**834** at staging time).
3. Counts by `artifact_type`/`status` match the T004 snapshot exactly.
4. `backlogit checkpoint list` returns the snapshot count (**32**), zero
   quarantined.
5. Stash entries intact, including `BED0DDED`.
6. `bash scripts/ci-topology-check.sh` passes (resolves `.backlog`, no
   ambiguity).
7. Restart the MCP servers and confirm tool calls resolve the new root.

**Acceptance:** every count matches the pre-migration snapshot; topology gate
passes; MCP tools operational against `.backlog`.

*Size S · Complexity medium · ~45 min*

## Dependency order

```text
T001 ─┐
T002 ─┼─> T004 ─> T005 ─> T006 ─> T007 ─> T008 ─> T009
T003 ─┘
```

`T001`, `T002` and `T003` are mutually independent; all three gate `T004`.
`T001` and `T002` form **Commit A** (root-agnostic prep, independently
mergeable); `T003` is documentation that must land before the irreversible
step. Everything from `T004` onward is strictly serial — each step's output is
the next step's precondition — and `T004`–`T009` form **Commit B**.

## Rollback

**Primary:** stop all `backlogit.exe`, delete `.backlog`, restore `.backlogit`
from the T004 out-of-tree backup, `git checkout -- .` to restore tracked state,
restart MCP.

**Secondary (unverified, convenience only):** `backlogit migrate --rollback`.
The plan does not depend on it.

**Dual-root emergency:** `BACKLOGIT_WORKSPACE_DIR=.backlog` (or `.backlogit`)
restores resolution immediately in both the engine and the harness resolver
without touching the filesystem.
