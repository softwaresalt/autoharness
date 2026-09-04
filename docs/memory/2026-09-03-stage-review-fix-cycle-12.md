# Stage session memory — SHIP-10 review-fix cycle 12

Date: 2026-09-03
Agent: Stage
Branch: `chore/stage-159-167-publication`
Base HEAD at session start: `b3156cb5`
Scope: Stage/backlog/docs only — no Git/source/test/config/workflow
implementation, no PR, no shipment claim, no worktree.

## Outcome

Fresh multi-persona plan review over the changed artifacts: **PASS**, zero
current P0 and zero current P1.
Publication readiness: **READY_WITH_FOLLOWUPS** carrying `76EBDE6D`,
`0B83AC8F`, `60C207F1`.

## The decisive finding — P-004 is impracticable on this workspace

Cycle 11 claimed P-004's red-phase gate "costs nothing to honour". That was a
false reconciliation of a policy this plan has no authority to reconcile. The
measurement, taken statically (Stage does not run suites):

1. `tests/` holds **106 files / 2,025 test functions**.
2. `.github/workflows/ci.yml` **line 112** runs P-004's exact command
   `PYTHONPATH=src python -m unittest discover -s tests` as the authoritative
   required gate, so it **exits 0** on the default branch.
3. P-004 requires that same command to exit **non-zero with expected failure
   markers for every test function**.
4. (2) and (3) cannot both hold without deliberately breaking 2,025 passing
   tests.

A **second, independent** obstruction: a CHARACTERIZATION case passes by
construction, so any mixed RED/CHARACTERIZATION suite fails "every test
function" regardless of the pre-existing 2,025. This survives even if those
tests were removed.

Resolution shape — defer, do not reinterpret. The harness-architect (P-004's
named producer) authors the red case and confirms the red phase; `harness-ready`
is applied only on the policy's own evidence; **Ship must not claim any task in
this shipment before it carries `harness-ready`**; Ship halts per P-002's
violation action; the gate stays fail-closed. Captured as P-021 reliability
follow-up **`76EBDE6D`** — separate policy work, outside SHIP-10.

## Why `RECORD` differences cannot prove installed orphan cleanup

`RECORD` inventories what a distribution *contains*. A member's absence is
silent on whether a prior install's copy is deleted, overwritten or left in
place during an upgrade — that is installer *execution* behaviour, observable
only by performing a real installed upgrade. T10 therefore verifies the
installer's **input** and never its execution; the real upgrade and orphan
cleanup remain deferred in full to `60C207F1`.

## Evidence model — subject and cardinality

`owner_tasks` (sorted, duplicate-free array) replaces the singular `owner_task`,
and `artifact_subject` (`static | wheel | plugin`) is added. The subject mapping
is a **total function of the ledger's own Owner column**, so it can never drift
and is never self-asserted: `{T7}`→wheel, `{T8}`→plugin, `{T7,T8}`→both,
everything else→static. The six dual-owner cases are #25, #26, #28, #29, #30,
#43. Primary key `(case_name, observation_phase, artifact_subject)`; coverage is
**106 record slots**, cross-checked by the identity
`owner assignments × 2 phases = 53 × 2 = 106`. Case count unchanged at **47**.

## Current metrics (all recomputed and reconciled this session)

| Metric | Value |
|---|---|
| Cases | 47 unique (33 RED-FIRST, 14 CHARACTERIZATION) |
| Owner assignments | 53 |
| Record slots | 106 (static 36, wheel 32, plugin 38) |
| RED-FIRST ordering paths | 34 |
| DAG | 19 nodes, 51 edges — plan table ↔ frontmatter exact match both ways |
| Live sizes | S 8 / M 11 |
| Derived `168-S` rollup | M 12 / S 8 (includes archived `160.019-T` — P2) |
| Shipment manifest | 20 members |
| Mandatory durable outputs | 10 |
| Pre-change captures | 6 across four tasks |
| Canonical plan | 1,088 lines / 56,659 bytes |

## Open P2

1. **Plan length** — 1,088 lines against a <1,000 target. A duplicate-definition
   sweep confirms one statement per subject for every load-bearing definition,
   so the overrun is required contract text, not redundancy.
2. **Rollup archived-child caveat** — `backlogit shipment get 168-S` resolves
   `160-F` into every child including retired `160.019-T`, so the derived
   histogram reads `M:12, S:8` over 20 members while the live 19-task histogram
   is `M:11, S:8`. A backlogit rollup behaviour, not a plan or manifest defect.

## Next steps

* `76EBDE6D` must be dispositioned as separate policy work before this shipment
  can pass the `harness-ready` gate. Until then Ship halts at that gate — this
  is the honest current state, not a plan defect.
* Ship owns claim and execution; Stage's staging path for SHIP-10 is complete.

## Pointers

* Canonical plan: `docs/plans/2026-09-03-minimal-copilot-plugin-payload-plan.md`
* Review history (all cycles):
  `docs/reviews/2026-09-03-minimal-copilot-plugin-payload-plan-review-history.md`
* Previous cycle: `docs/memory/2026-09-03-stage-review-fix-cycle-11.md`
