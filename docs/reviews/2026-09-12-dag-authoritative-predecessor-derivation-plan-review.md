---
title: "Plan review — DAG-authoritative predecessor derivation (cycle 4, authorized final review; + PR review-fix cycles 1-2)"
description: "Multi-persona adversarial plan review of docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md, gating harvest. Plan-review cycle 4 was the operator-authorized final narrow correction cycle. Subsequent PR review-fix cycles 1 and 2 (staging PR #448) are recorded in their own sections and consume none of the plan-review cycles."
doc_type: review
source: docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md
date: 2026-09-13
plan_path: docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
plan_revision: 6
review_cycle: 4
pr_review_fix_cycle: 2
pr: 448
decision: PASS
---

# Plan Review — DAG-Authoritative Predecessor Derivation (cycle 4)

**This is the operator-authorized FINAL review. There is no further fix loop.**

Review cycles 1–3 consumed the three normal correction cycles in the Stage
stop-condition table. The operator subsequently authorized **one additional narrow
correction cycle**. A prior attempt at that cycle made **no artifact changes**, so
the cycle remained available and is consumed here. This review evaluates **plan
revision 4** and the backlog records corrected alongside it.

It supersedes the cycle-3 review of plan revision 3 (that text remains in git
history). Cycle 3 returned PASS with 0 P0 / 0 P1; the operator then raised a
**fifteen-item coherent correction set**, including a ruling on the previously
blocking item 3. Revision 4 applies all fifteen in one pass. The *Operator
Correction Verification* section checks each item individually; the persona passes
are an independent re-review, not a restatement of that checklist.

## Operator Ruling Adopted — Item 3

The operator adopted **ruling (a)**: the empirically verified `SAFE_CLOSE` posture
for `173-S` is **valid and non-blocking**. `CASCADE` is **unavailable by design**
because archived off-manifest descendants remain. No reparenting, no invented
holding feature, and no re-addition to `173-S` is authorized. Every claim that
safe close is impossible is corrected. This review verifies that ruling is
recorded consistently and that no artifact still asserts the contrary.

## Dispatch Capability and Declared Degradation

```text
dispatch_mode: single-agent-declared-degradation
TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass
TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass
TOOL_DEGRADED: agent-engram (MCP unified_search / impact_analysis) — declared fallback: documented CLI parity surface + file-based grep/view over src/ and .github/
TOOL_DEGRADED: agent-intercom — declared fallback: no phase broadcast; operator visibility via session report only
TOOL_DEGRADED: graphtor-docs — declared fallback: direct read of docs/compound/ and docs/decisions/
TOOL_OK: backlogit (MCP) — index synced; shipment, task, and stash reads verified live
ENGRAM: reachable and workspace-bound (C:\Source\GitHub\autoharness); sync run this session (215 files, 0 errors)
```

No subagent dispatch surface and no alternate model route are available in this
session, so this is a **declared** degradation, not a silent one (P-012). Every
persona below was applied inline against its rubric — no persona was skipped, and
no finding was downgraded because of the degradation. Reviewer route:
`claude-opus-5`/`anthropic`/`high` (same as caller).

Claims in this review that depend on current source or agent-contract behaviour
were verified by **direct read in this cycle**, not carried over:

* `src/autoharness/gates/topology.py` — `ShipmentState` (L91–98), `_tuple_of_str`
  and `_ARTIFACT_ID_PATTERN` (L331), the shipment frontmatter parser (L560–600),
  `closure_complete` (L654), `_prior_shipment_id` (L1433–1469).
* `.github/agents/_orchestrator.agent.md` — L239–241 (route-to-Ship eligibility
  check) and L261–263 (cursor advance).
* `.github/agents/_ship.agent.md` — L227–229, L254–255, L258, L282–283.
* Live `.backlogit` records, manifest, dependency edges, and stash.

## Severity Scale

| Sev | Meaning | Gate effect |
|---|---|---|
| P0 | Plan cannot be executed as written; would produce incorrect or unsafe behaviour | BLOCK |
| P1 | Material defect; execution would produce a known-wrong intermediate state or violate a policy | BLOCK |
| P2 | Should be corrected; does not prevent execution | Record + handle |
| P3 | Advisory / stylistic | Record |

## Persona Findings

### Constitution Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | Principle II (Test-First, NON-NEGOTIABLE): **strengthened by the item-1 correction.** Cycle 3 marked a *passing characterization* as a strict expected-failure. Under `xfail(strict=True)` that case would XPASS and **fail the suite** — T1 could not have ended green. Reclassifying it as characterization (C5) and moving strictness onto genuinely-absent behaviour restores test-first integrity rather than relaxing it. | OK — resolves item 1 |
| — | Principle VIII (Explicit Safety Modes): the fail-closed posture is unchanged and the genesis narrowing survives intact. Item 8's "no defer hatch" for numeric claim-path residue keeps the strongest gate in the plan. | OK |
| — | Principle V (Structured Observability): `predecessor_source` on every payload plus genesis-disqualifier reporting still make each block explainable from output alone. The removal of the ledger does **not** reduce observability — the audit still reports; it simply does not persist. | OK |
| — | Principle VI (Single Responsibility): the T8 sources+mirrors merge remains a legitimate exception to width isolation — one artefact in two locations, not two concerns. Item 10's removal of stale separate-task wording removes the last suggestion of a follow-up commit. | OK — resolves item 10 |
| — | P-001 role separation: Stage authored planning, documentation, and backlog artefacts only this cycle. **No source, test, template, or config file was modified.** The one non-backlog file touched (`docs/bugs/2026-09-11-…`) is documentation, and only its frontmatter and transfer note changed. | OK |
| — | P-021 C1/C6: both deferred-scope-expansion entries now **explicitly cite P-021 C1** as their capture basis and retain `REQUIRES DELIBERATION: yes` under C6. The C1 citation is not decorative — each entry states *why* its surface is outside the running unit's authorized scope. | OK — resolves item 11 |
| — | P-016: no spike/research worktree was created; all work occurred on `chore/stage-173-S`. No parallel branch, no implementation worktree. | OK |

### Python Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | **Item 1 is a genuine latent defect and is correctly diagnosed.** Verified by direct read: `topology.py` contains **zero** `labels` references and `ShipmentState` has **no** `labels` field. Therefore `[dag-root, topology-gate]` parses cleanly *today* — nothing reads it, so nothing can reject it. The former N7a ("labels parse and raise nothing") describes **current passing behaviour**, making it a characterization, not an expectation. The genuinely-absent behaviour is *preservation* and *root classification* (N7) and *malformed-label rejection* (N8), and strictness now sits there. | OK — resolves item 1 |
| — | **Constrained expected-failure reasons close a real RED-laundering hole.** Without scoping, a fixture error, a collection error, or an unknown-phase error satisfies a strict xfail just as well as the absent behaviour does — the test would go "red for the wrong reason" and then flip green on an unrelated fix. Every strict marker is now scoped to its specific assertion and exception type. | OK — resolves item 1 |
| — | Item 8 is correct and load-bearing: `ShipmentState` **retains a validated immutable `labels` tuple** and root classification **derives from it**, rather than each call site re-parsing frontmatter. The validator remains **labels-specific** — reusing `_tuple_of_str` would brick every labelled record including `173-S` itself, since `_ARTIFACT_ID_PATTERN` (`^\d+(?:\.\d+)*-[A-Z]+$`) rejects `dag-root` and the helper raises `BacklogUnavailableError`. | OK — resolves item 8 |
| — | The historical directional-numeric cases are correctly re-posed as **audit-output expectations** rather than pins on a retired claim-path helper, and numeric claim-path residue is a **blocking failure with no defer hatch**. This prevents the retired predicate from being resurrected as a tested contract. | OK — resolves item 8 |
| — | Item 2: the audit is now a **pure read-only report**. Removing the ledger removes a write path from a gate whose defining property is that it does not mutate — and removes a second source of truth about backlog state that could itself drift from the backlog it describes. Verified: no persistence claim, no durable-artifact requirement, and no future-remediation field survives in T3, T6, or the feature record. | OK — resolves items 2, 9 |
| P3-1 | The shared **derivation** helper's module location remains unspecified — `topology.py` or a new module. | Advisory, carried. 165.005-T requires the executor to *state* the choice in the task record; either is acceptable. |
| P3-3 | Expected-failure tests must be **strict** xfail, and must now additionally be **reason-constrained**. | Already required by 165.001-T and restated in 165.002-T and 165.004-T. No change needed. |

