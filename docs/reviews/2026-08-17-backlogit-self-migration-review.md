---
title: Backlogit self-migration plan and decision review
description: Multi-persona adversarial review of the self-migration deliberation, plan and hardening
doc_type: review
source: docs/reviews/2026-08-17-backlogit-self-migration-review.md
status: pass
date: 2026-08-17
correction_pass: 2026-08-17
stash_source: BED0DDED
plan: docs/plans/2026-08-17-backlogit-self-migration-plan.md
hardening: docs/plans/2026-08-17-backlogit-self-migration-hardening.md
deliberation: docs/decisions/2026-08-17-backlogit-self-migration-choreography-deliberation.md
verdict: PASS
p0_count: 0
p1_count: 0
route: claude-opus-5/anthropic/high
---

# Backlogit self-migration plan and decision review

**Verdict: PASS — 0 unresolved P0, 0 unresolved P1.**

Six adversarial personas reviewed the deliberation, plan and hardening. Eight
findings were raised; all P1 findings were resolved by amending the plan or
hardening before this verdict was issued. Remaining P2 items are recorded as
out-of-scope with rationale.

## Persona 1 — Reliability / SRE

### F1 (P1, RESOLVED) — The plan treated the SQLite index as precious state

The original parity criteria implied that a byte-difference in
`backlogit.db`/`-wal` constituted migration failure. That is wrong and
dangerous in both directions: it could halt a healthy migration, and it
distracted from the artifacts that genuinely cannot be rebuilt.

`backlogit sync` rehydrates the index **from Markdown source files**, so the
database is derived state. Losing it is a rebuild; losing `archive/` (820
files) or `stash.jsonl` is unrecoverable.

**Resolution:** added **H13**. Parity assertions now target the
Markdown/JSONL inventory; DB byte-differences are explicitly expected and not a
failure signal, while any missing Markdown/JSONL artifact halts the shipment.
This materially lowers the residual risk of the whole plan.

### F2 (P2, ACCEPTED) — Backup retention

The backup contains full telemetry and memory history. Auto-deleting
it on success would destroy the only recovery artifact at the moment it is most
likely to be needed.

**Resolution:** added **H15** — disposal is operator-gated, never automatic,
never before merge and `T009` verification. *(Correction pass: the backup
location moved out-of-tree → in-repo contained; the operator-gated disposal
rule is retained unchanged. See F9.)*

## Persona 2 — Windows platform specialist

### F3 (P1, RESOLVED) — `Get-Process` does not prove handle release

The original **H2** allowed the stop precondition to be satisfied by a process
check. Windows releases file handles asynchronously after process exit, so a
rename can still fail with a sharing violation moments after `Get-Process`
returns empty.

Additionally, the plan's own dry-run (`T005`) opens the workspace in a fresh
process **after** the stop step — re-acquiring and releasing handles — so a
probe taken only at stop time is stale by the time the rename runs.

**Resolution:** **H2** rewritten. The exclusive-open (`FileShare.None`) probe
must succeed, with bounded retry, and must be re-run **after** the dry-run and
immediately **before** `T006`. Halt if it fails.

## Persona 3 — Git / VCS specialist

### F4 (P1, RESOLVED) — Ignored-file residue creates dual-root on ref transition

Because the DB files are gitignored, `git checkout` of a pre-migration ref
leaves `.backlog/` on disk holding only ignored residue while restoring
`.backlogit/`. The engine survives (residue lacks the `config.yaml` root
marker), but `src/autoharness/backlog_root.py` and
`scripts/ci-topology-check.sh` both test bare directory existence and fail
closed.

The subtle case: syncing `main` after merge via `git checkout main && git pull`
transits **stale pre-migration `main`** and triggers exactly this.

**Resolution:** **H6** prohibits post-Commit-B transitions to pre-migration
refs and mandates `git fetch origin` + `git checkout -B main origin/main`,
with `BACKLOGIT_WORKSPACE_DIR` as the immediate recovery.

### F5 (P1, RESOLVED) — Blind staging could commit a 14 MB database

`.gitignore` rules are path-literal (`.backlogit/*.db`), so post-rename the
14 MB of DB/WAL state matches no rule.

**Resolution:** `T001` makes the ignore rules a **superset** covering both
roots in **Commit A**, before the rename exists; **H11** additionally requires
explicit path staging (not `git add -A`) in Commit B plus a `git status`
assertion that no DB/WAL/SHM path is staged at either root.

## Persona 4 — CI / test integrity

### F6 (P1, RESOLVED) — A live-root test binding would turn the migration PR red

`tests/test_gates_sizing.py:72` reads
`_REPO_ROOT / ".backlogit" / "header-def.yaml"` — a hardcoded binding to the
**live repository root**. A repo-wide scan confirms it is the only one across
`tests/`, `src/autoharness/`, `src/autoharness/gates/` and `scripts/`.

