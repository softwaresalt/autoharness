---
doc_type: closure-compaction-summary
compaction_phase: phase-3-closure-compaction
compacted_on: "2026-08-26"
period_start: "2026-08-08"
period_end: "2026-08-09"
shipments: [121-S, 122-S, 123-S]
features: [113-F, 114-F, 115-F]
source_artifacts:
  - docs/archive/closure/121-S-113-F-post-merge-closure.md
  - docs/archive/closure/122-S-114-F-post-merge-closure.md
  - docs/archive/closure/123-S-115-F-post-merge-closure.md
---

# Closure Summary — 121-S through 123-S: Model-Routing Hierarchy Fix, Capability-Pack Runtime Detection & Deterministic Resumption Advisory (2026-08-08/09)

Consolidates three post-merge closure records: model-routing hierarchy
correctness + dynamic session-start reload (`113-F`, F02FD596 + E8B5B3C5;
final shipment closing `113-F` to terminal state), bounded capability-pack
runtime detection (`114-F`, tracker `47971057`; final shipment of the
dark-mode sequence `120-S → 121-S → 122-S`), and the deterministic
`next_eligible` resumption advisory (`115-F`, 33CC445C Phase 2). Source
artifacts are preserved verbatim at `docs/archive/closure/`.

## Shipments & Features Covered

| Shipment | Feature | Tasks | PR (+ closure PR) | Merge commit (+ closure) | Merged at | `closure_status` | `feature_terminal_status` |
|---|---|---|---|---|---|---|---|
| 121-S | 113-F | 5 | #316 (+ #317) | `db8630b6ce7b83bebf9a0006940fcccf01bf3ee0` (+ `9a3dc6a27724f57e58d858376e42c1042d83a574`) | 2026-08-08T18:49:15Z | READY | done |
| 122-S | 114-F | 3 | #318 (+ #319) | `d923820e29473cb24e0c4c7d76070b4d811d55a5` (+ `f0c3538cad7a954e21e41790fd9907b54c67019c`) | 2026-08-08T20:23:52Z | READY | done |
| 123-S | 115-F | 3 | #323 | `5fa949ad5f05f35690f44e9577ab8d2bb25fd7ae` | 2026-08-09T22:01:16Z | READY | done |

All entries carry `compaction_status: done` (verbatim from source
frontmatter). All merges verified as genuine two-parent merge commits
(P-009). This group is the second half of the dark-mode ordered sequence
`120-S → 121-S → 122-S` (120-S covered in the 2026-08-06 group summary),
plus the independent, single-shipment dark-mode scope `123-S`.

## What Was Verified, and Verdict per Shipment

- **121-S / 113-F** — model-routing hierarchy fix (nested per-role
  escalation, F02FD596) + dynamic session-start reload (E8B5B3C5). Fixed a
  real schema-versioning bug found in review round 5: the
  `harness-config/1.0.0.schema.json` mirror was being mutated in place —
  fixed by restoring `1.0.0` and publishing a new `1.1.0` mirror (compound
  doc: `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`).
  Feature `113-F` closed to terminal state after this shipment (its only
  feature). **Verdict: READY.**
- **122-S / 114-F** — capability-pack runtime detection, bounded (tracker
  `47971057`, confirmed still **ACTIVE** as a "partially-consumed living
  tracker" for deferred provisioning work, annotated during this same
  session). **Final shipment of the dark-mode sequence `120-S → 121-S →
  122-S`.** Fixed a shell-pipeline exit-status-masking bug in
  `deploy-harness.sh`'s version-probe logic (2 Copilot threads on the `.sh`
  file, 1 on a weak test; compound doc:
  `docs/compound/2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md`).
  **Verdict: READY.**
- **123-S / 115-F** — deterministic `next_eligible` resumption advisory
  (33CC445C Phase 2), layered over 117-S's DAG-readiness gate. Single-
  shipment dark-mode scope. 2 rounds of Copilot review (round 1: 3 threads —
  a vacuous tie-break test, a `next_eligible_detail` field-scoping deviation,
  a doc branch-numbering inconsistency; round 2: clean). Compound doc:
  `docs/compound/2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md`.
  Feature `115-F` closed to terminal state after this shipment (its only
  feature). **Verdict: READY.**