### Test Strategy Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | **The characterization/RED split is now correct in both directions.** Malformed **dependency** behaviour already exists and is pinned as characterization; malformed **label** behaviour does not exist and is strict-xfail. Cycle 3 had these partially conflated, which would have produced one guaranteed-XPASS case and one untested gap simultaneously. | OK — resolves items 1, 12 |
| — | Closure variants are applied **only to explicit predecessors** — and in revision 4 they are removed from the parity matrix entirely (item 5), leaving closure pinned solely by the characterization lock in T1 (C2). `declared_root`, `genesis`, and `unsequenced` have no predecessor for closure to apply to, so no coverage is lost. | OK — resolves items 5, 12 |
| — | **Edge-less states are asserted exactly once each**, so no fixture carries two states indistinguishably. Ordering assertions are explicitly required to be non-vacuous, per the recorded prior learning on vacuous tiebreak tests. | OK — resolves item 12 |
| — | Green-per-task is preserved across the rearrangement: T1 ends green (characterizations pass, strict-xfails fail as specified); T2 flips its own set; T4 lands parity strict-xfail; T5 flips. No task ends red. | OK |
| — | Per-case disposition remains mandatory for all five historical cases and bulk deletion is still forbidden, so re-posing them as audit-output expectations did not create a deletion loophole. | OK |
| P3-2 | `audit_sequencing` as a phase name still sits alongside `pre_claim`/`post_claim`/`lifecycle`/`ambient`, which are lifecycle *positions* rather than activities. | Advisory, carried. Registered in `VALID_PHASES` only, never `SCOPED_PHASES`, so it cannot acquire an active-target requirement. |

### Scope Boundary Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | **Item 5 is the most consequential scope correction in this cycle.** Cycle 3 still permitted read-only reuse of `closure_complete` through the shared helper. That was insufficient: read-only reuse would still have shipped `173-S` as an installed **consumer** of the exact producer/consumer naming surface `FD0CCB42` exists to redefine — forcing that deferred work to negotiate compatibility with a dependent it never agreed to. Removing closure entirely from T4, T5, and every acceptance criterion is the only disposition that leaves `FD0CCB42` free. | OK — resolves item 5 |
| — | Verified by grep across the plan, decision, feature, shipment, and all eight task records: **no** acceptance criterion in `173-S` discovers, evaluates, or asserts parity over closure evidence. `FD0CCB42` now carries an explicit **exclusive ownership** statement. `pre_claim`'s own pre-existing per-explicit-predecessor closure check is untouched. | OK — resolves item 5 |
| — | Item 13: the rollback claim no longer depends on a gate-owned ledger. The migration record is the **version-controlled operator commit and its diff** — reviewable, attributable, and already protected by repository history. This is *stronger* evidence than a gate-written ledger, and requires the gate to own no write path. Data-first ordering is preserved, and the never-committed case is narrowed honestly to manual reconstruction. | OK — resolves items 2, 13 |
| — | Item 14: stale counts, task lists, and cumulative references corrected. The plan's §4 task table no longer labels `165.008-T` as "T7"; the T-label↔ID rule is stated explicitly and records that **there is no T7** because `165.007-T` is archived. Revision and cycle references updated to rev 4 / cycle 4 throughout. | OK — resolves item 14 |
| P2-A | The shipment `size_composition.members` rollup still lists archived, off-manifest `165.007-T` and `165.010-T`, because it derives members from `parent_id` children rather than from `custom_fields.items`. The manifest itself is correct at 9 items. | **Externalized**, not absorbed: stash `9AA34143`, now recording a third consecutive-cycle confirmation and a second consumer of the same defect (the close-path classifier). Fixing it requires modifying backlogit, outside this shipment. The `173-S` record carries a "known tool artefact" note so a future reader does not "reconcile" it by re-adding an archived task. |
| — | Scope fences hold: `86498B64`, `9B582824`, `97B28746`/`50434138`, `58A85283` all remain separate; backlogit is not modified; closure semantics are untouched and now exclusively owned elsewhere. | OK |

### Architecture Strategist

| Sev | Finding | Disposition |
|---|---|---|
| — | **Item 3 / ruling (a) is correctly recorded and the false claims are retracted.** Verified empirically: the workspace's own close-path classifier over the `173-S` manifest returns per-item `SAFE_CLOSE`, naming `165.007-T` and `165.010-T` as archived off-manifest descendants of `165-F`. `SAFE_CLOSE` is the **designed fail-closed fallback and a supported close path** — its availability means `173-S` *can* be closed. The prior artifacts' claim that both close paths were impossible was simply wrong, and it is now retracted in the plan, the decision, `165-F`, `173-S`, and `9AA34143`. | OK — resolves item 3 |
| — | `CASCADE` is correctly characterized as **unavailable by design** rather than broken. It would require re-adding the two archived tasks to the manifest, which is forbidden by D4 and item 5. `_enumerate_descendants` walks the full transitive tree, so intra-subtree reparenting could not help either — and reparenting is not authorized in any case. | OK — resolves item 3 |
| — | Provenance and off-manifest status of `165.007-T` and `165.010-T` are **preserved exactly**. Verified: neither record's `parent_id` was mutated, neither appears in `custom_fields.items`, no holding feature was invented, and both remain in `.backlogit/archive/`. | OK — resolves item 3 |
| — | The genesis narrowing (G2/G3/G4, single-snapshot, cardinality-1) survives revision 4 unchanged and remains the strongest correctness property in the design. | OK |
| P2-B | The `dag-root` label still has **no mechanical enforcement**: any actor who can edit a shipment record can declare a root. | **Accepted with handling, and now correctly *narrowed*** (item 6). Revision 4 states the claim at its true strength: `dag-root` is a version-controlled, review-gated declaration inside the repository trust boundary — **auditable but not mechanically permission-enforced, and not a security boundary**. Every "no escape hatch" / "technically prevented" formulation is removed. Overstating this would have taught readers a guarantee the implementation does not provide, which is a worse failure than the gap itself. Mechanical enforcement needs a backlogit-side permission model — outside this shipment. |