Post-migration this raises `FileNotFoundError`. The PR's changed files
(`.gitignore`, `.engram/registry.yaml`, `tests/**`) make the fail-closed
`changes` filter report `code == 'true'`, so the unittest gate **will** run and
**will** fail — blocking merge immediately after the irreversible step. This is
the single most damaging defect found in this review.

**Resolution:** added task **T002** (Commit A) routing the binding through
`resolve_backlog_root(_REPO_ROOT)` — the same fix `126-F` applied to
`topology.py` — plus **H14** recording why it must land in Commit A. Correct
before and after the rename.

### F7 (P2, OUT OF SCOPE) — Stale scratch artifacts at repository root

`out.json`, `res.json` and `results.json` are tracked 25.8 KB
`verify-workspace` outputs whose `workspace_path` is the **external**
`D:\Source\GitHub\backlogit` repository. They reference `.backlogit` as that
workspace's directory and are irrelevant to this migration.

**Disposition:** recorded, not fixed. Cleaning them is unrelated hygiene and
would widen this change's diff without reducing its risk. Stashed as follow-up.

## Persona 5 — Backlog / process governance

### F8 (P1, RESOLVED) — Narrowing H5 risked being read as blanket permission

The plan supersedes the scope of the 2026-08-14 hardening `H5`, which excluded
this migration from automation. Left implicit, a future agent could cite this
plan as precedent for automating the migration in a dark-factory run.

**Resolution:** **H5** now states explicitly that the original exclusion
remains in force for dark-factory, unattended, and concurrent-agent runs, and
is narrowed **only** for the operator-present, idle-gated case; if the H1 gate
cannot be satisfied, the original exclusion applies unchanged.

### Governance checks passed

* Role boundary preserved — Stage produced only deliberation, plan, hardening,
  review and backlog structure (**H12**). No migration, no config edit, no
  build, no PR, no shipment claim.
* Historical record protected — **H8** forbids rewriting the ~150 historical
  files that mention `.backlogit`; `T007`'s diff is bounded to five files.
* Provenance to `BED0DDED` preserved on every artifact.
* Every task is sized under the 2-hour rule with both axes assigned.

## Persona 6 — Devil's advocate against the chosen decision

*Challenge: is one PR genuinely safe, or merely convenient?*

Two rebuttals were tested and both failed to overturn the decision:

1. *"Two PRs isolate the risk."* — They do not. P-001 forces sequential
   execution anyway, so both designs contain exactly **one** post-migration
   merge. The two-PR design adds an extra branch-creation and ref-transition
   cycle, and after **F4** every additional ref transition is a live hazard.
   Two PRs is strictly worse.
2. *"The shipment manifest cannot survive relocating itself."* — Empirically
   falsified. `backlogit` resolves its root **fresh per process** with no
   cross-move caching (**E7**: a fresh process in an empty directory creates
   nothing and simply errors), and the manifest moves with the rest of the
   root. With MCP stopped during the window, no process holds a stale resolved
   root, and the shipment remains addressable by ID at the new path.

*Residual challenge accepted:* `migrate --rollback` semantics were never
executed and remain unverified. The plan correctly does **not** depend on them
(**H9**); the in-repo containment-gated backup (**H4**) is the primary recovery
path.

## Findings summary

| ID | Severity | Persona | Status |
|---|---|---|---|
| F1 | P1 | Reliability | RESOLVED — H13 |
| F2 | P2 | Reliability | RESOLVED — H15 |
| F3 | P1 | Windows platform | RESOLVED — H2 rewritten |
| F4 | P1 | Git/VCS | RESOLVED — H6 |
| F5 | P1 | Git/VCS | RESOLVED — T001 + H11 |
| F6 | P1 | CI/test integrity | RESOLVED — T002 + H14 |
| F7 | P2 | CI/test integrity | OUT OF SCOPE — stashed |
| F8 | P1 | Governance | RESOLVED — H5 narrowed explicitly |

**0 unresolved P0. 0 unresolved P1. Plan approved for harvest.**

---

# Correction pass — 2026-08-17 (post-Orchestrator review)

The verdict above was issued over a plan carrying **two P1 defects that this
review missed**. Orchestrator review found them. This appended pass re-runs the
multi-persona adversarial review against the **corrected safety contract**
only; the original pass is retained above as provenance and is not erased.

**Missed-defect accountability:** Persona 1 and Persona 5 both accepted "the
backup lives outside the repository" as a *safety* property without testing it
against Constitution Principle IV / CLI containment, which forbids creating or
modifying anything outside the current working directory. Persona 3 reviewed
staging hazards but never read the rollback section's `git checkout -- .` as an
in-scope destructive breadth question. Both are review-coverage gaps, now
closed by adding containment and destructive-authority to the persona charters.

