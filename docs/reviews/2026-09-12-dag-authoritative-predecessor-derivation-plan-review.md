---
title: "Plan review — DAG-authoritative predecessor derivation (cycle 4, authorized final review)"
description: "Multi-persona adversarial plan review of docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md revision 4, gating harvest. Operator-authorized additional narrow correction cycle; no further fix loop."
doc_type: review
source: docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md
date: 2026-09-13
plan_path: docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
plan_revision: 4
review_cycle: 4
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

Harvest is complete and `173-S` is **staging-PR ready**, contingent on Ship using
the **three** audited `pre_claim --force` invocations (U0 Orchestrator, U1 Ship
pre-branch, U2 Ship pre-claim) authorized by decision D6 for `173-S` only, under
the per-invocation conditions recorded on the shipment, with any mismatch expiring
the authority and post-claim retry unauthorized.

**This was the authorized final review. No further correction cycle is available.**