### Agent-Native Parity Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | **Item 4 corrects a defect that would have deadlocked the shipment at the pipeline's first gate.** Verified by direct read: `_orchestrator.agent.md` L239–241 runs `--phase pre_claim` as a route-to-Ship eligibility check **before Ship is invoked at all**. The cycle-3 two-use grant covered only Ship's two runs (L227–229, L254–255), so the authorization would have been exhausted-by-absence — consumed by an invocation nobody had counted — before Ship ever started. Three audited invocations (U0/U1/U2) is the correct count. | OK — resolves item 4 |
| — | The **cursor-advance** check at `_orchestrator.agent.md` L261–263 is correctly **excluded**: it evaluates `{next_shipment_id}`, a different shipment, and is outside a `173-S`-only grant by construction. Including it would have silently widened the grant to a second shipment. | OK — resolves item 4 |
| — | Per-invocation conditions remain genuinely constraining: **sole token** `PREDECESSOR_NOT_SHIPPED`, inferred predecessor **exactly `172-S`**, exact reviewed HEAD and manifest match, and no other violation. Each is independently checkable from the gate payload plus git state, so no agent can satisfy them by assertion. Any mismatch **expires the authority**. | OK — resolves item 4 |
| — | **Post-claim retry with force is explicitly unauthorized.** The `CLAIM_NOT_OBSERVED` path (L282–283) genuinely re-runs `pre_claim`, so an unbounded grant would have silently covered a fourth use. Naming it and declaring authority exhausted closes a real, reachable path. | OK — resolves item 4 |
| — | Sources and installed mirrors remain one atomic unit (item 10), and the historical split is now recorded as a *note*, not an instruction — with an explicit "do not re-derive a second commit from this note" guard. | OK — resolves item 10 |
| P3-4 | 165.008-T sits at `M` (~2h), the top of the 2-hour bound, after absorbing the mirror work. | Advisory. The estimate is defensible because the contract text is *authored once* and mirrored within the same working context. If execution exceeds budget, the correct response is escalation inside `173-S`, **not** re-splitting sources from mirrors — that would reinstate the drift window. |

### Security / Safety Lens

| Sev | Finding | Disposition |
|---|---|---|
| — | The three-use force grant is a **safety improvement over an unsatisfiable two-use grant**. An unsatisfiable authorization is the more dangerous artefact: it pressures the executing agent to halt mid-protocol or silently stretch one grant across uncounted invocations. Naming all three makes the real cost visible and auditable. | OK — resolves item 4 |
| — | Expiry is defined on **both** the success and the mismatch edge, and the mismatch edge halts to the operator rather than degrading to retry. Combined with self-liquidation via `declared_root` once T2 lands, the grant cannot outlive its purpose. | OK |
| — | `--force` semantics themselves remain unchanged; no agent may self-authorize; the grant remains `173-S`-only with no precedent. | OK |
| — | **Item 6 is a safety finding, not a stylistic one.** A document that claims an unenforced rule is mechanically enforced is more dangerous than one that admits the gap, because readers stop looking for the hole. Narrowing the `dag-root` claim to "auditable, review-gated, not a security boundary" is the honest and safer formulation. | OK — resolves item 6 |
| — | **Item 7 removes a traceability hazard.** The bug artifact previously carried a `source:` path that did not resolve locally and presented source-workspace paths as if they did. It now has valid local frontmatter, a `source:` pointing at its own committed path, and an explicit `external_provenance` block naming `softwaresalt/backlogit#438` plus the origin path, recorded as **not resolving here**. The analysis body is preserved unchanged; historical meaning is intact. | OK — resolves item 7 |
| — | Removing the gate-owned ledger (item 2) also removes a **write path** from a read-only gate — a net reduction in blast radius, not merely a documentation change. | OK — resolves items 2, 13 |

## Operator Correction Verification (fifteen-item coherent set)

| # | Operator correction | Resolution | Where |
|---|---|---|---|
| 1 | T1 N7a is a passing characterization; strict expected-failure only for genuinely absent behaviour; constrained failure reasons | Verified empirically (`topology.py` has zero `labels` references; `ShipmentState` has no `labels` field), so label parsing succeeds trivially today. Former N7a reclassified as characterization **C5**; strictness moved to **N7** (preservation + root classification) and **N8** (malformed-label rejection). Every strict marker is scoped to its assertion and exception type, so setup/collection/unknown-phase failures cannot satisfy RED. | Plan §4 + T1; 165.001-T (C1–C5, N1–N8) |
| 2 | T3 audit is a pure read-only report; remove all durable-ledger writes, future-remediation fields, and persistence claims | Ledger **withdrawn in full**. No durable artifact, no file format, no persistence subsystem, no remediation field. Version-controlled operator migration commits/diffs are the external migration record and rollback evidence. T6 renders the report only and asserts **no write**. | Plan §3.3 + T3/T6; decision D3; 165.003-T; 165.006-T; 165-F; 173-S |
| 3 | Ruling (a): `SAFE_CLOSE` valid and non-blocking; `CASCADE` unavailable by design; preserve provenance and off-manifest status; retract all "impossible" claims | Verified classifier output recorded: per-item `SAFE_CLOSE`, naming `165.007-T`/`165.010-T` as archived off-manifest descendants. Documented as the **supported close path and final closure strategy** for `173-S`. `CASCADE` recorded as unavailable **by design**. All "both paths impossible" claims retracted. **No** reparenting, **no** holding feature, **no** manifest re-addition — verified unchanged. | Plan *Closure posture*; decision D4; 165-F; 173-S; 9AA34143 |
| 4 | Exactly THREE audited forced `pre_claim` invocations for `173-S`: Orchestrator U0, Ship pre-branch U1, Ship pre-claim U2; sole token, predecessor exactly `172-S`, exact HEAD/manifest, no other violation; mismatch expires; post-claim retry unauthorized | Corrected upward from two. U0 verified at `_orchestrator.agent.md` L239–241 (runs **before Ship is invoked**); U1 at `_ship.agent.md` L227–229; U2 at L254–255. Cursor-advance L261–263 **explicitly excluded** (different shipment). Conditions, expiry, and the unauthorized fourth/post-claim-retry path recorded. | Plan H6; decision D6; 165-F; 173-S |
| 5 | Remove closure-evidence discovery/evaluation/parity from T4/T5 and every `173-S` acceptance criterion; `FD0CCB42` exclusively owns closure naming | Closure removed **entirely** from T4 and T5, including the cycle-3 read-only `closure_complete` reuse (withdrawn with reason). T4/T5 cover only explicit/declared-root/genesis/unsequenced predecessor-state parity. `FD0CCB42` carries an explicit exclusive-ownership statement. `pre_claim`'s own closure check untouched. | Plan §2/§3.4/T4/T5; decision D4, D5; 165.004-T; 165.005-T; 165-F; FD0CCB42 |
| 6 | Narrow `dag-root` claims: version-controlled, review-gated, inside repository trust boundary; auditable but not mechanically permission-enforced; not a security boundary; no no-escape-hatch claim | Claim narrowed everywhere it appears. All "impossible"/"technically prevented"/"no escape hatch" formulations removed; recorded as an agent-contract rule enforced by review and audit, and as an **accepted residual risk**. | Plan §3.2 + H5; decision D1; 165.008-T (content req. 5); 165.009-T (deliverable 1); 165-F |
| 7 | Bug artifact self-contained: valid local frontmatter, explicit external provenance, no source-workspace paths presented as locally resolving, historical meaning preserved | `doc_type: bug`; `source:` now its own committed path; `docline.status: committed-intake-record`; **`external_provenance`** block added (`softwaresalt/backlogit`, `#438`, origin path, explicit non-resolution note). Transfer note replaced with a committed-intake note. Both non-resolving paths are **explicitly labelled** as external and non-resolving. Analysis body unchanged. | `docs/bugs/2026-09-11-…` |
| 8 | `ShipmentState` retains validated immutable labels tuple; root classification derives from it; labels-specific validator; historical directional cases become audit-output expectations; numeric claim-path residue blocking with no defer hatch | Labels tuple retained and validated by a **labels-specific** fail-closed validator (never `_tuple_of_str`). Classification derives from the tuple, not a re-parse. Directional cases re-posed as `audit_sequencing` **output** expectations, explicitly not helper-behaviour pins. Residue blocks the task **and** `173-S`; no deferral, stash, or waiver. | Plan §3.2 + T2; decision D1; 165.002-T; 165-F |
| 9 | T6 retains dependencies on T2 and T3 and renders only pure audit output | Both edges retained and verified live (`165.002-T → 165.006-T`, `165.003-T → 165.006-T`). The T3 edge is justified independently of the ledger: T3 still defines the **report shape** T6 renders. Rendering is pure output with a no-write assertion. | 165.006-T; 173-S; plan T6 |
| 10 | T8 keeps template and installed mirrors atomic; remove stale separate-task wording | Atomicity restated as mandatory (one task, one commit). The cycle-1 split is recorded as a **historical note** with an explicit "there is no separate mirror task, no follow-up, no second commit — do not re-derive one" guard. Ledger mention removed from content requirement 6. | 165.008-T; plan T8; 173-S |
| 11 | `FD0CCB42` and `9AA34143` explicitly cite P-021 C1 and keep requires-deliberation yes | Both entries now open with an explicit **P-021 C1** capture citation and carry a dedicated *POLICY BASIS* paragraph explaining why the surface is outside the running unit's authorized scope. Both retain `REQUIRES DELIBERATION: yes` under C6. Late-identifier reconciliation re-run and recorded (no-op, N/A values stand as truthful terminal records); unconditional duplicate scan re-run and recorded **CLEAN** for both. | Stash `FD0CCB42`, `9AA34143` |
| 12 | Tests: closure variants only for explicit predecessors; edge-less states once each; non-vacuous ordering; malformed dependency/label split correctly between characterization and RED | Closure variants removed from the matrix entirely (stronger than "explicit only"); each edge-less state asserted exactly once plus one genesis-narrowness parity case; non-vacuous fixture requirement stated with its prior-learning citation; malformed **dependency** = characterization (behaviour exists), malformed **label** = strict RED (behaviour absent). | 165.001-T; 165.004-T; plan T1/T4 |
| 13 | Rollback: code rollback does not undo migration data; migration commits/diffs are the ledger; explicit data rollback ordering; no gate-owned persistence subsystem | Documented: what is/is not code-reversible; the **version-controlled operator commit and its diff** as the durable record; mandatory **data-first** ordering (revert migration commits, then the engine) with the reason; narrowed claim where the migration was never committed, plus the preventive rule. Gate owns no write path. | Plan H4; decision D3; 165.009-T (deliverable 6a–6d); 165-F |
| 14 | Fix stale counts, task lists, and cumulative references | Plan/decision to **rev 4**; review to **cycle 4**; `165.008-T` relabelled **T8** with an explicit "there is no T7" rule and the T-label↔ID mapping; active task set restated as 8; archived set restated as `165.007-T` + `165.010-T` with a no-recreate/no-reparent/no-re-add guard; source-artifact revision references updated; "committed verbatim and unmodified" corrected to the cycle-3 self-containment description. | Plan §1/§4 + review block; decision frontmatter; 165-F; 173-S |
| 15 | Keep shipment manifest/dependencies/sizes coherent; document `SAFE_CLOSE` as the final closure strategy for `173-S` | Manifest **unchanged at 9 items**, dependency edges **unchanged at 10**, all sizes unchanged and complete. `SAFE_CLOSE` recorded as the **final closure strategy** on both `173-S` and `165-F`, with the explicit statement that no further closure work, authorization, or escalation is required. | 173-S; 165-F; plan *Closure posture* |

