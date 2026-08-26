# Stage — Publication-Review P2 Repair: per-task allowed-state torn refusal (112-F)

- **Date:** 2026-08-05 (local) / 2026-08-06Z
- **Route:** claude-opus-4.8/anthropic/high (Stage-only)
- **Scope:** Stage-only — backlogit + read-only file/git. NO source/template/config
  mutation, no checkpoint mutation, no shipment claim, no branch/build/commit/push/PR.
  Boundary preserved (only `.backlogit/` + `docs/memory/` changed).

## Finding (publication-review P2-3)

112.001-T precondition (iii) — folded from review P1-1 — required the pre-mode
per-item classification to be all-`matched`. But pre-mode `matched` keys on a
SINGLE `expected_status` parameter (`SKILL.md.tmpl` classification table ~line 40;
pre-mode step 3 ~line 159). A valid queued-with-active-work **repair target** has
**mixed** manifest-task statuses by definition (some `active`, some `done`, possibly
some `queued`), so no single `expected_status` can make every task `matched`. The
all-`matched` gate was therefore **UNREACHABLE** — it always refused the exact state
the repair mode exists to repair, contradicting chosen-direction precondition (iii).

## Resolution (honest correction)

Replaced the reuse-pre-mode-`matched` gate with a **PER-TASK ALLOWED-STATE**
classification that defines a **reachable** narrow silently-dropped-claim target:
each manifest task file PRESENT in the location expected for its status (queue for
`queued`/`active`; queue-or-archive for `done`), status within the allowed lifecycle
set `{queued|active|done}`, NO `orphan`, NO missing/malformed/out-of-set/torn anomaly.
Proceed only when EVERY task satisfies the predicate; refuse on ANY per-item anomaly.
Ambiguity refusal is **unweakened** — the torn signal is a per-item ANOMALY, not the
mixedness of statuses. All other invariants preserved: operator-invoked `--confirm`,
single-shot, forward-only queued->active via existing ClaimShipment (061-F),
TOCTOU-explicit detection-not-prevention, no active->queued rollback, malformed-legacy
`blocked` status halt, fail-closed on non-target ambiguity, and the strictly
no-auto-mutation pre/post/safe-close default (their single-`expected_status`
classification is UNCHANGED — no template behavior change).

## Artifacts corrected (contract-only; tasks remain queued/unimplemented)

- **112.001-T** AC 2(iii) — per-task allowed-state predicate; source-of-truth note.
- **112.002-T** AC 3 — mixed-status PROCEED regression guard + per-item anomaly refusal.
- **112.003-T** AC 1/4 — docs preconditions + Addendum D cross-ref.
- **112.004-T** AC 3 — audit records per-task statuses of anomalous items.
- **112-F** IMPL-PLAN precondition (iii) + DoD (3).
- **013-DL** Addendum D (append-only historical correction).
- **112.001-R** decisions/findings (P2-3)/summary/title — VERDICT REMAINS PASS, P0/P1 CLEAR.

## Stage set integrity (revalidated)

- **12 tasks:** 110×3, 111×5, 112×4.
- **14 task-blocks edges, no cycles:** 110:2, 111:8, 112:4.
- **Shipments (task-only, serial):** 117-S={110.001,110.003,110.002};
  118-S={112.001,112.004,112.002,112.003} — 118-S DEPENDS ON 117-S (117-S must ship first);
  119-S={111.001,111.004,111.005,111.002,111.003} — 119-S DEPENDS ON 118-S (118-S must ship first). Chain 117→118→119;
  **only 117-S eligible** (handoff token to Ship). 118-S membership + deps UNCHANGED.
- **Checkpoints:** single active valid Stage checkpoint `checkpoint-20260806-034020.json`
  (unchanged; not mutated). Two 093-S ship-owned actives are unrelated legacy, out of scope.
- **Provenance:** stash 936C68F3→013-DL, E3C25E6D→012-DL intact; no source/template/config mutation.
- **doctor:** all edited artifacts PASS; only pre-existing out-of-scope orphans 048.00{1,2,3}-T.

## Handoff

Uncommitted. Operator owns commit/push. Handoff token to Ship = shipment **117-S**
(sole eligible cursor) once artifacts land on origin/main.

## Correction / reconciliation — final publication-review repair (2026-08-06, append-only)

Route claude-opus-4.8/anthropic/high; Stage-only, backlogit MCP/CLI + read-only file/git; NO
source/template/config mutation; no claim/branch/build/commit/push/PR. A later independent
final publication-review resolved seven findings on the still-uncommitted set and SUPERSEDES the
"Stage set integrity" counts above:

