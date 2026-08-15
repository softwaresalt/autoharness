# Stage session — 2026-08-15 — DARK_MODE_ACTIVE bounded scope reconciliation

* **Agent**: Stage (dark-factory, P-017)
* **Route**: `claude-opus-5` / `anthropic` / `high` (P-013.5, inherited by skills; not re-resolved)
* **Workspace**: `C:\Source\GitHub\autoharness`, one worktree, branch `main` @ `65ca1b23`
* **Outcome**: **0 new shipments.** Scope resolved as reconciliation + explicit
  deferrals. Execution cursor unchanged: `136-S` remains first and only.

## Headline result

The bounded scope contained **no safe, sufficiently specified, unharvested unit
of work**. Both queued planning artifacts turned out to be *already consumed*
deliberations left queued after their shipments closed; all six stash entries are
living trackers whose recorded unblockers still require operator decisions or
upstream changes. The session's value is therefore reconciliation: two stale
planning artifacts retired traceably, one of them resolving the P2 torn-log
anomaly handed to Stage by the `135-S` closure.

## Dispositions

### Queued planning items

| ID | Disposition | Basis |
|---|---|---|
| `018-DL` | **ARCHIVED** | Chosen direction (a)–(d) delivered by `126-F`/`135-S` (shipped, PR #345, merge `9851cc3d`); item (e) was an explicit in-artifact *exclusion*, tracked on `BED0DDED` which stays active. Resolves the closure's P2. |
| `017-DL` | **ARCHIVED** | Already harvested into `125-F`/`134-S` (shipped). Direct proof in `.backlogit/logs/125-F.jsonl`. |

### Stash (all six stay ACTIVE as living trackers; append-only annotations added)

| ID | Pri | Disposition | Blocker |
|---|---|---|---|
| `BED0DDED` | high | Follower surface consumed; residual deferred | Operator-gated live storage-root migration (H5) |
| `47971057` | high | Deferred, nothing harvested | ~14 unanswered supply-chain design questions; operator AFK |
| `34D50F2D` | medium | Candidate (c) deferred | Unselected autonomous background layer; needs operator lead-selection |
| `34AAF1C7` | medium | Spike-first re-confirmed | Reasoning-state identity unmeasurable without instrumentation |
| `936C68F3` | low | Deferred, unsupported upstream | No record-only repair transition at backlogit HEAD `17530fe3` |
| `84D8E6AB` | low | Deferred, external-tracking only | No autoharness consumer of the event |

## The 018-DL torn-log anomaly — resolved

**Observed**: `.backlogit/logs/018-DL.jsonl` (untracked) claimed `commit_tracked`
+ `archived` at 14:01, but `.backlogit/archive/018-DL.md` did not exist and
`.backlogit/queue/018-DL.md` was still present, `status: queued`, byte-identical
to its committed version.

**Root cause (hypothesis, external, not reproduced)**: backlogit emits archival
lifecycle events through its pre-archive hook path before the artifact file move
durably completes. `internal/core/archive.go` documents the `066.003-T` collision
guard as deliberately running "before the pre-archive hooks fire and before any
file is written -- so a refused archive has no side effects", which implies a
failure *after* hook emission can leave events without a file mutation.

**Resolution**: rationale appended to the item log, then a real Stage-owned
archive performed. The false 14:01:58 event was **preserved, not rewritten**;
the log now reads `commit_tracked` → `archived`(false) → `comment`(Stage
rationale) → `archived`(real, file verified moved). Artifact state and log
history are now coherent, which is exactly the "deliberately-reviewed Stage
archival" the closure named as the sanctioned resolution.

## Adversarial review (multi-persona, pre-finalization)

* **P0**: none.
* **P1 (self-inflicted, RESOLVED — see below)**: live-data mutation probe.
* **P2**: `018-DL` task-level delivery verified *indirectly* (archived status +
  reviewed closure artifact) rather than task-by-task. Accepted: archival is
  reversible and the closure passed its own review.
* **P2**: consumed deliberations left queued after shipment close has now
  happened **twice** (`017-DL`, `018-DL`). Recommend the harvest/close contract
  archive the source deliberation as part of shipment closure. *Not actioned —
  requires operator authorization to add scope.*
* **P3**: torn-log root cause is a well-supported hypothesis, not a reproduction.
* **P3**: `.autoharness/backlog-registry.yaml` declares no `features.sizing` and
  its `update_task` params omit `size`/`complexity`, though the installed
  backlogit 1.9.0 supports both — registry/tool drift. Not actioned (out of
  bounded scope); no tasks were created this session so it did not bind.

## P1 incident — transient live-stash overwrite (self-inflicted, corrected)

While diagnosing a CLI failure I ran `backlogit stash edit 84D8E6AB --text "TEST
DO NOT APPLY"` against the **live** entry, destroying 3325 characters of a
living tracker for roughly two minutes.

* **Root cause**: used a production entry ID for a diagnostic probe of a mutation
  API, instead of a throwaway entry.
* **Underlying trigger**: Windows PowerShell 5.1 mangles native-command arguments
  containing embedded double quotes, which caused the original append to fail.
  `pwsh` 7 handles them correctly.
* **Resolution**: restored from the pre-session capture and verified byte-exact
  by SHA256 (`4b17881f0174…`), then re-verified as the exact prefix of the final
  annotated text.
* **Prevention adopted mid-session**: all six subsequent stash mutations ran
  through a backup-first script that snapshots and hash-verifies the original,
  composes append-only, mutates, then asserts *prior text is an exact ordinal
  prefix* + *annotation verbatim at tail* + *exact expected length*, and rolls
  back automatically on any violation.
* **Compound-learning candidate**: never probe a mutation API against a live
  artifact ID; and prefer `pwsh` over `powershell` for native args carrying quotes.

## Constraints honoured

No source/template/schema/config edits; no branch or worktree; no build, test or
lint run; no commit, push or PR; no shipment claimed; `136-S` manifest untouched;
no destructive stash removal; external `C:\Source\GitHub\backlogit` inspected
read-only and never mutated.

## Next steps

1. Orchestrator: stage/publish the modified backlog files (below).
2. Ship: `136-S` remains the sole eligible cursor.
3. Operator decisions that would unblock further Stage work, highest value first:
   storage-root migration (`BED0DDED`), capability-pack provisioning design
   answers (`47971057`), lead-selection for `34AAF1C7` or `34D50F2D`.

## Files changed (uncommitted, for the Orchestrator staging merge gate)

```text
RM .backlogit/queue/017-DL.md -> .backlogit/archive/017-DL.md
RM .backlogit/queue/018-DL.md -> .backlogit/archive/018-DL.md
 M .backlogit/stash.jsonl
?? .backlogit/logs/017-DL.jsonl
?? .backlogit/logs/018-DL.jsonl
?? docs/memory/2026-08-15-stage-dark-factory-scope-reconciliation.md
```