## Backlog Integrity Verification

Verified by a **fresh read** after all mutations, through backlogit **and** by an
independent parse of the `.backlogit/queue` Markdown records:

* **Manifest of `173-S`** — 9 items, stored order:
  `165-F`, `165.001-T`, `165.002-T`, `165.003-T`, `165.004-T`, `165.005-T`,
  `165.006-T`, `165.008-T`, `165.009-T`.
  `165.007-T` and `165.010-T` **absent**; both present in `.backlogit/archive/`
  with `parent_id: 165-F` **unmodified**. Shipment labels `[dag-root,
  topology-gate]` preserved.
* **Parent-first** — every item's `parent_id` precedes it in the manifest; no
  off-manifest parent; **no violation**.
* **Dependency edges (10, acyclic, no dangling, no manifest-order violation)**:
  `165.001-T → 165.002-T`;
  `165.002-T → 165.003-T`; `165.002-T → 165.004-T`; `165.002-T → 165.006-T`;
  `165.003-T → 165.006-T`;
  `165.004-T → 165.005-T`;
  `165.005-T → 165.008-T`; `165.005-T → 165.009-T`;
  `165.006-T → 165.008-T`; `165.006-T → 165.009-T`.
  Every prerequisite precedes its dependent in the stored manifest.
* **Sizing** — all eight tasks carry `size`, `complexity`, `size_source: agent`,
  and `size_ruleset_version: ah-stage-sizing-v1`, with **zero gaps**:
  165.001-T M/medium, 165.002-T M/high, 165.003-T M/medium, 165.004-T S/medium,
  165.005-T M/high, 165.006-T S/low, 165.008-T M/medium, 165.009-T S/low.
  No task exceeds the 2-hour bound. The two `complexity: high` tasks are de-risked
  by a preceding test-authoring task rather than split, since splitting would break
  the atomicity the plan requires. **No size or complexity value changed this
  cycle** — corrections were content-only.
* **Stash persistence** — `FD0CCB42` and `9AA34143` both retrievable live and
  present in tracked `.backlogit/stash.jsonl`; both carry `REQUIRES DELIBERATION:
  yes` and an explicit **P-021 C1** citation.
* **Document integrity** — frontmatter on all 13 touched artifacts parses as valid
  YAML. No unresolved `{{...}}` template placeholder tokens. Of 60 unique
  repo-relative file references across the corrected documents, **58 resolve**; the
  2 that do not are both in the bug artifact and are **explicitly labelled as
  external source-workspace paths that do not resolve here**, which is precisely
  what item 7 requires.
* **Residue scan** — every surviving mention of "migration ledger", `T7`, and
  read-only `closure_complete` reuse was inspected in context and is an
  **intentional retraction or withdrawal statement**, not a live instruction.

## Merged Finding Counts

| Severity | Count | Status |
|---|---|---|
| P0 | **0** | — |
| P1 | **0** | All fifteen operator corrections applied and verified in-cycle; none deferred |
| P2 | 2 | P2-A externalized to stash `9AA34143` (backlogit rollup member set); P2-B accepted with recorded handling and **narrowed** claim (`dag-root` is auditable, not mechanically enforced) |
| P3 | 4 | P3-1 shared-helper module location — requires a recorded choice at execution; P3-2 `audit_sequencing` phase-name taxonomy — accepted; P3-3 strict + reason-constrained xfail — already satisfied; P3-4 165.008-T budget note — advisory |

Neither open P2 is a same-contract-surface deferral: **P2-A** requires modifying
backlogit (a different repository surface, explicitly fenced out), and **P2-B**
requires a backlogit permission model that does not exist. Both are recorded with
handling rather than silently carried. No P3 blocks execution.

## Gate Decision

**decision: PASS**

Zero P0 and zero P1 findings. All fifteen items of the operator's coherent
correction set are applied in plan revision 4, the decision record revision 4, the
bug artifact, the covering feature `165-F`, the shipment `173-S`, all eight task
records, and both stash entries — and each is independently verified above.

The item-3 ruling is recorded consistently: `SAFE_CLOSE` is the verified,
supported, **non-blocking** final closure strategy for `173-S`; `CASCADE` is
unavailable by design; provenance and off-manifest status of `165.007-T` and
`165.010-T` are preserved without mutation.

