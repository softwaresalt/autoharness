---
shipment: 135-S
feature: 126-F
tasks: [126.001-T, 126.002-T, 126.003-T, 126.004-T, 126.005-T, 126.006-T, 126.007-T]
feature_pr: 344
closure_pr: 345
merge_commit: 9851cc3defb8ba295940064d201bda006b15d7ff
merged_at: "2026-08-15T20:50:38Z"
reviewed_head: 125a916d4820821e9d9179e9c6b97b8dbea60a48
closure_status: READY
compaction_status: degraded
feature_terminal_status: done
feature_archived_status: done
---

# 135-S / 126-F Post-Merge Closure — Adopt the backlogit `.backlog` Storage Root

Shipment `135-S` implemented covering feature `126-F`: adopting backlogit
1.9.0's `.backlog` storage root across the autoharness product surface,
making the surface directory-agnostic with `.backlog`-first precedence
(`BACKLOGIT_WORKSPACE_DIR` -> `.backlog` -> `.backlogit`), mirroring
upstream's fail-closed both-exist detection, keeping legacy `.backlogit`
workspaces valid, and defaulting new installs to `.backlog`. Explicitly
excluded (operator-gated, never dark-mode automation): migrating this
repository's own `.backlogit` directory, and changing
`.autoharness/backlog-registry.yaml`'s directory value.

`126-F` is a root feature (no `parent_id`) with exactly 7 children
(`126.001-T` through `126.007-T`), all of which are this shipment's manifest,
so `126-F` is fully covered by `135-S` alone — qualifying for the P-015
verified fully-covered-root cascade close path (see Backlog Archival below).

This session picked up an **already-shipped-but-not-yet-closed** shipment:
`135-S`/`126-F` had already been merged (PR #344) and safe-closed via the
cascade path in a prior session, leaving the resulting `.backlogit/archive/*`
and `.backlogit/logs/*` mutations uncommitted on
`post-merge/adopt-the-backlogit-backlog-storage-root`. This closure continues
the same explicit `DARK_MODE_ACTIVE` bounded dark-factory continuation
record, ordered scope `[134-S, 135-S, 136-S]`, covering `135-S` only. `136-S`
was not claimed, edited, or touched during this session.

## Merge Confirmation

- PR **#344** ("feat: Adopt the backlogit .backlog storage root (135-S /
  126-F)") merged to `main` at `2026-08-15T20:50:38Z` with merge commit
  `9851cc3defb8ba295940064d201bda006b15d7ff`. Confirmed via
  `git log --pretty=%P -1`: two parents (`5ab716008132fffc07762d5914a68fe259e5a98a`
  prior `main` tip + `125a916d4820821e9d9179e9c6b97b8dbea60a48` feature
  branch HEAD), preserving the P-009 merge-commit strategy. Confirmed
  ancestor of `origin/main` (this session's own `HEAD`/`origin/main`/`main`
  are all exactly `9851cc3d`).
- Repo merge-strategy settings (P-009), verified this session:
  `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false` — only "Create a merge commit" is possible.
- Reviewed HEAD `125a916d4820821e9d9179e9c6b97b8dbea60a48` matches the
  feature-branch parent of the merge commit exactly.
- CI checks on PR #344 at merge: `ci gate`, `detect code changes`,
  `pipeline-topology (ambient)`, `test` — all **pass**.

## Review-Fix History (PR Lifecycle, PR #344)

Three rounds of Copilot review recorded on PR #344
(`copilot-pull-request-reviewer` comments at 19:39, 20:05, 20:32, each
followed by an author fix-commit round at 20:02, 20:27, 20:40, with a final
Copilot pass at 20:45 before merge), consistent with the 3-cycle Copilot-fix
budget. This shipment's own implementation review history lives on PR #344
itself and is not re-litigated here; this closure's own review scope is the
backlog-archival/bookkeeping delta below (see Local Review below).

## Backlog State Inspection (this closure session)

On starting this session, the working tree contained the already-applied
cascade-close mutation for `135-S`:

- `.backlogit/queue/135-S.md` -> `.backlogit/archive/135-S.md` (renamed,
  staged): `status: archived`, `archived_status: shipped`,
  `commit: 9851cc3defb8ba295940064d201bda006b15d7ff`.
- `.backlogit/archive/126-F.md`: `status: archived`, `archived_status: done`.
- `.backlogit/archive/126.00{1..7}-T.md`: each `status: archived`,
  `archived_status: done`, `commit: 9851cc3d...`.
