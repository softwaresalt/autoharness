# Stage — Final Publication-Review Repair (P-017 uncommitted set)

- **Date:** 2026-08-05 (local) / 2026-08-06Z
- **Route:** claude-opus-4.8/anthropic/high
- **Scope:** Stage-only — backlogit MCP/CLI + read-only file/git. NO source/template/config
  mutation, no shipment claim, no branch/build/commit/push/PR. Boundary preserved
  (only `.backlogit/` + `docs/memory/` changed).

## Findings resolved

### P1 — zero-candidate recovery semantics (crash-resumption)
The recovery contract previously treated **zero active recovery checkpoints** as a
fail-closed / operator-handoff condition (over-broad "cannot be uniquely selected").
Corrected to an explicit **two-branch** contract:

1. **Zero active recovery candidates** ⇒ **no recovery needed** ⇒ the Orchestrator
   **continues normal orchestration**. This is the expected steady state — NOT a
   failure and NOT an operator handoff.
2. **One or more valid candidates** ⇒ the recovery gate engages: **explicit operator
   selection by filename (never auto-pick)** → validate CheckpointV1 `agent` ownership
   (`stage`/`ship`) → Orchestrator routes restore/resume/prune **exclusively to the
   owning agent** (never restores/resumes/prunes Stage/Ship-owned state directly) → **fail closed
   AMONG EXISTING CANDIDATES** on missing/invalid/ambiguous ownership or a
   non-unique/ambiguous selection. Zero candidates never fails closed.