Harvest is complete and `173-S` is **staging-PR ready**. *(The cycle-4 text here
originally made this contingent on Ship using three audited `pre_claim --force`
invocations authorized by decision D6. That contingency is **retracted** — see the
PR Review-Fix Cycle 1 section below, which establishes that no installed agent
contract can perform a forced invocation and replaces it with an operator-run
bootstrap plus the product mechanism `173-S` now ships.)*

**Plan-review cycle 4 was the authorized final PLAN-REVIEW cycle. No further
plan-review correction cycle is available.** PR review-fix cycles are a separate
counter and are recorded below.

## PR Review-Fix Cycle 1 (staging PR #448, 2026-09-13)

```text
scope: same-contract-surface correction of two Copilot review threads
branch: chore/stage-173-S
base HEAD at intake: 64fca6da
decision: PASS
P0: 0   P1: 0
```

**This is a PR review-fix cycle, not a plan-review cycle.** It is separate from and
subsequent to the four completed plan-review cycles and consumes none of them. It
modifies only Stage-owned plan/backlog/review/memory artifacts; no product source,
test, or template file was touched, no PR API action was performed, and nothing was
pushed or claimed.

### Thread 1 — `PRRT_kwDORzpWpM6h3Tgb` (`.backlogit/queue/173-S.md`) — ACCEPTED

**Finding.** The U0/U1/U2 bootstrap grant is not executable, because current
Orchestrator/Ship contracts call `pre_claim` without `--force` and halt on exit 1;
and the existing force telemetry/audit lacks full payload, HEAD, and D6 fields.

**Verification performed (evidence, not assertion).**

| Claim | Evidence |
|---|---|
| Orchestrator never forces; halts on exit 1 | `.github/agents/_orchestrator.agent.md` step 2a — command has no `--force`; "Exit 1 ... or exit 2 ...: halt routing to Ship ... never inferred, never fail-open" |
| Ship never forces; halts on exit 1 (both runs) | `.github/agents/_ship.agent.md` step 3 — both invocations lack `--force`; "halt immediately with the reported token/message — never inferred, never fail-open" |
| No force provision exists for this gate | The only agent-visible force provision is for `copilot-review` (`_ship.agent.md` L526–527); none for `pipeline-topology` |
| `--force` is stateless | `src/autoharness/cli.py` `_gate_pipeline_topology_command` converts exit 1 → 0 **in-process** and appends an audit line; it persists no verdict, so an agent's later unforced run is unaffected |
| Audit payload is insufficient | `_audit_pipeline_topology_force` writes only `timestamp`, `actor`, `reason`, `mode`, `phase`, `target_shipment_id`, `token`, `message` |
| Force audit log is not durable evidence | `.autoharness/gates/` is listed in `.gitignore` |
| Gate blocks `173-S` as described | Read-only evaluation from `main`: exit 1, sole blocking check `shipment_readiness`, token `PREDECESSOR_NOT_SHIPPED`, `details.predecessor_id: "172-S"`, `live_status: "queued"` |
| **New:** the recorded HEAD/vantage condition was wrong | Read-only evaluation from `chore/stage-173-S`: exit 1, sole blocking check `branch_ownership`, token `BRANCH_MISMATCH`. `PREDECESSOR_NOT_SHIPPED` is never reached, so cycle-3 validity condition 3 would have forced past a block D6 never authorized |

**Correction applied.** The three-invocation agent-run grant is retracted. It is
replaced by two explicitly separated mechanisms: **BOOTSTRAP-A**, a one-time
operator-run entry path for `173-S` that is executable today (operator runs the
three named gates unforced-then-forced from the correct vantages, commits a
version-controlled evidence record because the audit log is gitignored, claims
`173-S`, verifies `post_claim` **unforced**, and invokes Ship directly against an
already-claimed shipment — a path Ship's own step 6 explicitly contemplates with
"`expected_status: queued` (or `active` if already claimed)"); and **BOOTSTRAP-B**,
the product mechanism `173-S` ships for future migrations, added as two new manifest
tasks `165.011-T` (grant surface + full-provenance audit recording invocation, full
observed payload, HEAD, manifest identity, token/predecessor, and D6) and
`165.012-T` (Orchestrator/Ship consumption, sources and mirrors atomic).

**No retroactive authorization.** Every artifact now states explicitly that
`165.011-T`/`165.012-T` are shipped *by* `173-S`, are not installed until it merges,
and therefore cannot authorize the claim that precedes that merge.

**Authority bounds preserved.** Shipment-specific (`173-S` only), `pre_claim` only,
exact-token (`PREDECESSOR_NOT_SHIPPED`) and exact-predecessor (`172-S`) bound, at
most three forced invocations, expiring on claim or on any condition mismatch, with
no fourth invocation and no post-claim force.

### Thread 2 — `PRRT_kwDORzpWpM6h3Tgi` (`.backlogit/queue/165.003-T.md`) — ACCEPTED

**Finding.** `pipeline-topology` always emits ordinary telemetry when enabled, so
the absolute no-write claim is false.

**Verification.** `_gate_pipeline_topology_command` calls
`_emit_pipeline_topology_telemetry` unconditionally on every run, for every phase,
before returning; the emitter is fail-open by an `except Exception` handler that
returns a warning and never alters behaviour or exit code.

**Correction applied.** The audit contract is narrowed to **no backlog mutations
and no migration-state/ledger writes**. The pre-existing telemetry emission is
explicitly allowed and must remain observational and fail-open; the audit adds no
new field, journal, or emission site, and telemetry is never read back as state.
The test requirement changed from "assert that no file is created or modified" to
asserting no backlog/migration-state mutation, plus a positive assertion that with
telemetry enabled the event *is* emitted while output and exit code are identical
to a telemetry-disabled run, and that telemetry failure changes neither.

### Coupled-artifact sweep (completing the cycle)

The first pass of this cycle corrected `173-S`, `165.003-T`, the plan, the review,
and added `165.011-T`/`165.012-T`, but left coupled artifacts still asserting the
retracted claims. The sweep below closed them; a contradiction between a shipment
record and its own feature record is a P1-class defect, not a cosmetic one.

| Artifact | Residual defect found | Correction |
|---|---|---|
| `165-F` | BOOTSTRAP section still stated the U0/U1/U2 agent-run grant as live authorization | Rewritten to the retraction plus BOOTSTRAP-A/BOOTSTRAP-B split, with the no-retroactive-authorization rule stated |
| `165-F` | "THE AUDIT PERSISTS NOTHING … the gate owns NO write path" | Narrowed to no backlog mutation / no migration-state write; telemetry explicitly allowed, observational, fail-open |
| `165.006-T` | Body trailer omitted the new `→ 165.011-T` edge | Trailer states it, with the CLI-rendering serialization rationale |
| `165.008-T` | Body trailer omitted the new `→ 165.012-T` edge | Trailer states it, with the same-four-files serialization rationale |
| `165.008-T` | "READ-ONLY REPORT which persists nothing" propagated into agent contract text | Narrowed, and the agent text is explicitly barred from writing the absolute form |
| `165.009-T` | Frontmatter carried the `165.012-T` edge but the body did not, and the plan's new bootstrap-grant documentation requirement had no task-side deliverable | Added deliverable 8 (bootstrap grant surface) and corrected the trailer |
| `165.009-T` | Two further absolute no-write claims ("persists nothing", "owns no write path at all") | Narrowed; force-audit-log append also named so the doc task cannot restate the absolute |
| `165.009-T` | Deliverable 8 pushed an `S` (~1.5h) task toward the 2-hour bound | Size raised `S` → `M` (complexity unchanged at `low`); plan §4 table row updated to match |
| Deliberation `D6` | Still presented U0/U1/U2 as the executable disposition | Supersession banner added: the operator *authorization* stands, the *executor assumption* is retracted; historical sizing analysis preserved verbatim |
| Deliberation `D3` | "It writes nothing, persists nothing" | Same narrowing applied in place, historical body preserved |
| Deliberation frontmatter | `revision: 4` | Raised to `5` with a PR-review-fix revision note; `165-F` and `173-S` source references updated |