- Matching `commit_tracked` + `archived` events appended to each item's
  `.backlogit/logs/*.jsonl`.

**Cascade verification performed this session** (equivalent to the
shipment-reconcile Cascade Close Sub-Procedure's own checks, since the
mutation itself pre-dated this session):

- `archived_ids` present in the working tree matches exactly the manifest's
  task items + qualifying feature member + the shipment record itself:
  `{126.001-T, 126.002-T, 126.003-T, 126.004-T, 126.005-T, 126.006-T,
  126.007-T, 126-F, 135-S}` — nothing more, nothing less. No sibling task or
  unrelated feature was archived.
- `parent_id: 126-F` verified present, unchanged, on all 7 archived tasks.
- No `queue/126*` entries remain (confirmed via `Get-ChildItem`) — no
  descendant was requeued/detached, ruling out the destructive
  `backlogit_ship_shipment` requeue-and-detach failure mode.
- Predecessor `134-S` untouched throughout: verified still
  `archived_status: shipped`, unchanged, at closure time.

**Anomaly found and excluded**: an **untracked**
`.backlogit/logs/018-DL.jsonl` claimed `commit_tracked` +
`archived` events for deliberation record `018-DL` (referenced by `126-F`'s
body as "Deliberation: 018-DL", but **not** a manifest member of `135-S`).
Cross-checking against the actual artifact showed `.backlogit/archive/018-DL.md`
does not exist and `.backlogit/queue/018-DL.md` is unchanged
(`status: queued`, byte-identical to the committed version) — the claimed
archive never actually happened; this is torn log state for an
out-of-manifest artifact. **This closure does not commit
`.backlogit/logs/018-DL.jsonl`** (left untracked, unresolved) and does not
touch `018-DL.md` in any way — resolving a deliberation record's lifecycle
state is Stage's domain, not Ship's, under the role boundary. See compound
learning
`docs/compound/2026-08-15-torn-archive-log-entry-without-file-mutation-must-not-be-committed.md`.
Recorded as an explicit follow-up (P2, non-blocking) below.

## TOPOLOGY_GATE note

`autoharness gate pipeline-topology --mode agent --shipment 135-S --phase
lifecycle --json` was run at the start of this closure session and returned
`exit_code: 1` / `LIFECYCLE_NO_ACTIVE_SHIPMENT` (`active_shipment_ids: []`).
This is the **expected** postcondition, not a violation: the gate's
`lifecycle` phase requires exactly one active shipment matching the target
as a precondition for invoking the safe-close mutation itself, but `135-S`'s
safe-close/cascade had already completed in a prior session (see above) —
there is no shipment left to be "active." This closure does not re-invoke
`shipment-reconcile` (which already ran); this checkpoint therefore gates an
action (invoking shipment-reconcile) this session never takes, and does not
block the remaining bookkeeping/PR work.

## Local Review

