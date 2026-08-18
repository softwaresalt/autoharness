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

## Correction record — 2026-08-17 (Stage, post-Orchestrator review)

Two P1 defects were found by Orchestrator review **after** the original PASS
verdict and corrected here. Prior provenance is preserved in git history and in
the review's appended correction pass; nothing was erased.

| # | Defect | Correction |
|---|---|---|
| C1 | The plan, **H4**, **H15**, `T004`, the handoff and the rollback all required an out-of-repository `$env:TEMP` backup — a Constitution Principle IV / CLI-containment violation that made the plan unshippable | Backup relocated **inside the working directory**, outside both root-level storage candidates, at a gate-proven contained path; **G1–G6** containment gates added and empirically verified |
| C2 | Rollback directed `delete .backlog` and `git checkout -- .` **automatically** — destructive, broad, and not authorized by the general migration authorization | Replaced by the **H16** preserve-and-halt contract: verified `BACKLOGIT_WORKSPACE_DIR`, preserve both roots and the backup, record evidence, HALT for explicit operator approval; approved rollback targets explicit enumerated paths only |

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
| P7 | In-repo contained backup exists, gates G1–G6 pass, and inventory is verified | Backup manifest file-count + relative-path inventory match source |

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
recovery section reproducing the **H16** preserve-and-halt contract; states
that restore from the **H4 in-repo contained backup** is the **primary**
recovery mechanism and `migrate --rollback` is secondary and unverified; states
that every recovery action is operator-gated and targets explicit enumerated
paths only.

*Size S · Complexity low · ~45 min*

### T004 — Pre-flight gate, inventory snapshot, contained in-repo backup

Verify P1–P4 and P6. Then capture a snapshot to a gate-proven contained path
**inside the working directory** and **outside both root-level storage
candidates** (`.backlog`, `.backlogit`):

```text
.copilot\session-state\7ced3fcb-faba-47fb-81f9-09e0670a393f\files\backlog-premigration-<UTC-timestamp>\
```

Run containment gates **G1–G6** (see **H4**) and record each result **before
copying any byte**. All six passed at staging time. If any fails, HALT and
select another existing ignored in-repo path (fallback: `.autoharness/staging/`);
**never write outside the working directory** — that is a Constitution
Principle IV / CLI-containment violation.

Capture:

* full recursive relative-path + size inventory of `.backlogit` (expect 1656
  files),
* `backlogit list` / `query_sql` counts by `artifact_type` + `status`,
* `backlogit checkpoint list` count (expect 32) and stash entry count,
* a byte-for-byte copy of the **contents** of `.backlogit\*` into the backup
  root — **not** the `.backlogit` directory itself, which would create a
  candidate-named directory and violate **G5**.

**The backup MUST NOT be written outside the working directory tree**, and MUST
NOT create any directory named `.backlog` or `.backlogit` at any depth.

**Acceptance:** G1–G6 all recorded PASS; backup exists at the contained path;
file count equals the source inventory count (1656) and the relative-path
inventory symmetric difference is empty; `archive/` = 820 and `queue/` = 12
subtotals match; DB/WAL/SHM byte differences excluded per **H13**;
`backup-manifest.json` written; snapshot recorded in the task record. An
unverified backup is not a rollback capability.

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

If **both** exist, STOP: do not commit, do not continue. Set a verified
`BACKLOGIT_WORKSPACE_DIR` to restore tooling, preserve both roots and the
backup, record evidence, and HALT for explicit operator approval per **H16**.
Do **not** delete a root and do **not** run a broad `git checkout -- .`.

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

## Failure recovery (replaces the former "Rollback" section)

> **CORRECTED 2026-08-17.** The former rollback directed `delete .backlog` and
> `git checkout -- .` **automatically**. Both are destructive and broad, and
> general migration authorization does not silently authorize them after a
> failure. Superseded by **H16**.

**On any failure, dual-root state, or partial migration — the immediate,
non-negotiable sequence:**

1. Set a **verified** `BACKLOGIT_WORKSPACE_DIR` override (exactly `.backlog` or
   `.backlogit`, existing, a real directory, not a symlink/reparse point) so
   tooling resolves again **without touching the filesystem**.
2. **Preserve both roots and the H4 backup.** Delete nothing, restore nothing,
   move nothing.
3. **Record evidence**: per-root inventories, which root holds the
   authoritative `config.yaml`, `git status --porcelain`, resolver output,
   backup path and verification result, timestamps.
4. **HALT** and request **explicit operator approval** for any deletion or
   restoration.

**Prohibited without explicit operator approval — and prohibited outright in
their broad forms:**

* auto-deleting either root,
* `git checkout -- .` or any whole-worktree reset,
* guessing which root is authoritative.

**A future approved rollback targets explicit paths only** — an enumerated
pathspec list for tracked files, and a named source/destination pair for the
backlog-root copy-back from the **H4** backup. `backlogit migrate --rollback`
remains **secondary, unverified (H9), and operator-gated**.

**Dual-root emergency (non-destructive, always safe):**
`BACKLOGIT_WORKSPACE_DIR=.backlog` (or `.backlogit`) restores resolution
immediately in both the engine and the harness resolver without touching the
filesystem.

---

## SUPERSEDED — CANCELLED BY OPERATOR SCOPE CORRECTION (2026-08-18)

> **APPEND-ONLY NOTICE. Nothing above this line has been altered, deleted, or
> back-dated.** Every step, hardening reference, containment proof and
> rationale above remains the authentic record of what was planned.

**This plan WILL NOT EXECUTE. Status: CANCELLED.**

The operator issued an authoritative scope correction recorded at
`docs/decisions/2026-08-18-backlogit-legacy-root-support-operator-scope-correction.md`:

1. `.backlogit` **remains an acceptable, supported** Backlogit workspace
   directory — permanently, with no removal schedule.
2. `.backlog` is the default **only for NEW workspaces** into which Backlogit
   is installed.
3. **Existing workspaces do NOT need migration** — including this repository.

The premise of this plan — that this repository's live `.backlogit` root must
be renamed to `.backlog` — has therefore been withdrawn. There is no longer any
outcome this plan can deliver that the operator wants.

**This is a scope withdrawal, NOT a quality judgement.** This plan passed
review (0 P0 / 0 P1) and was hardened to H1–H16 including a six-gate,
empirically verified containment proof. It was correct as designed. It is
cancelled because its *goal* is no longer desired, not because it was unsound.

**Do not execute any step of this plan.** Do not rename, create, or delete any
storage root. Do not create the pre-migration backup.

Disposition of the associated backlog artifacts:

* `129-F` → `rejected`
* `129.001-T` … `129.009-T` → `rejected`
* `138-S` → `abandoned` (Ship-owned; see §5 of the decision artifact for the
  exact supported command sequence and the `queued → active → abandoned`
  transition constraint)

The already-shipped new-workspace product surface (`126-F` / `135-S` / PR #345
/ merge `9851cc3`) is **unaffected and remains correct**.