- **P1 (per-task allowed-state, archived-completed):** the per-task predicate was corrected — a
  COMPLETED task is represented as `status: archived` + `archived_status: done` (with valid
  `archived_from` provenance) in `archive/` ONLY, NEVER as a live `status: done`; queued/active
  tasks are UNIQUE LIVE QUEUE records; FAIL CLOSED on duplicate/conflicting/missing/malformed
  provenance. Folded into 112.001..004-T / 112-F / 013-DL Addendum E / 112.001-R (publication-review P1).
- **P1 (owner-agent recovery conflict):** NEW task **111.006-T** updates BOTH owner agent
  templates (Stage + Ship) to the fail-closed lifecycle (no fresh-start on invalid checkpoint;
  resolve only after confirmed successful owner resume; zero-candidate normal startup; explicit
  operator selection; owner `agent`-ownership validation; owner-exclusive restore/resume/prune).
  Hardening H8; deps 111.006→111.001, 111.003→111.006; 002-SP SIXTH addendum; 111.001-R P1-10.
- **P2 (DAG ready-set):** _[ORIGINAL WORDING — SUPERSEDED by the "DAG ready-set predecessor-finished
  predicate (P2-4)" correction section below, which fixes the `active`-as-terminal/non-blocking error;
  retained for append-only provenance]_ defined as LIVE QUEUED shipments only with no unfinished predecessor;
  terminals (active/shipped/abandoned/archived) NEVER included even if dependency-free (110-F/110.001-T/110.003-T/110.002-T/110.001-R P2-3/P2-4).
- **P2 (dependency wording):** 118-S DEPENDS ON 117-S; 119-S DEPENDS ON 118-S (corrected above; the
  earlier "(blocks 117-S)/(blocks 118-S)" phrasing inverted the semantics).
- **P2 (diff.txt):** removed the review scratch file from the publication set.

**Superseding authoritative counts:** **13 tasks** (110×3, 111×**6** {001,002,003,004,005,006}, 112×4);
**16 task-blocks edges** (110:2, 111:**10**, 112:4), no cycles. **119-S** membership (topological):
{111.001, 111.004, 111.005, **111.006**, 111.002, 111.003}. Serial chain 117→118→119, only **117-S**
eligible. Single active valid Stage checkpoint rolled forward from `checkpoint-20260806-034020.json`
to the new final checkpoint (034020 RESOLVED). See the authoritative final memory
`2026-08-05-stage-publication-review-repair-p017-final`.

## Correction / reconciliation — publication-review repair, FIVE findings (2026-08-06, append-only)

Route claude-opus-4.8/anthropic/high; Stage-only, backlogit MCP/CLI + read-only file/git; NO
source/template/config mutation; no claim/branch/build/commit/push/PR. A further independent
publication-review of the still-uncommitted set resolved FIVE findings and SUPERSEDES the P1
per-task representation and the checkpoint pointer above:

