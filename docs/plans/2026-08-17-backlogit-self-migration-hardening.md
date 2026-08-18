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

## H4 — The backup MUST live inside the working directory, in a gate-proven contained location

> **CORRECTED 2026-08-17** (supersedes the original H4, which mandated an
> out-of-repository `$env:TEMP` backup). Constitution Principle IV / CLI
> containment **forbids** creating or modifying anything outside the current
> working directory tree. The original H4 was therefore a P1 safety/policy
> defect that made the plan unshippable. The prior text is preserved in git
> history; the corrected contract below is binding.

The backup MUST be written **inside the workspace/cwd**, and MUST be outside
both root-level storage candidates `.backlog` and `.backlogit`.

### Canonical backup root

```text
<repo>\.copilot\session-state\7ced3fcb-faba-47fb-81f9-09e0670a393f\files\backlog-premigration-<UTC-timestamp>\
```

The basename MUST NOT be `.backlog` or `.backlogit`, and MUST NOT begin with a
dot. `backlog-premigration-<yyyyMMddTHHmmssZ>` is the mandated form.

### Containment gates G1–G6 — ALL must pass BEFORE any byte is copied

| Gate | Assertion | Staging result |
|---|---|---|
| **G1** canonical containment | `[IO.Path]::GetFullPath(BACKUP_ROOT)` starts with the repo root plus a directory separator | **PASS** |
| **G2** no reparse point | every path segment from repo root down has no `FILE_ATTRIBUTE_REPARSE_POINT` (mirrors `_is_reparse_point`; junctions are not symlinks on Windows) | **PASS** |
| **G3** ignored | `git check-ignore -v` returns a matching rule | **PASS** — `.gitignore:4:*.copilot` |
| **G4** unstageable | `git status --porcelain` does not surface it, **and** `git add <path>` without `-f` exits non-zero | **PASS** — exit 1, nothing staged |
| **G5** non-candidate naming | basename ∉ {`.backlog`, `.backlogit`}, **and** after the copy a recursive scan finds **zero** directories named `.backlog`/`.backlogit` anywhere inside `BACKUP_ROOT` | **PASS** |
| **G6** resolver-undiscoverable | `resolve_backlog_root(BACKUP_ROOT)` and `resolve_backlog_root(<parent>)` both raise `BacklogUnavailableError`; `resolve_backlog_root(<repo>)` still returns the live root; `backlogit --cwd BACKUP_ROOT` errors and creates nothing | **PASS** |

If **any** gate fails, `T004` HALTS. Ship MUST NOT relocate the backup outside
the working directory to work around a failed gate — that reintroduces the
Principle IV violation. Select another **existing, ignored, in-repo** path
(documented fallback: `.autoharness/staging/`, ignored via `.gitignore:6`) and
re-run G1–G6 in full.

### G5 is load-bearing — proven by negative control

The resolver checks only `<workspace>/.backlog` and `<workspace>/.backlogit`;
it does **not** recurse downward, and the `backlogit` engine does **not** walk
up ancestors (`backlogit --cwd <rootless-subdir> list` →
`workspace storage root not found under <dir>`, exit 1, nothing created).