## Checkpoint Anomaly Disposition (Operator-Authoritative) — Preserved Verbatim

**121-S and 122-S both independently investigated the same underlying
anomaly** in historical checkpoint files, at the operator's direction. This
is distinct from and must not be conflated with the **120-S-created
labeled stash** documented in the 2026-08-06 group summary (that stash held
120-S's own out-of-scope model-route-rename/checkpoints changes, which
121-S superseded via its own fresh commits — that stash's content became
moot, not the subject of this anomaly investigation).

- **121-S**: root-caused the apparent re-trigger of two historical
  checkpoint files to dirty-worktree repairs having been moved into a
  **different, larger remainder stash**,
  **`ab16544a1636651d2368825d08cbd5e7c26ec755`** — confirmed
  byte-identical/untouched throughout 121-S's own session. This remainder
  stash contains 5 tracked + 3 untracked checkpoint JSON files plus the
  "BED0DDED deliberation" doc. It is explicitly a **separate, pre-existing
  debris accumulation**, not the 120-S-created labeled stash.
- **122-S**: the operator named **4 specific historical files**; all were
  root-caused to the **same** `ab16544a...` stash-isolation persistence
  bug, and confirmed **not touched** during 122-S's session either.

**This is one continuous anomaly investigation spanning both shipments,
concerning the single stash `ab16544a1636651d2368825d08cbd5e7c26ec755`,
confirmed untouched at both checkpoints (121-S and 122-S).** It remains
distinct from the 120-S labeled stash referenced in the prior group summary.

## Healthy Signals

- All three merges are genuine two-parent commits; P-009 preserved.
- Two independent real bugs were caught by Copilot review and fixed with
  dedicated compound-learning docs: the schema-mirror in-place mutation
  (121-S) and the shell-pipeline exit-status masking (122-S).
- Both features under this group (`113-F`, `115-F`) reached terminal status
  cleanly within their own single shipment, with no cascade corruption.
- The `ab16544a...` stash was independently confirmed untouched across two
  separate sessions (121-S and 122-S), giving high confidence in the
  operator-authoritative disposition.

## Failure Signals Observed

- **121-S**: the pre-existing schema-mirror-mutated-in-place defect (fixed
  this session, not a regression introduced by 121-S itself).
- **122-S**: the pre-existing shell-pipeline exit-status-masking defect in
  `deploy-harness.sh` (fixed this session).
- **123-S**: a vacuous tie-break test and a doc branch-numbering
  inconsistency (both fixed in round 1; round 2 was clean).
- No unresolved regressions carried out of this group.

## Monitoring, Validation Windows & Rollback Triggers

- **121-S**: rollback = revert `db8630b6...`. The new `1.1.0` schema mirror
  is additive (the `1.0.0` mirror was restored, not removed), so rollback is
  safe. Validation window: immediate post-merge 2026-08-08.
- **122-S**: rollback = revert `d923820e...`. Bounded capability-pack
  detection; the `47971057` tracker remains ACTIVE for deferred work beyond
  this shipment's bounded scope. Validation window: immediate post-merge
  2026-08-08.
- **123-S**: rollback = revert `5fa949ad...`. Advisory-only, read-only
  resumption cursor; no destructive migration. Validation window: immediate
  post-merge 2026-08-09.

## Unresolved Follow-Ups Carried Forward

1. **Tracker `47971057`** (122-S) — confirmed **still ACTIVE** as a
   "partially-consumed living tracker" for deferred capability-pack
   provisioning work beyond this bounded shipment's scope. Not closed by
   this group.
2. **Stash `ab16544a1636651d2368825d08cbd5e7c26ec755`** — the operator-
   authoritative Checkpoint Anomaly Disposition confirms this stash remains
   untouched and its disposition (what to do with the debris it contains) is
   not resolved within these three closure records — it is documented, not
   consumed.
3. **34D50F2D candidates a/c** (from the 119-S/`111-F` crash-resumption
   protocol, see the 2026-08-06 group summary) remain deferred/ACTIVE — not
   addressed by any shipment in this group.
4. No shipment-specific residual-risk items were recorded beyond the
   above; 121-S, 122-S, and 123-S each closed with their review findings
   fully resolved (no declined/partial dispositions in this group).