### Handoff precision added this cycle

Two operational gaps in BOOTSTRAP-A were closed, both required by "the initial path
must be executable" rather than merely describable:

1. **B6 entry state is now explicit.** Ship cannot derive that `173-S` is already
   claimed, which `expected_status` its step-6 `shipment-reconcile` check should
   use, or that it must run neither `pre_claim` invocation nor the step-5
   `post_claim` verification. The operator now states all four. The
   `expected_status` value is **observed at B3 and recorded at B5**, not assumed —
   the prior text asserted "every manifest task is still `queued`", which depends
   on unverified claim semantics. A **mixed** manifest means the operator skips
   that check per its own recorded Scope note rather than passing a value
   `shipment-reconcile` would classify `status-mismatch`.
2. **The installed "Bootstrap exemption" clauses are ruled out explicitly.**
   `_orchestrator.agent.md` L245–247 and `_ship.agent.md` L232–234, L297–299 skip
   the topology gate *while the gate is not installed*. It **is** installed here,
   so the exemption is inapplicable by its own condition — but it is exactly the
   clause a reader could misuse to skip the gate for a self-hosted shipment.
   `173-S` and the plan now bar that reading: BOOTSTRAP-A **runs** the gate
   unforced at every step and forces only a verified, condition-matched block.

### Necessity and bounds review of the two added tasks

`165.011-T` and `165.012-T` were re-examined against "verify they are necessary,
sized, dependency-wired, and bounded; otherwise simplify":

* **Necessary, and only jointly so.** The audit-provenance half (`165.011-T`
  deliverables 4–5) is directly demanded by the second half of the finding. The
  grant surface without a consumer is dead code, and the consumer without the
  surface has nothing to consume — so this is two tasks or zero, never one. Zero
  would leave the next self-hosted migration repeating BOOTSTRAP-A's manual path
  with no mechanism and no improved audit record, which is the state the finding
  objected to.
* **Correctly scoped as product work, not as a prerequisite.** Both are shipped
  *by* `173-S` and are explicitly barred from authorizing its own claim. Nothing in
  the entry path depends on them; BOOTSTRAP-A uses only currently installed
  mechanisms.
* **Sized within the rule.** Both `M` (~2h) / `medium`; neither is `high`
  complexity, so no split or de-risking step is forced.
* **Width-isolated.** `165.011-T` is CLI/audit code; `165.012-T` is agent-contract
  text. They do not share an edited surface.
* **Bounded.** `165.011-T` carries an explicit scope fence (no derivation
  semantics, no verdict logic, no exit-code contract change; a no-grant run is
  byte-identical to today). Grant authority is shipment-, token-, predecessor-,
  manifest-, and label-bound, at most once per site, `pre_claim` only — the same
  bounds as BOOTSTRAP-A, made mechanical. Shipment grows 9 → 11 items, every task
  ≤ `M`.

### Deterministic checks run this cycle

| Check | Result |
|---|---|
| Frontmatter validity (12 backlog records + plan + review + deliberation) | PASS — all parse, all `id` fields match filenames |
| Cross-reference integrity (every path referenced by an edited artifact resolves) | PASS — sole miss is a pre-existing cycle-3 ellipsis (`docs/bugs/2026-09-11-…`) in display text, P3, not a link |
| Manifest integrity (`173-S` = 11 items, unique, parent first, every item after its prerequisites) | PASS |
| Dependency DAG acyclicity + every edge endpoint on the manifest | PASS — 0 structural errors |
| Size + complexity present and enum-valid on all 10 tasks (two independent axes) | PASS — `165.011-T` M/medium, `165.012-T` M/medium, `165.009-T` raised S→M/low |
| 2-hour rule (no task over `M`; no new `complexity: high`) | PASS |
| Width isolation (CLI/audit work separated from agent-contract work) | PASS |
| Evidence claims re-verified against source, not inherited | PASS — audit field list, unconditional fail-open telemetry emission, stateless in-process `--force`, gitignored `.autoharness/gates/`, absent `--force` in both agent contracts, and `branch_ownership`-before-`shipment_readiness` short-circuit (`topology.py` L795–806) all confirmed by direct read |
| Residual absolute no-write claims anywhere in the feature's artifacts | NONE — swept to zero |
| Residual claims that an agent consumes a force grant to enter `173-S` | NONE — swept to zero |
| Unresolved template placeholders introduced | NONE |
| P-001 role boundary (no source, test, template, or config file modified) | PASS |

### Finding counts

| Severity | Count |
|---|---|
| P0 | **0** |
| P1 | **0** |
| P2 | 2 (carried unchanged from cycle 4: `9AA34143` rollup member set; `dag-root` not mechanically enforced) |
| P3 | 4 (carried unchanged from cycle 4) |

No new P0 or P1 finding remains open. Both threads are resolved on the same
contract surface they were raised against, and every coupled artifact now states
the corrected contract consistently.

## PR Review-Fix Cycle 2 (staging PR #448, 2026-09-13)

```text
scope: same-contract-surface correction of five Copilot review threads
branch: chore/stage-173-S
base HEAD at intake: 5aec76f2
decision: PASS
P0: 0   P1: 0
```

**Still a PR review-fix cycle, not a plan-review cycle.** It consumes none of the
four completed plan-review cycles. It modified only Stage-owned
plan/backlog/review/memory artifacts; no product source, test, or template file was
touched, no PR API action was performed, and nothing was pushed or claimed. All five
findings were assessed VALID and ACCEPTED.

**Scope of record (thread `PRRT_kwDORzpWpM6h3frY`, final item).** Current scope is
**10 executable tasks** (`165.001-T`, `165.002-T`, `165.003-T`, `165.004-T`,
`165.005-T`, `165.006-T`, `165.008-T`, `165.011-T`, `165.012-T`, `165.009-T`) plus
the covering feature `165-F` — **11 manifest items** — and the one-time operator
entry path **BOOTSTRAP-A, steps B0/B1/B2** (forced `pre_claim`), B3, B4, B5, B6.
`U0`/`U1`/`U2` name the **retracted** cycle-2/cycle-3 agent-run grant and are
historical only. The PR #448 body is **Orchestrator-owned** and is updated
separately; `173-S` and `165-F` are authoritative for these counts. No manifest,
edge, or size change was made this cycle.

### Thread 1 — `PRRT_kwDORzpWpM6h3fqf` (`165.011-T`, at-most-once consumption) — ACCEPTED

**Finding.** "At most once" had no defined mechanism — the text said only that a
label "is not already consumed".

**Assessment.** Valid, and the most consequential finding of the cycle. At-most-once
*is* the entire security value of a bootstrap grant; leaving its mechanism undefined
left the bound undefined. As written the requirement was satisfiable by an
in-process set that resets on every CLI invocation — a zero-guarantee at-most-once
that would still have passed review.

**Correction applied.** Deliverable 6 defines a concrete durable atomic mechanism:

| Aspect | Contract |
|---|---|
| Claim primitive | `os.open(..., O_CREAT \| O_EXCL \| O_WRONLY, 0o600)` — atomic on POSIX, `CREATE_NEW` on Windows. Read-then-write existence checks are **forbidden** (TOCTOU) |
| Location | `.autoharness/gates/bootstrap-grant-consumption/{shipment_id}/{label}.json` — under the already-gitignored `.autoharness/gates/` prefix, because this is node-local runtime state; the **grant** remains the version-controlled reviewable authorization |
| Ordering | Evaluate unforced → apply all non-consumption match conditions → **claim** → only then force → emit audit. A non-matching grant never burns a label |
| Record | `schema_version`, `grant_digest`, `grant_path`, `shipment_id`, `label`, `phase`, `actor`, `session_id`, `head_sha`, `manifest_digest`, `blocking_token`, `inferred_predecessor_id`, `claimed_at`, `status`, `audit_ref` |
| Contention / replay | `FileExistsError` → fail closed, exit 1, warning. Never wait, retry, poll, break, or steal. **No TTL** (a TTL is at-most-once-per-interval) |
| Grant tampering | `grant_digest` mismatch fails closed — editing the grant cannot reset consumption |
| Crash states | Crash after claim (pre-evaluation or pre-audit) leaves an intact `claimed` record carrying every audit field; `claimed`→`consumed` uses temp+`fsync`+`os.replace` so the record is never torn |
| Recovery | **Operator-only, out-of-band.** No CLI reset flag exists — such a flag would let an agent re-open an exhausted grant (P-005/P-001) |
| Audit source | Emitted **from the claimed record**, not recomputed from live state, so the audit cannot record a state that was never authorized |
| Malformed/stale record | Treated as **consumed** (fail closed) — the deliberate inverse of a malformed *grant* being treated as *no grant*; both resolve toward **no force** |
| Containment | ID/label validated before any path construction; separators, `..`, NUL, drive/UNC rejected; resolved path asserted inside the resolved root, symlinks included |

**Scope bound stated rather than hidden.** The guarantee is **per workspace clone**;
a fresh clone starts with no consumption state. Compensating bounds
(`expires_on_claim`, exact-token binding that stops matching once the shipment
leaves `queued`, manifest-digest binding) are recorded, and a cross-machine
guarantee is explicitly **not** invented. Recorded as accepted residual risk in plan
§H5 and assigned to `165.009-T` deliverable 8b for documentation.

**Sizing consequence.** `165.011-T` complexity raised **medium → high**; size
unchanged at `M`. Per the two-axis rule `complexity: high` forces split-or-de-risk;
**de-risked in place**, because Deliverable 6 is inseparable from Deliverable 2's
matching rule — splitting them would ship a grant surface whose at-most-once bound is
unenforced for the duration of the gap, which is precisely the defect raised. The
de-risking is the enumerated 6a–6i contract plus a named concurrency/crash/replay
test matrix.

### Thread 2 — `PRRT_kwDORzpWpM6h3fq1` (`173-S` B4, claim reversal) — ACCEPTED

**Finding.** BOOTSTRAP-A B4 instructed the operator to "reverse the claim" on a
non-zero `post_claim`, but backlogit has no `active` → `queued` transition.

**Verification performed (evidence, not assertion).**

| Claim | Evidence |
|---|---|
| No unclaim/release/abort exists | `backlogit shipment --help` at this HEAD lists exactly `add`, `claim`, `create`, `get`, `list`, `return-blocked`, `ship` |
| `queued` is not reachable from `active` | Shipment status enum is {`queued`, `blocked`, `active`, `shipped`, `abandoned`}; `queued` is the create-time default only |
| `abandoned` *is* reachable | `abandoned` is a member of the shipment status enum; `backlogit update <id> --status <s>` exposes `--status` |

**Assessment.** Valid. A failure branch that terminates in an unexecutable step — at
the exact moment the workspace sits half-entered — is worse than having no failure
branch, because it reads as a safety net that does not exist.

**Correction applied.** "Reverse the claim" is **removed**. The executable contract
is: halt immediately, `173-S` **remains `active`**, B5/B6 are not performed, Ship is
not invoked, and no forced re-run is attempted (force authority already expired on
the successful B3 claim). Remediation is explicit and operator-owned:
**(a) diagnose and converge** — resolve the rejected condition (most plausibly a
second `active` shipment, a P-001 violation) and re-run B4 unforced until it exits 0,
then resume at B5; `173-S` stays `active`, a forward fix rather than a rollback; or
**(b) abandon** — the supported `active` → `abandoned` transition, which **must be
verified** by re-reading the record and confirming `status: abandoned`, and which is
**terminal, not a requeue**: the scope must then be re-shipped under a new shipment
record. No artifact may promise automatic reversal or requeue. Applied to `173-S`,
plan §H6, and `165-F`.

### Thread 3 — `PRRT_kwDORzpWpM6h3frC` (RED-test mechanism) — ACCEPTED

**Finding.** Canonical CI uses `unittest`; `unittest.expectedFailure` cannot
constrain the reason.

**Verification performed.**

| Claim | Evidence |
|---|---|
| Canonical CI runs stdlib `unittest` | `.github/workflows/ci.yml` — `PYTHONPATH=src python -m unittest discover -s tests`; the file header states "autoharness has no ruff/pyright/pytest configured; the only real gates are the stdlib unittest suite … and markdownlint" |
| A pytest `xfail` marker is inert there | Under `unittest`, `@pytest.mark.xfail` sets an attribute nothing reads — the body runs, the expectation raises, **CI goes red** |
| `expectedFailure` cannot constrain the reason | It accepts *any* exception and takes no `raises=` and no reason argument |

**Assessment.** Valid, and it invalidated an instruction the plan had been carrying
since cycle 3. The cycle-3 text ("pin each marker with an explicit `raises=`/reason")
described a pytest capability under a runner that is not pytest. Had it been
implemented literally, the harness task would have left canonical CI **red** — the
precise outcome its own "every task ends green" rule forbids.

**Correction applied.** A stdlib-only helper replaces both mechanisms:
`@expect_red(raises=..., message_contains=..., reason=...)` — (a) passes only on the
named exception type whose *normalized* message (`str(exc)`, whitespace-collapsed,
stripped, casefolded) contains the expected substring; (b) **fails on any other
exception**, naming expected vs. observed and flagging it as a *wrong* failure, so a
broken fixture, an import/collection error, or an unregistered `--phase` turns the
suite red instead of masquerading as RED; (c) **fails on XPASS**, preserving the
strictness that made `xfail(strict=True)` desirable. Pure stdlib, no `pytest`
import, identical behaviour under both runners. The permitted simpler alternative —
authoring a RED expectation in the same task as its implementation, with the RED
observation recorded in the disposition notes — is stated explicitly. **Every task
ends green under both routes.** Applied to `165.001-T`, `165.002-T`, `165.004-T`,
`165.005-T`, and plan §4/§T1/§T2/§T3/§T4/§H2 (F5, F13).

### Thread 4 — `PRRT_kwDORzpWpM6h3frF` (genesis narrowness) — ACCEPTED

**Finding.** Genesis must hold only when the candidate is the sole shipment record
across all live and archived records, regardless of status/provenance; blocked,
missing, and malformed/unrecognized archived statuses must disqualify or fail closed.

**Verification performed.**

| Claim | Evidence |
|---|---|
| `blocked` is a real shipment status | `backlogit_get_metadata_catalog` → shipment `status` enum = {`queued`, `blocked`, `active`, `shipped`, `abandoned`} |
| The cycle-2 rule omitted it | G3 enumerated disqualifying nonterminal states as "`queued`/`active`"; G2 covered shipped-terminal only; G4 covered abandoned only. `blocked` appeared in **none** |
| Therefore a fail-open existed | Candidate + one `blocked` record satisfied G2 ∧ G3 ∧ G4 → returned `genesis` — an unearned pass |