## Persona 7 — Security / containment (Principle IV)

### F9 (P1, RESOLVED) — Out-of-repository backup violated CLI containment

The plan, **H4**, **H15**, `129.004-T`, the Ship handoff and the rollback all
mandated a backup under `$env:TEMP` — outside the working directory tree. This
is a non-negotiable Principle IV violation and made the plan unshippable. It
was not a stylistic preference: no amount of migration authorization permits
writing outside cwd.

**Resolution:** **H4** rewritten. The backup moves inside the working
directory, outside both root-level storage candidates, to
`.copilot\session-state\<id>\files\backlog-premigration-<UTC>\`, behind six
containment gates **G1–G6**, all empirically verified this session:

| Gate | Result | Evidence |
|---|---|---|
| G1 canonical containment | PASS | `GetFullPath` resolves under the repo root |
| G2 no reparse point | PASS | every segment `ReparsePoint = None` |
| G3 ignored | PASS | `.gitignore:4:*.copilot` |
| G4 unstageable | PASS | `git add` exit 1; `git status` clean; nothing staged |
| G5 non-candidate naming | PASS | basename is not `.backlog`/`.backlogit` |
| G6 resolver-undiscoverable | PASS | `BacklogUnavailableError` at the path and its parent |

Escape-hatch abuse is closed explicitly: a failed gate does **not** authorize
relocating outside cwd; it requires selecting another existing ignored in-repo
path (`.autoharness/staging/`) and re-running all six gates.

## Persona 8 — Backlog-root / self-hosting specialist

### F10 (P1, RESOLVED) — The obvious in-repo fix would have created a second root

The original H4's stated justification was real: a naive in-repo backup made by
`Copy-Item .backlogit -Destination X -Recurse` creates `X\.backlogit` — a
**candidate-named** directory. A **negative control** confirmed the danger:
creating `.copilot\session-state\<id>\files\.backlogit\` caused
`resolve_backlog_root(files)` to return **that** directory.

Root selection is by directory **name**, not by `config.yaml` marker presence;
the resolver does not recurse downward, and the engine does not walk up
ancestors (`backlogit --cwd <rootless-subdir> list` → `workspace storage root
not found`, exit 1, **nothing created**).

**Resolution:** **G5** is therefore load-bearing and mandates copying the
**contents** of `.backlogit\*` into a non-candidate-named backup root, never
the directory itself, plus a post-copy recursive assertion that zero
`.backlog`/`.backlogit` directories exist at any depth inside the backup. The
copied `config.yaml` landing in a non-candidate-named directory is inert.

## Persona 9 — Git / VCS specialist

### F11 (P1, RESOLVED) — In-repo backup must not be able to enter git

The original H4's second justification — committing ~14 MB of binary SQLite
state — is also real.

**Resolution:** closed by proof rather than by distance. **G3** shows the path
matches `.gitignore:4:*.copilot`; **G4** shows `git status --porcelain` does
not surface it and `git add` without `-f` exits **1** with nothing staged;
**H11** independently forbids `git add -A` in Commit B and requires explicit
path staging. Three independent layers.

### F12 (P1, RESOLVED) — `git clean -x` would silently destroy the backup

**Newly found in this pass.** Being gitignored is what makes the backup safe
for git — and simultaneously makes it a target for `git clean -x`/`-X`, which
deletes ignored files. A routine cleanup between `T004` and disposal would
destroy the **primary recovery artifact**, and nothing in the plan forbade it.

**Resolution:** **H4** now prohibits `git clean -x`/`-X` (and plain
`git clean -fd`) for the entire window from `T004` until operator-approved
disposal, alongside the H15 session-state preservation rule and a mandatory
backup re-assertion immediately before `T006`.

## Persona 10 — Reliability / durability

### F13 (P2, ACCEPTED with mitigation) — The backup lives in CLI-managed state

`.copilot/session-state/` is managed by the Copilot CLI, and the chosen
subdirectory belongs to **Stage's** session while Ship executes in a different
one. Aggressive pruning would remove the recovery artifact.

**Evidence against high severity:** 27 session-state directories are present
and the oldest dates to **2026-04-22** (~4 months), so pruning is not
aggressive. Free space is 323 GB against a ~14 MB payload.

**Mitigation:** **H15** forbids clearing session state before operator-approved
disposal; **H4** requires backup re-assertion immediately before the
irreversible step, so a vanished backup HALTS rather than silently proceeding;
the absolute path is recorded in the task record, runbook and handoff.
`.autoharness/staging/` remains the documented fallback.

## Persona 11 — Destructive-operation governance

### F14 (P1, RESOLVED) — The automatic rollback was both unauthorized and incorrect

The rollback directed `delete .backlog` and `git checkout -- .`
**automatically**. Two independent defects:

1. **Unauthorized breadth.** General authorization to perform the migration
   does not silently authorize destroying a storage root or resetting the whole
   worktree after a failure. `git checkout -- .` also reverts unrelated tracked
   changes, violating surgical preservation.
2. **It does not work.** `.backlogit` is git-tracked (**E1**, 1613 files), so
   after the rename `git checkout -- .` **restores `.backlogit` from HEAD while
   `.backlog` still exists on disk** — manufacturing the exact dual-root state
   **H10** exists to prevent. The prescribed recovery would have *caused* the
   failure mode it was meant to cure.

**Resolution:** added **H16**. Failure recovery is now: verified
`BACKLOGIT_WORKSPACE_DIR` to restore tooling without touching the filesystem →
preserve both roots and the backup → record evidence → **HALT** for explicit
operator approval. Auto-deleting a root, broad `git checkout -- .`, and
guessing root authority are prohibited outright. An approved rollback targets
an **enumerated pathspec list** and a named source/destination copy-back only.
The plan's "Rollback" section is replaced by "Failure recovery"; `T006` and
`129.006-T` now route to H16.

## Persona 12 — Devil's advocate against the correction

*Challenge 1: "This trades a policy violation for a safety regression — the
out-of-tree backup was genuinely safer."*

Rejected. Distance never **closed** either hazard; it merely avoided being
near them, and it was never permissible in the first place. The corrected
design closes both by construction and proves it: the second-root hazard by
name-based resolution semantics plus a negative control (**F10**), and the
git-pollution hazard by three independent layers (**F11**). The corrected
design also surfaced **F12**, a hazard the out-of-tree design would have hidden
rather than removed.

*Challenge 2: "`BACKLOGIT_WORKSPACE_DIR` may not survive a dual-root state, so
H16's step 1 is wishful."*

Rejected on evidence. The validated override returns at
`src/autoharness/backlog_root.py:126`, **before** the ambiguity check at
`:136`; `scripts/ci-topology-check.sh` honours it ahead of its own dual-root
error; and both `=.backlog` and `=.backlogit` resolved cleanly in throwaway
two-root directories at staging time.

*Challenge 3: "H16 halts instead of recovering, leaving the repo unusable."*

Rejected. H16 step 1 restores tooling non-destructively and immediately. The
halt gates **deletion and restoration**, not operability. Halting with both
roots and a verified backup intact strictly dominates halting with a root
already destroyed.

## Correction-pass findings summary

| ID | Severity | Persona | Status |
|---|---|---|---|
| F9 | P1 | Security/containment | RESOLVED — H4 rewritten, G1–G6 verified |
| F10 | P1 | Backlog-root/self-hosting | RESOLVED — G5 + contents-copy, negative control |
| F11 | P1 | Git/VCS | RESOLVED — G3/G4 + H11 |
| F12 | P1 | Git/VCS | RESOLVED — H4 `git clean -x` prohibition |
| F13 | P2 | Reliability | ACCEPTED — H15 + pre-T006 re-assertion + fallback path |
| F14 | P1 | Destructive governance | RESOLVED — H16 replaces automatic rollback |

**Correction-pass verdict: PASS — 0 unresolved P0, 0 unresolved P1.**
Five P1 findings raised, all resolved in the artifacts before this verdict. One
P2 accepted with explicit, gated mitigation. The corrected safety contract is
approved; `138-S` is shippable.

---

## SUPERSEDED — SUBJECT CANCELLED BY OPERATOR SCOPE CORRECTION (2026-08-18)

> **APPEND-ONLY NOTICE. Both verdicts above stand as issued.** No finding,
> severity, resolution or verdict has been altered or withdrawn.

**The PASS verdicts above remain literally true and are NOT retracted.** The
plan they approved was sound. What changed is not the plan's *quality* but its
*premise*.

Per `docs/decisions/2026-08-18-backlogit-legacy-root-support-operator-scope-correction.md`,
the operator has ruled that `.backlogit` remains a supported workspace root,
that `.backlog` is the default for **new workspaces only**, and that
**existing workspaces require no migration**. The reviewed work therefore has
no outcome the operator wants.

**Effect on this review artifact:**

* The verdict line "`138-S` is shippable" is **superseded**. `138-S` is now
  destined for `abandoned`, not for shipping. That sentence was correct at the
  time of writing and is preserved for the record.
* No re-review is required or possible — there is no revised plan to review.
  Cancellation is an operator scope decision, outside review authority.
* The review's findings F1–F13 and the containment/rollback analysis remain
  valid reference material for any future storage-root work.

**This review did not fail, and must not be recorded as a failure** in any
telemetry, learnings, or quality metric. Classify as
`cancelled-by-scope-change`.