**Aligned artifacts:** 111.001-T (AC #1/#2 + implementation-notes), 111.003-T
(verify + docs AC #1/#3 + notes), 111-F (IMPL-PLAN, DoD #3, hardening H7), 002-SP
(FOURTH correction addendum, append-only), 111.001-R (FOURTH re-review P1-7 in
decisions/findings/summary), stash 34D50F2D living-tracker note.

### P2 — memories.json durable superseded facts
`.backlogit/memories.json` carried stale facts (11 tasks, 12 edges, missing
111.005-T, "already-installed" overlay). Reconciled via the supported
`save_memory` workflow, append-only provenance preserved:

- Marked `2026-08-05-stage-dark-factory-remaining-p017` **SUPERSEDED** (original text
  preserved).
- Marked `2026-08-05-stage-second-blocked-review-repair-p017` **SUPERSEDED** (original
  text preserved).
- Marked `2026-08-05-stage-third-blocked-review-repair-p017` **SUPERSEDED** (original
  text preserved).
- Marked `2026-08-06-stage-blocked-review-repair-p017` **SUPERSEDED** (original text
  preserved).
- Published one authoritative final memory
  `2026-08-05-stage-publication-review-repair-p017-final`, which supersedes ALL four
  prior operational repair records above. No prior operational record remains
  unsuperseded — only this final contract is authoritative.

## Authoritative final state
- **12 tasks:** 110-F ×3 {001,002,003}; 111-F ×5 {001,002,003,004,005}; 112-F ×4 {001..004}.
- **14 task blocks edges:** 110:2, 111:8, 112:4 — no cycles.
- **Shipments (task-only):** 117-S={110.001,110.003,110.002}; 118-S={112.001,112.004,112.002,112.003};
  119-S={111.001,111.004,111.002,111.003,**111.005**}. Serial chain 117→118→119;
  only **117-S eligible** (handoff token to Ship).
- **Overlay** `.github/instructions/backlogit.instructions.md` **currently ABSENT**
  (no first-party manifest artifact); **installed by 111.005-T** (standard single
  `artifacts[].checksum`).
- **Hardening:** 110-F none / 112-F H1–H8 / 111-F H1–H7.
- **Reviews:** 110.001-R / 112.001-R / 111.001-R **PASS, P0=0 / P1=0**.
- **Checkpoints:** single valid active Stage checkpoint
  `checkpoint-20260806-034020.json` (supersedes/resolves
  `checkpoint-20260806-023057.json`, now RESOLVED — which itself superseded
  `checkpoint-20260806-020353.json`); two 093-S ship-owned actives are
  unrelated legacy, out of scope. **[SUPERSEDED 2026-08-06 — the current sole active valid
  Stage checkpoint is now `checkpoint-20260806-062506.json`; `034020` (and the later `053524`)
  are RESOLVED history. See the final "active checkpoint roll to checkpoint-20260806-062506.json"
  correction at the end of this file.]**

## Handoff
Uncommitted. Operator owns commit/push. Handoff token to Ship = shipment **117-S**
(only eligible cursor) once artifacts land on origin/main. Pre-existing orphaned
048.00{1,2,3}-T are out of scope (untouched).

## Correction — never-direct contract alignment (2026-08-06, append-only)
Route claude-opus-4.8/anthropic/high; Stage-only, no source/template/config, no
claim/branch/build/commit/push/PR. A later pass found this publication record (and the
peer durable surfaces: stash 34D50F2D candidate-(d) note, the authoritative final memory
`2026-08-05-stage-publication-review-repair-p017-final`, and the archive/002-SP correction
addendum) still stated the Orchestrator never-direct clause over **restore only**, even
though P1-8 had already widened the backlog artifacts (111-F DoD #3 / hardening H7,
111.003-T verify AC#1(a)/docs AC#3, 111.001-T notes) to all three operations. Corrected
here so no active authoritative surface remains restore-only: on explicit unique operator
checkpoint selection + CheckpointV1 `agent`-ownership validation (`stage`/`ship`), the
Orchestrator routes **restore/resume/prune** exclusively to the owning agent (stage-owned ⇒
Stage, ship-owned ⇒ Ship) and **NEVER directly RESTORES, RESUMES, or PRUNES** Stage/Ship-owned
state; fail closed AMONG EXISTING CANDIDATES on missing/invalid/ambiguous ownership or a
non-unique/ambiguous selection; ZERO active candidates ⇒ no recovery needed ⇒ normal
orchestration continues (not a failure/handoff). The inline P1 clause above was updated in
place and this subsection appended for provenance. Conforms to 111-F DoD#3/H7, 111.003-T,
and 111.001-R P1-8. Also in this pass: deliberation **013-DL** linked `informs → 112-F`,
moved queued→active→done, and archived (deliberation only; 112-F/112.001..004-T and 118-S
remain queued/intact; 117-S remains sole eligible). 111.003-T verifier coverage and
111.002-T hosting detail strengthened (H3 resolve-after-owner-resume; H5/C3 degraded
fallback with named host sections/artifacts). No scope/decomposition/edge change: 12 tasks /
14 task-blocks edges intact; task-only manifests; single active Stage checkpoint retained.

## Correction — active checkpoint reference roll (2026-08-06, append-only)
Route claude-opus-4.8/anthropic/high; Stage-only, no source/template/config, no
claim/branch/build/commit/push/PR; no checkpoint mutation in this pass. The **Checkpoints**
bullet above previously named `checkpoint-20260806-023057.json` as the single valid active
Stage checkpoint. That reference is now STALE: the 2026-08-06 final cleanup pass rolled
`checkpoint-20260806-023057.json` (now **RESOLVED**) forward to
`checkpoint-20260806-034020.json`, which is the current **sole active valid Stage
checkpoint** (chain `020353` → `023057` → `034020`; both predecessors RESOLVED). The inline
bullet was corrected in place and this subsection appended for provenance. Verified against
live checkpoint state: `checkpoint-20260806-034020.json` (agent=stage, active) is the only
active Stage checkpoint; the two 093-S `ship`-owned actives are unrelated legacy, out of
scope. No scope/decomposition/edge change (12 tasks / 14 task-blocks edges intact). **[SUPERSEDED
2026-08-06 — `034020` was subsequently rolled to `053524` and then to the current sole active valid
Stage checkpoint `checkpoint-20260806-062506.json`; both `034020` and `053524` are RESOLVED history.
See the final "active checkpoint roll to checkpoint-20260806-062506.json" correction at the end of
this file.]**

## Correction — final publication-review repair, seven findings (2026-08-06, append-only)

Route claude-opus-4.8/anthropic/high; Stage-only, backlogit MCP/CLI + read-only file/git; NO
source/template/config mutation; no claim/branch/build/commit/push/PR. An independent final
publication-review resolved seven findings on the still-uncommitted set; this SUPERSEDES the
counts/membership stated above in this record:

1. **P1 per-task allowed-state (archived-completed):** a COMPLETED manifest task is
   `status: archived` + `archived_status: done` in `archive/` ONLY (never live `status: done`);
   queued/active tasks are UNIQUE LIVE QUEUE records; FAIL CLOSED on
   duplicate/conflicting/missing/malformed provenance. (112.001..004-T, 112-F, 013-DL Addendum E,
   112.001-R publication-review P1.)
2. **P1 owner-agent recovery conflict:** NEW task **111.006-T** updates BOTH owner agent
   templates (Stage `_stage.agent.md.tmpl` + Ship `_ship.agent.md.tmpl`) to the fail-closed
   lifecycle — no fresh-start on invalid checkpoint; resolve only after confirmed successful owner
   resume; zero-candidate normal startup; explicit operator selection; owner `agent`-ownership
   validation; owner-exclusive restore/resume/prune. Hardening H8; deps 111.006→111.001 and
   111.003→111.006 (verify AC#8); 002-SP SIXTH addendum; 111.001-R P1-10 (seventh alignment).
3. **P2 DAG ready-set (predecessor-finished predicate; CORRECTED — the earlier wording that listed
   `active` among terminal/non-blocking predecessor states was WRONG, see the DAG-semantics correction
   section below):** a LIVE `queued` shipment enters the ready-set ONLY when EVERY predecessor is
   completed in a genuine no-longer-blocking terminal closure (valid `shipped`/`done` closure); a
   `queued` OR `active` predecessor is UNFINISHED and BLOCKS its dependent (`active` is IN-PROGRESS
   work, NOT terminal and NOT non-blocking); an `abandoned`, malformed, or unknown predecessor state
   FAILS CLOSED (still-blocking / not-ready). The ready-set itself contains ONLY live `queued`
   candidates — never an `active`/`shipped`/`abandoned`/`archived` shipment even if dependency-free
   (110-F, 110.001/003/002-T, 110.001-R P2-3/P2-4).
4. **P2 active checkpoint predates final repairs:** a NEW valid active Stage checkpoint carrying the
   final corrections/counts was created; `checkpoint-20260806-034020.json` RESOLVED and superseded;
   all current pointers rolled forward.
5. **P2 119-S authoritative order:** topological — {111.001, 111.004, 111.005, **111.006**, 111.002, 111.003}.
6. **P2 dependency wording:** 118 depends on 117; 119 depends on 118 (never inverted).
7. **P2 diff.txt:** removed from the publication set.

**Superseding authoritative state:** **13 tasks** (110×3, 111×**6** {001,002,003,004,005,006}, 112×4);
**16 task-blocks edges** (110:2, 111:**10**, 112:4), no cycles; task-only manifests
117-S={110.001,110.003,110.002}, 118-S={112.001,112.004,112.002,112.003},
119-S={111.001,111.004,111.005,111.006,111.002,111.003}; serial chain 117→118→119, only **117-S**
eligible = handoff token to Ship; hardening 110-F none / 112-F H1-H8 / 111-F H1-H8; reviews
110.001-R/112.001-R/111.001-R PASS, P0/P1 clear. Uncommitted; operator owns commit/push.

## Correction — active checkpoint roll to `checkpoint-20260806-062506.json` (2026-08-06, append-only)

Route claude-opus-4.8/anthropic/high; Stage-only, backlogit checkpoint lifecycle (`create`/`resolve`)
+ read-only file/git; NO source/template/config mutation; no claim/branch/build/commit/push/PR; NO
hand-edit of checkpoint JSON. Finding P2-4 above ("active checkpoint predates final repairs") had
rolled the pointer to `checkpoint-20260806-053524.json`, but that checkpoint was later found to have
been **improperly amended in place** after creation (a five-findings repair was appended directly into
the file — `updated_at` later than `created_at` — instead of being rolled to a new checkpoint).
Corrected through the supported lifecycle ONLY: a NEW valid active Stage checkpoint
**`checkpoint-20260806-062506.json`** was created via `backlogit checkpoint create`, carrying the
complete final state and all corrections (13 tasks, 16 task-blocks edges, serial chain 117→118→119 with
only 117-S eligible, F1 two-representation archive/owner provenance predicate, F2 111.006-T/H8
owner-agent fail-closed lifecycle with cross-role resolution prohibited + owner-scoped resolution + no
fresh-start fallback, F3 DAG live-queued ready-set, F5 119-S order, F6 depends-on direction, F7
diff.txt removed) as first-class content; then `checkpoint-20260806-053524.json` was **RESOLVED** via
`backlogit checkpoint resolve`. The current **sole active valid Stage checkpoint is
`checkpoint-20260806-062506.json`**; the full chain `020353 → 023057 → 034020 → 053524` is RESOLVED
history. All prior inline "current active" checkpoint statements in this record are superseded by this
correction. Structural state UNCHANGED. Two 093-S `ship`-owned actives remain unrelated legacy, out of
scope. Uncommitted; operator owns commit/push.

## Correction — DAG ready-set predecessor-finished predicate + active-checkpoint roll to `checkpoint-20260806-072043.json` (2026-08-06, append-only)

Route claude-opus-4.8/anthropic/high; Stage-only, supported backlogit checkpoint lifecycle
(`create`/`resolve`) + read-only file/git; NO source/template/config mutation; no
claim/branch/build/commit/push/PR; NO hand-edit of checkpoint JSON. Two coupled defects were closed:

1. **F3 DAG ready-set semantics.** Finding 3 ("P2 DAG ready-set") above, `checkpoint-20260806-062506.json`,
   and the authoritative `7findings` memory all still described the ready-set with wording that listed
   `active` among terminal/non-blocking predecessor states. That is **WRONG** — an `active` shipment is
   IN-PROGRESS work, NOT a terminal state and NOT non-blocking. The P2-4 predecessor-finished predicate had
   already been folded into the 110-F backlog artifacts and
   `docs/memory/2026-08-06-stage-publication-review-p2-per-task-allowed-state.md`, but was never propagated
   to the checkpoint or this record. **CORRECTED predicate (now aligned everywhere):** a LIVE `queued`
   candidate is ready ONLY when EVERY predecessor is completed in a genuine no-longer-blocking terminal
   closure with valid `shipped`/`done` closure; a `queued` OR `active` predecessor is UNFINISHED and BLOCKS
   its dependent; an `abandoned`, malformed, or unknown predecessor state FAILS CLOSED
   (still-blocking / not-ready, never casually treated as terminal-ready); the ready-set itself still
   contains ONLY live `queued` candidates (never an `active`/`shipped`/`abandoned`/`archived` shipment even
   if dependency-free). Finding 3's bullet above has been inline-corrected accordingly; the original
   wording is explicitly superseded by this section.

2. **Active-checkpoint roll.** Because `checkpoint-20260806-062506.json` carried the stale F3 wording, the
   correction could not be an in-place edit (checkpoints are never hand-edited). Through the supported
   lifecycle ONLY: a NEW valid active Stage checkpoint **`checkpoint-20260806-072043.json`** was created via
   `backlogit checkpoint create` (`created_at == updated_at`), carrying the identical structural state plus
   the corrected F3 predecessor-finished predicate as first-class content; then
   `checkpoint-20260806-062506.json` was **RESOLVED** via `backlogit checkpoint resolve`. The current
   **sole active valid Stage checkpoint is `checkpoint-20260806-072043.json`**; the full chain
   `020353 → 023057 → 034020 → 053524 → 062506` is RESOLVED history. All prior "current active" checkpoint
   statements in this record (including the `062506` roll section above) are superseded by this correction.

**Invariants UNCHANGED:** 13 tasks (110×3, 111×6 incl. 111.006-T, 112×4) / 16 task-blocks edges
(110:2, 111:10, 112:4), no cycles; task-only manifests 117-S={110.001,110.003,110.002},
118-S={112.001,112.004,112.002,112.003} (deps 117-S), 119-S={111.001,111.004,111.005,111.006,111.002,111.003}
(deps 118-S); serial chain 117→118→119, only **117-S** eligible = handoff token to Ship; hardening
110-F none / 112-F H1-H8 / 111-F H1-H8; reviews 110.001-R/112.001-R/111.001-R PASS, P0/P1 clear. Exactly one
active valid Stage checkpoint (`checkpoint-20260806-072043.json`); two 093-S `ship`-owned actives remain
unrelated legacy, out of scope. Only `.backlogit/` + `docs/memory/` changed; the unrelated `.gitmodules`,
references, `_stage.agent.md`, mem1.txt, mem2.txt are EXCLUDED/untouched. Uncommitted; operator owns commit/push.
