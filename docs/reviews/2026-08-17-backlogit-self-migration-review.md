---
title: Backlogit self-migration plan and decision review
description: Multi-persona adversarial review of the self-migration deliberation, plan and hardening
doc_type: review
source: docs/reviews/2026-08-17-backlogit-self-migration-review.md
status: pass
date: 2026-08-17
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

The out-of-tree backup contains full telemetry and memory history. Auto-deleting
it on success would destroy the only recovery artifact at the moment it is most
likely to be needed.

**Resolution:** added **H15** — disposal is operator-gated, never automatic,
never before merge and `T009` verification.

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
(**H9**); the out-of-tree backup is the primary recovery path.

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