**Assessment.** Valid, and structurally important beyond the single missing status.
Enumerating statuses is fragile by construction: every value the enum gains in
future silently re-opens the same hole at a moment nobody is watching for it.
Counting *records* is status-agnostic and cannot be widened by a new enum member.

**Correction applied.** G2/G3/G4 are replaced by a single **sole-record** rule:
genesis requires G1 (no edges, no `dag-root`) **and** G2 (the candidate is the only
shipment record in the workspace, live and archived counted together, regardless of
status and provenance). Any other record disqualifies. A record whose status is
absent, empty, non-string, unparseable, or unrecognized — including an unrecognized
`archived_status` — **counts as disqualifying, fail closed**, never skipped or
defaulted. An enumeration failure raises `BacklogUnavailableError` rather than
concluding sole-extancy from a partial read. Genesis remains cardinality-1.
Secondary benefit: the shared-snapshot surface (§3.4) drops from three facts to one,
strictly lowering divergence risk.

**Regression cases added.** `165.001-T` N5f (a `blocked` record present, live and
archived), N5g (missing / empty / non-string / unrecognized status / unrecognized
`archived_status`, each asserted independently), N5h (enumeration failure raises);
N5e extended to prove `dag-root` still passes in every one of those workspaces;
`165.004-T` P3b widened to two disqualifier shapes including `blocked`. Applied to
`165-F`, `165.001-T`, `165.002-T`, `165.004-T`, `165.005-T`, `165.008-T`,
`165.009-T`, and plan §3.1/§3.4/§T1/§T2/§T4/§T5/§T6/§T8/§T9/§H2 (F10, F11)/§H5.

### Thread 5 — `PRRT_kwDORzpWpM6h3frY` (`165.006-T` audit purity) — ACCEPTED

**Finding.** The zero-write assertion was reintroduced in the CLI task.

**Assessment.** Valid, and a genuine **regression of a cycle-1 correction**.
PR review-fix cycle 1 retracted the absolute no-write claim from `165.003-T`,
`165-F`, `165.008-T` and `165.009-T` on thread `PRRT_kwDORzpWpM6h3Tgi`, but
`165.006-T` deliverable 5 — authored in that same cycle — still required "an
assertion that the audit render path performs NO WRITE — no file created, no record
mutated". It is false for the same verified reason:
`_gate_pipeline_topology_command` calls `_emit_pipeline_topology_telemetry`
unconditionally on every run of every phase. This is exactly the class of
coupled-artifact miss the cycle-1 sweep existed to catch, which is why the sweep
table is now a standing obligation rather than a one-off.

**Correction applied.** The absolute assertion is **removed** and replaced by the
scoped form matching `165.003-T`: (a) no backlog mutation; (b) no migration-state or
ledger write; (c) telemetry **explicitly allowed and positively tested** — with
telemetry enabled the event *is* emitted while rendered output and exit code are
identical to a telemetry-disabled run; (d) telemetry failure changes neither output
nor exit code (fail-open preserved, not narrowed or made load-bearing). An explicit
anti-regression note bars any future reintroduction. Applied to `165.006-T` and plan
§T6.

### Coupled-artifact sweep (completing this cycle)

| Artifact | Change |
|---|---|
| `173-S` | B4 failure contract rewritten (no reversal); BOOTSTRAP-B bullet names the durable consumption record; new "PR REVIEW-FIX CYCLE 2 CHANGES" block with the five thread dispositions and the scope-of-record statement |
| `165-F` | Genesis rewritten to the sole-record rule; BOOTSTRAP-A B4 halt-with-active note; BOOTSTRAP-B names the consumption record; new SCOPE OF RECORD paragraph (10 executable tasks, B0/B1/B2, not U0/U1/U2) |
| `165.001-T` | RED mechanism section replacing the xfail/`expectedFailure` instruction; genesis rewritten to sole-record with N5f/N5g/N5h added and N5e extended; fixture quality gate and sizing rationale updated |
| `165.002-T` | Genesis rewritten to sole-record with fail-closed unclassifiable-record rule and eight-case coverage list; constrained-RED mechanism replacing "CONSTRAINED XFAIL REASONS"; strict-xfail references re-expressed |
| `165.004-T` | Constrained-RED mechanism; P3 fixture restated under sole-record; P3b widened to two disqualifier shapes including `blocked` |
| `165.005-T` | Shared-helper snapshot reduced from three genesis facts to one sole-record count, with fail-closed and enumeration-failure rules |
| `165.006-T` | Zero-write assertion removed and narrowed; genesis-disqualifier rendering restated as naming the disqualifying record(s) |
| `165.008-T` | Agent-text genesis rule restated as sole-record, with an explicit bar on restating the retired three-probe form |
| `165.009-T` | Doc genesis rule restated as sole-record with the "why count records" rationale; new deliverable 8b documenting the consumption mechanism and its honest per-clone scope bound |
| `165.011-T` | Deliverable 6 added (6a–6i) with its test matrix; Deliverable 2 no longer says "not already consumed"; complexity medium → high with recorded de-risk rationale |
| Plan | §3.1 genesis table and rules; §4 RED mechanism + T10 complexity cell; §T1/§T2/§T3/§T4/§T5/§T6/§T9/§T10; §H2 F5/F10/F11/F13; §H5 new residual risk; §H6 B4 failure contract; frontmatter revision 5 → 6 |

### Deterministic checks run this cycle

| Check | Result |
|---|---|
| Frontmatter validity (12 backlog records + plan + review + deliberation) | PASS — all parse; all `id` fields match filenames |
| Manifest integrity (`173-S` = 11 items, unique, parent first, every item after its prerequisites) | PASS — unchanged this cycle |
| Dependency DAG acyclicity + every edge endpoint on the manifest | PASS — 0 structural errors, edge set unchanged |
| Size + complexity present and enum-valid on all 10 tasks (two independent axes) | PASS — `165.011-T` now M/**high**, recorded via the structured `complexity` field; all others unchanged |
| 2-hour rule | PASS — no task above `M`; the one new `complexity: high` is de-risked in place with recorded rationale rather than left unaddressed |
| Width isolation | PASS — CLI/audit, engine, agent-contract, and docs work remain separate tasks |
| Evidence claims re-verified against source, not inherited | PASS — `backlogit shipment` subcommand list, shipment status enum, CI test-runner invocation, and the unconditional telemetry emission all confirmed by direct read this cycle |
| Residual absolute no-write claims anywhere in the feature's artifacts | NONE — swept to zero (the `165.006-T` regression was the last one) |
| Residual undefined "not already consumed" semantics | NONE — replaced by Deliverable 6 |
| Residual promises of automatic claim reversal or requeue | NONE — swept to zero |
| Residual `G2`/`G3`/`G4` probe references presented as live rule | NONE — retained only as explicitly-labelled retracted history |
| Residual `xfail`/`expectedFailure` instructions presented as live mechanism | NONE — retained only as explicitly-labelled rejected alternatives |
| Residual claims that an agent consumes a force grant to enter `173-S` | NONE |
| Unresolved template placeholders introduced | NONE |
| P-001 role boundary (no source, test, template, or config file modified) | PASS |

### Finding counts

| Severity | Count |
|---|---|
| P0 | **0** |
| P1 | **0** |
| P2 | 2 (carried unchanged from cycle 4: `9AA34143` rollup member set; `dag-root` not mechanically enforced) + 1 new, accepted and recorded (bootstrap-grant at-most-once is per-workspace-clone, not global — plan §H5) |
| P3 | 4 (carried unchanged from cycle 4) |

No new P0 or P1 finding remains open. All five threads are resolved on the same
contract surface they were raised against, every coupled artifact states the
corrected contract consistently, and no manifest, edge, or size change was required.