- **P1 (completed-task provenance — TWO valid archive representations):** the per-task
  completed-task predicate is broadened. Backlogit persists a completed task in EITHER of two
  valid archive-directory representations, both verified present in this workspace: **(a) TERMINAL
  RELOCATION** — a unique `archive/` record with `status: done` (explicit `archived_status`/
  `archived_from` provenance NOT required; e.g. `002.001-T.md`, and the `112.001-R` review archive
  itself); **or (b) EXPLICIT ARCHIVAL** — `status: archived` + `archived_status: done` + valid
  `archived_from` (e.g. `012-DL.md`). Both require the record be unique in `archive/` with NO
  conflicting live queue record. FAIL CLOSED on any OTHER archived status/provenance, duplicates
  (id in both queue and archive), conflicts (archive alongside a live queue record, or a live
  `status: done` in the QUEUE), missing records, or malformed/absent data. This replaces the earlier
  single-representation predicate ("`status: archived` + `archived_status: done` … NEVER a live
  `status: done`"), which wrongly rejected representation (a). Folded into 112.001-T AC 2(iii),
  112.002-T AC 3, 112.003-T AC 1/4, 112.004-T AC 3, 112-F IMPL-PLAN (iii)/DoD (3), **013-DL Addendum
  F**, and 112.001-R (publication-review P1-2b).
- **P1 (owner lifecycle — cross-role RESOLUTION):** **111.006-T** now explicitly prohibits
  CROSS-ROLE checkpoint RESOLUTION in addition to restore/resume/prune, and REPLACES bulk resolution
  in BOTH owner protocols with **owner-scoped resolution of ONLY the single explicitly operator-
  selected, ownership-matched checkpoint**, and ONLY after a confirmed successful owner resume (no
  bulk sweep, no cross-role, no fresh-start fallback). Verification **111.003-T AC 8** asserts
  explicit operator confirmation/filename selection, matching owner, owner-scoped resolution, no
  bulk/cross-role resolution, and no fresh-start fallback. Aligned on 002-SP SIXTH addendum and
  111.001-R P1-10.
- **P2 (memory banner):** the stale superseded banner in `2026-08-05-stage-third-blocked-review-repair-p017`
  was rolled forward from the RESOLVED `checkpoint-20260806-034020.json` to the current active
  `checkpoint-20260806-053524.json`; the earlier chain (020353 → 023057 → 034020) marked RESOLVED history.
- **P2 (111.001-R summary):** reconciled from 12 tasks/14 edges/checkpoint-034020 to **13 tasks / 16
  edges / checkpoint-053524** with current H8 + 111.006-T facts.
- **P2 (living tracker 34D50F2D):** a superseding provenance annotation was appended (H1-H8, NEW
  111.006-T, updated 119-S membership/order {111.001,111.004,111.005,111.006,111.002,111.003}, and the
  current 111.001-R alignment counts).

**Checkpoint (reconciled):** [SUPERSEDED 2026-08-06 — the in-place amendment described here was
IMPROPER; the pointer has since been rolled forward to `checkpoint-20260806-062506.json` and
`checkpoint-20260806-053524.json` is now RESOLVED. See the "active checkpoint roll to
checkpoint-20260806-062506.json" correction at the end of this file.] the current single active valid
Stage checkpoint is `checkpoint-20260806-053524.json` (amended in place to fold in these five
corrections; NOT rolled to a new file because the recorded structural state — 13 tasks / 16 edges /
task-only manifests / only 117-S eligible / hardening H1-H8 — is unchanged by these contract-prose
refinements); `checkpoint-20260806-034020.json` and the earlier chain remain RESOLVED history. Invariants re-validated: 13 tasks / 16 task-blocks edges /
no cycles / task-only manifests / only 117-S eligible; stash+012-DL/013-DL provenance intact; the
unrelated `.gitmodules` + `references/hve-core`/`references/tokenmasterx` changes remain EXCLUDED from the
publication set (unstaged/untouched); no source/template/config mutation. Uncommitted; operator owns commit/push.

## Correction — active checkpoint roll to `checkpoint-20260806-062506.json` (2026-08-06, append-only)

Route claude-opus-4.8/anthropic/high; Stage-only, backlogit checkpoint lifecycle (`create`/`resolve`)
+ read-only file/git; NO source/template/config mutation; no claim/branch/build/commit/push/PR; NO
hand-edit of checkpoint JSON. `checkpoint-20260806-053524.json` (named above as "current active") was
found to have been **improperly amended in place** after creation — a five-findings repair was appended
directly into the file (`updated_at` later than `created_at`) instead of being rolled to a new
checkpoint. Corrected through the supported lifecycle ONLY: a NEW valid active Stage checkpoint
**`checkpoint-20260806-062506.json`** was created via `backlogit checkpoint create`, carrying the
complete final state and all corrections as first-class content; then `checkpoint-20260806-053524.json`
was **RESOLVED** via `backlogit checkpoint resolve`. The current **sole active valid Stage checkpoint is
`checkpoint-20260806-062506.json`**; the full chain `020353 → 023057 → 034020 → 053524` is RESOLVED
history. Structural state UNCHANGED (13 tasks / 16 task-blocks edges / task-only manifests / only 117-S
eligible / hardening H1-H8). The two 093-S `ship`-owned actives remain unrelated legacy, out of scope.
Uncommitted; operator owns commit/push.

## Correction — DAG ready-set predecessor-finished predicate (P2-4, 2026-08-06, append-only)

Route claude-opus-4.8/anthropic/high; Stage-only, backlogit MCP/CLI + read-only file/git; NO
source/template/config mutation; no checkpoint mutation, no claim/branch/build/commit/push/PR. A
surgical publication-review correction fixed a remaining FACTUAL P2 in the 110-F family: the
"P2 (DAG ready-set)" bullet above listed `active` among terminal/non-blocking states. That is
WRONG — an `active` shipment is IN-PROGRESS work, NOT a terminal state and NOT non-blocking.
CORRECTED predicate (aligned everywhere across 110-F, 110.001-T, 110.002-T, 110.003-T, 110.001-R):
a LIVE `queued` candidate is ready ONLY when EVERY predecessor is completed in a genuine
no-longer-blocking terminal closure with valid `shipped`/`done` closure; a `queued` OR `active`
predecessor is UNFINISHED and BLOCKS its dependent; an `abandoned`, malformed, or unknown
predecessor state follows the EXISTING FAIL-CLOSED semantics (still-blocking / not-ready, never
casually treated as terminal-ready). The ready-set itself still contains ONLY live `queued`
candidates (never an `active`/`shipped`/`abandoned`/`archived` shipment even if dependency-free).
Added an explicit REGRESSION acceptance/test — "active predecessor blocks queued dependent" —
to 110.001-T AC 5 (reader) and 110.003-T AC 6 (CLI render), reflected in 110-F DoD (5) and
110.001-R (P2-4). Contract-prose only: task/shipment counts, task-blocks edges, shipment manifests,
and the active Stage checkpoint are UNCHANGED. Tasks remain queued/unimplemented; the unrelated
`.gitmodules`, references, `_stage.agent.md`, mem1.txt, and mem2.txt are EXCLUDED/untouched.
Uncommitted; operator owns commit/push.

## Correction — active checkpoint roll to `checkpoint-20260806-072043.json` (2026-08-06, append-only)

Route claude-opus-4.8/anthropic/high; Stage-only, supported backlogit checkpoint lifecycle
(`create`/`resolve`) + read-only file/git; NO source/template/config mutation; no
claim/branch/build/commit/push/PR; NO hand-edit of checkpoint JSON. The P2-4 DAG ready-set correction
above was recorded as **contract-prose only** and explicitly left `checkpoint-20260806-062506.json`
UNCHANGED — so that checkpoint kept the stale F3 wording that mislabeled `active` as a
terminal/non-blocking predecessor state. Because checkpoints are never hand-edited, the fix was
propagated through the supported lifecycle ONLY: a NEW valid active Stage checkpoint
**`checkpoint-20260806-072043.json`** was created via `backlogit checkpoint create`
(`created_at == updated_at`), carrying the identical structural state plus the corrected F3
predecessor-finished predicate (a `queued` OR `active` predecessor is UNFINISHED and BLOCKS its
dependent; only a valid `shipped`/`done` closure is no-longer-blocking; `abandoned`/malformed/unknown
FAILS CLOSED; ready-set = live `queued` candidates only) as first-class content; then
`checkpoint-20260806-062506.json` was **RESOLVED** via `backlogit checkpoint resolve`. The current
**sole active valid Stage checkpoint is `checkpoint-20260806-072043.json`**; the full chain
`020353 → 023057 → 034020 → 053524 → 062506` is RESOLVED history. Every "current sole active valid
Stage checkpoint is `checkpoint-20260806-062506.json`" statement above is superseded by this
correction. Structural state UNCHANGED (13 tasks / 16 task-blocks edges / task-only manifests / only
117-S eligible / hardening H1-H8). Uncommitted; operator owns commit/push.

> **[SUPERSEDED 2026-08-06 — active-checkpoint roll to `checkpoint-20260806-083118.json`]** Every "current / sole active valid Stage checkpoint is `checkpoint-20260806-072043.json`" statement in this document is SUPERSEDED. The Copilot PR #304 repair rolled the sole active Stage checkpoint forward to **`checkpoint-20260806-083118.json`** (`072043` RESOLVED; full chain `020353 → 023057 → 034020 → 053524 → 062506 → 072043` is RESOLVED history) and the decomposition to **14 tasks** (110×3, 111×7 incl new **111.007-T**, 112×4) / **19 task-blocks edges** (110:2, 111:13, 112:4); 112-F is RE-SCOPED report-only; **936C68F3 stays ACTIVE** (cleanup-triggering `source_stash_id` replaced with the non-cleanup `source_stash_tracker_id` — Ship must leave 936C68F3 active). See `docs/memory/2026-08-06-stage-copilot-pr304-five-finding-repair.md` and memory `2026-08-06-stage-copilot-pr304-provenance-cleanup-083118`.

> **[FURTHER ROLL 2026-08-06 — active-checkpoint roll to `checkpoint-20260806-150505.json`]** The `checkpoint-20260806-083118.json` named in the superseded note above is itself now RESOLVED/superseded via the supported `backlogit checkpoint create`+`resolve` lifecycle. The current SOLE active valid Stage checkpoint is **`checkpoint-20260806-150505.json`**, which corrects the F3 112-F provenance from the cleanup-triggering `custom_fields.source_stash_id` to the NON-cleanup `custom_fields.source_stash_tracker_id: 936C68F3` (936C68F3 stays ACTIVE; Ship MUST NOT archive it). Structural state (14 tasks / 19 task-blocks edges / manifests / review verdicts) UNCHANGED. `checkpoint-20260806-083118.json` preserved as RESOLVED history.