Adversarial local review of the closure delta (backlog archival/log
mutations + this closure's own new docs) performed this session, multi-
persona (correctness/provenance, role-boundary, security/secrets):

- **P0/P1**: none found.
- **P2** (follow-up, non-blocking): the `018-DL` torn-log anomaly above —
  recommend Stage investigate why `backlogit archive` (or equivalent)
  logged an `archived` event for a deliberation-type artifact without
  performing the corresponding file mutation, and decide (as a triage
  action, out of Ship's scope) whether/when `018-DL` should actually be
  archived once its linked feature has shipped.
- No secrets, credentials, or raw operator content present in any new file
  in this closure delta.

## Validator Evidence

This closure changes only `.backlogit/*` backlog-state files and
`docs/*` (compound learning, closure artifact, session memory) — no source
code, schema, or template changed. Full local build/test suite is **not
applicable**; recorded per the docs/backlog-only exemption. A CLI smoke
check was still run for baseline confidence:

| Area | Verdict | Evidence |
|---|---|---|
| CLI smoke test | PASS | `.venv\Scripts\autoharness.exe --help` exits 0, prints CLI help text |
| Backlog cascade-close invariant (manual, see above) | PASS | `archived_ids` exact-match, `parent_id` preserved, no residual `queue/126*` entries |
| Full local build/test suite | N/A | Docs/backlog-only closure delta; no source changed |

## Runtime Verification

No runtime surface is touched by this closure delta (backlog-state files and
documentation only). Per `.autoharness/workspace-profile.yaml`
`runtime_validation.validator_manifest`, the only declared surface is `cli`;
the CLI smoke check above satisfies that surface's probe
(`cli-help`, `expected_signal` met). No additional validator evidence is
applicable.

## Invariants Preserved

- The safe-close/cascade mutation already applied before this session is
  verified byte-for-byte consistent with the P-015 verified fully-covered-root
  cascade contract (exact `archived_ids`, preserved `parent_id`, no
  protected-set violation).
- No deliberation-record (`018-DL`) content or lifecycle state was modified
  by this closure.
- No commit in this closure targets `main` directly; all closure commits
  land on `post-merge/adopt-the-backlogit-backlog-storage-root`.

## Pre-Deploy Audits and Deployment Path

Docs/backlog-only change; released by merge-only deployment to `main`. No
runtime service, background job, deployment surface, or public API is
introduced or altered. No pre-deploy audit beyond the CLI smoke check above
is applicable.

## Monitoring and Healthy Signals

No dedicated monitoring is required for a backlog-archival/documentation
closure. Healthy state is simply `135-S` and `126-F` (+ its 7 tasks) showing
`archived_status: shipped`/`done` with no residual `queue/126*` entries, and
`.backlogit/logs/018-DL.jsonl` remaining excluded from tracked history until
Stage resolves the anomaly.

## Failure Signals and Rollback

If `.backlogit/logs/018-DL.jsonl` is later found committed anywhere without
a corresponding, deliberately-reviewed Stage archival of `018-DL.md`, treat
that as a regression of the exclusion decision made here — the log-only
event should not have been laundered into history. Rollback for this
closure itself is a plain revert of the closure merge commit (additive
backlog-state + docs only, no destructive migration).

## Releasability Evidence

`closure_status: READY`. Merge, review (PR #344 review history + this
session's own closure-delta review), and backlog-state invariant evidence
are complete. No runtime surface is introduced or altered by this closure.
One explicit, non-blocking P2 follow-up is recorded (the `018-DL` anomaly,
owned by Stage).

## P-020 Compaction

`compaction_status: degraded`. The mandatory `compact-context` invocation was
attempted at post-merge closure, but no installed/executable runtime skill
exists in this environment — only the repository's own authored template at
`templates/skills/compact-context/SKILL.md.tmpl` (this self-hosting repo
does not resolve `.github/skills/compact-context/SKILL.md`), consistent with
the `130-S`/`121-F` and `134-S`/`125-F` closure precedents. This session's
own manual consolidation — one compound-learning document and one
session-memory document, both written during this same closure — constitutes
the bounded, cheap Tier-1 consolidation of this shipment's fresh memory that
a working `compact-context` tool would otherwise perform. Recorded as
attempted-and-degraded, non-blocking, per P-020.

## Backlog Archival

- Feature `126-F` and its 7 tasks (`126.001-T` through `126.007-T`) were
  closed via the **P-015 verified fully-covered-root cascade** path in a
  prior session (verified in this closure per Backlog State Inspection
  above): `archived_ids` matched exactly
  `[126.001-T, 126.002-T, 126.003-T, 126.004-T, 126.005-T, 126.006-T,
  126.007-T, 126-F, 135-S]` — nothing extra. `parent_id: 126-F` verified
  preserved on all 7 archived tasks. Feature archived with
  `archived_status: done`; all 7 tasks archived with `archived_status: done`.
- Shipment `135-S` archived with `archived_status: shipped` and commit
  `9851cc3defb8ba295940064d201bda006b15d7ff`.
- Predecessor `134-S` untouched throughout: verified still
  `archived_status: shipped` at closure time (already closed by its own
  prior closure).
- `.backlogit/logs/018-DL.jsonl` (untracked, out-of-manifest, torn log
  state) is **explicitly excluded** from this closure's commit. See Backlog
  State Inspection above and follow-up below.

## Follow-Ups

- **P2 (non-blocking, owned by Stage)**: investigate and resolve the
  `018-DL` torn-log anomaly — a log entry claims `018-DL` was archived, but
  the artifact file was never actually moved/updated. Decide whether
  `018-DL` (the deliberation tracker for this now-shipped feature) should be
  archived, and if so, perform that archival deliberately as a Stage
  triage action, not as a byproduct of this Ship closure.