A backup whose top-level directory is **not** candidate-named is therefore
undiscoverable. But a negative control proved the converse: creating
`.copilot\session-state\<id>\files\.backlogit\` made
`resolve_backlog_root(files)` return **that** directory. Hence:

**Copy the CONTENTS of `.backlogit\*` into `BACKUP_ROOT`, never the
`.backlogit` directory itself.** `Copy-Item .backlogit -Destination X -Recurse`
creates `X\.backlogit` and **violates G5**. The copied `config.yaml` root
marker landing directly in a non-candidate-named `BACKUP_ROOT` is inert,
because selection is by directory **name**, not by marker presence.

### Backup verification is a bounded file-count / inventory check

An unverified backup is not a rollback capability. Before `T005` proceeds:

1. **File count** — backup count equals source inventory count (**1656**
   expected).
2. **Bounded inventory equality** — the set of relative paths under
   `BACKUP_ROOT` equals the set under `.backlogit`; the symmetric difference
   MUST be empty. This is a bounded comparison over the captured inventory, not
   an unbounded rescan.
3. **Per-path size equality** for every Markdown/JSONL/YAML artifact. Per
   **H13**, `backlogit.db`/`-wal`/`-shm` byte differences are expected and are
   explicitly **excluded** from the failure criterion.
4. **Directory subtotals** — `archive/` = 820, `queue/` = 12.
5. A `backup-manifest.json` (count, relative-path inventory, sizes, the six
   gate results) is written alongside the backup and its counts recorded in the
   task record.

Any mismatch ⇒ the backup is INVALID ⇒ **HALT**; `T005` and `T006` MUST NOT run.

### Backup preservation constraints (the backup is ignored, therefore fragile)

Because the backup is deliberately gitignored (**G3**), it is invisible to git
and **would be destroyed by `git clean -x`/`-X`**. For the whole window from
`T004` until operator-approved disposal:

* `git clean` with `-x` or `-X` is **PROHIBITED**. Plain `git clean -fd` is
  also prohibited during the window (it removes untracked directories and its
  behaviour near ignored paths is easy to get wrong).
* Copilot session state MUST NOT be cleared or pruned (**H15**).
* Ship MUST re-assert backup existence + inventory immediately before `T006`.

### Re-verification before the irreversible step

Because the backup now lives under CLI-managed session state, Ship MUST
**re-assert** backup existence and the file-count/inventory check immediately
before `T006`, at the same point H2's lock probe is re-run. A missing or
mismatched backup at that moment HALTS the shipment.

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
  immediately, then **HALT**. Determining which root holds the authoritative
  `config.yaml` is an *evidence-gathering* step, not an authorization to
  delete. Removal of a residual root requires **explicit operator approval**
  and MUST target that one enumerated path only (see **H16**).

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
restore tooling, then follow the **H16** preserve-and-halt contract. Silent
disambiguation is exactly the backlog-state-split hazard `BED0DDED` has
forbidden since 2026-08-07.

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

> **CORRECTED 2026-08-17** — "out-of-tree" replaced by the H4 in-repo canonical
> backup root. The operator-gated disposal rule itself is **retained
> unchanged**.

The backup contains the full backlog history including `telemetry.jsonl` and
`memories.json`. It MUST NOT be deleted automatically on success. Ship reports
its path; the operator decides when to remove it, and never before the PR is
merged and `T009` verification has passed.

Because the backup now lives under `.copilot/session-state/`, one additional
binding constraint applies: **Copilot session state MUST NOT be cleared or
pruned until the operator has approved disposal.** Ship records the absolute
backup path in the task record, the runbook, and the handoff so a later session
can locate it.

## H16 — Failure recovery is non-destructive, evidence-first, and operator-gated

> **ADDED 2026-08-17.** The original plan's rollback directed
> `delete .backlog` and `git checkout -- .` **automatically**. Both are
> destructive and broad, they violate surgical preservation, and general
> migration authorization does **not** silently authorize a destructive broad
> rollback after failure. That was a P1 defect. This guard replaces it.

On dual-root detection, partial migration, or any `T006`-window failure, the
mandated sequence is:

1. **Restore tooling, mutate nothing.** Set a **verified**
   `BACKLOGIT_WORKSPACE_DIR` override. Verification means: the value is exactly
   `.backlog` or `.backlogit` (case-sensitive; the resolver rejects paths,
   separators, `.`/`..`, absolute and drive/UNC forms), the named directory
   exists, is a real directory, and is not a symlink or reparse point. The
   validated override returns before the ambiguity check, so tooling resolves
   immediately without touching the filesystem.
2. **Preserve everything.** Both roots and the H4 backup are retained
   **as-is**. Delete nothing. Restore nothing. Move nothing.
3. **Record evidence.** Capture: the inventory of each root, which root holds
   the authoritative `config.yaml`, `git status --porcelain`, resolver and
   `backlogit --cwd .` output, the backup path and its verification result, and
   timestamps. Write this to the task record and the runbook recovery section.
4. **HALT and request explicit operator approval** for any deletion or
   restoration. Do not proceed on inference, precedent, or the general
   migration authorization.
5. **Prohibitions, absolute.** Never auto-delete a root. Never run a broad
   `git checkout -- .` or any whole-worktree reset. Never guess authority
   between two roots.
6. **A future approved rollback targets explicit paths only.** Once the
   operator approves, restoration is performed against an **enumerated path
   list** — e.g. `git checkout -- .gitignore .engram/registry.yaml
   tests/test_gates_sizing.py .autoharness/backlog-registry.yaml
   .autoharness/config.yaml .autoharness/workspace-profile.yaml
   .autoharness/harness-manifest.yaml` — and the backlog root is restored by
   copying from the named backup path into an explicitly named destination.
   Pathspec-less and wildcard forms remain forbidden even after approval.

`backlogit migrate --rollback` remains **secondary and unverified** (**H9**)
and is likewise operator-gated.

**HARDENED.** H1-H16 applied (H4 corrected, H16 added, 2026-08-17). The plan's
irreversible step (`T006`) is preceded by a gate-proven **in-repo** backup
(**H4**), a proven-released lock (**H2**), a reviewed dry-run (**H9**) and a
committed rollback runbook (`T003`), and is followed by a fail-closed
single-root assertion (**H10**) whose failure path is non-destructive and
operator-gated (**H16**).

---

## SUPERSEDED — CANCELLED BY OPERATOR SCOPE CORRECTION (2026-08-18)

> **APPEND-ONLY NOTICE. Hardening controls H1–H16 above are preserved
> verbatim.** No control has been weakened, removed, or re-scoped.

**The plan these controls harden will not execute. Status: CANCELLED.**

Per `docs/decisions/2026-08-18-backlogit-legacy-root-support-operator-scope-correction.md`,
`.backlogit` remains a supported workspace root, `.backlog` is the default for
**new workspaces only**, and **existing workspaces need no migration**. The
live self-migration of this repository is cancelled.

**H1–H16 are hereby DORMANT, not retired.** They were authored against a
live storage-root rename. They are preserved here because:

* they remain the correct control set **if** a root migration is ever
  authorized in future — do not re-derive them, reuse them;
* **H16** (never auto-delete a root; never broad `git checkout -- .`; preserve
  both roots and the backup; HALT for explicit operator approval) states a
  general safety rule that outlives this plan and should be honoured by any
  future work touching storage roots;
* the **G1–G6 containment proof** for an in-working-directory backup, and the
  negative control proving G5 (non-candidate naming) is load-bearing, are
  reusable empirical results independent of the migration goal.

**No control here is to be executed now.** In particular: create no backup,
take no lock, run no dry-run, and perform no single-root assertion.

Ironically, the size of this control set is itself part of the operator's
stated rationale for cancellation: a cosmetic rename that required sixteen
hardening controls and a six-gate containment proof to be survivable is a
change whose cost/benefit does not close.
