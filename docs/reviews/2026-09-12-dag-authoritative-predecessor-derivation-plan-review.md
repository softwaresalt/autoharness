---
title: "Plan review — DAG-authoritative predecessor derivation (cycle 3)"
description: "Multi-persona adversarial plan review of docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md revision 3, gating harvest. Final normal correction cycle."
doc_type: review
source: docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md
date: 2026-09-12
plan_path: docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
plan_revision: 3
review_cycle: 3
decision: PASS
---

# Plan Review — DAG-Authoritative Predecessor Derivation (cycle 3)

Review cycles used: **3 of 3**. This is the **final normal correction cycle**; no
further in-cycle correction budget remains under the Stage stop-condition table.

This review supersedes the cycle-2 review of plan revision 2 (commit `2744359a`;
that text remains in git history). Cycle 2 returned PASS with 0 P0 / 0 P1, and the
operator subsequently raised **twelve** further findings (nine P1, three P2)
against the cycle-2 output. Cycle 3 reviews **plan revision 3**, rewritten to
resolve them. The "Operator Findings Verification" section checks each of the
twelve individually; the persona passes below are an independent re-review, not a
restatement of that checklist.

## Dispatch Capability and Declared Degradation

```text
dispatch_mode: single-agent-declared-degradation
TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass
TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass
TOOL_DEGRADED: agent-engram (unified_search / impact_analysis) — declared fallback: file-based grep/view over src/ and tests/
TOOL_DEGRADED: agent-intercom — declared fallback: no phase broadcast; operator visibility via session report only
TOOL_DEGRADED: graphtor-docs — declared fallback: direct read of docs/compound/ and docs/decisions/
TOOL_OK: backlogit (MCP) — index synced; shipment, task, and stash reads verified live
```

No subagent dispatch surface and no alternate model route are available in this
session, so this is a **declared** degradation, not a silent one (P-012). Every
persona below was applied inline against its rubric — no persona was skipped, and
no finding was downgraded because of the degradation. Reviewer route:
`claude-opus-5`/`anthropic`/`high` (same as caller).

Claims in this review that depend on current source behaviour were verified by
**direct read** in this cycle, not carried over: `src/autoharness/gates/topology.py`
(`_tuple_of_str` L331 and `_ARTIFACT_ID_PATTERN`; the shipment frontmatter parser
L560–600), `.github/agents/_ship.agent.md` (the pre-claim protocol at L227–229,
L254–258, L282–283), and the live `.backlogit` records and stash.

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
| — | Principle II (Test-First, NON-NEGOTIABLE): still satisfied, and strengthened. The cycle-2 risk that T2 could close with claim-path numeric residue under a "record a follow-up" escape is removed; the residue now blocks the task and the shipment, so the test is load-bearing rather than advisory. | OK |
| — | Principle VIII (Explicit Safety Modes for Elevated Risk): the fail-closed posture is materially tighter after the genesis narrowing. The only remaining pass-without-edges paths are an explicit recorded declaration and a cardinality-1 bootstrap. | OK |
| — | Principle V (Structured Observability): `predecessor_source` on every payload, plus the new genesis-disqualifier reporting and the migration ledger, make each block explainable from output alone. | OK |
| — | Principle VI (Single Responsibility): the T7/T8 merge is a legitimate exception to width isolation, not a violation of it — template sources and their installed mirrors are one artefact in two locations, and splitting them separates a thing from its own copy rather than separating concerns. | OK |
| — | P-001 role separation: Stage authored planning and backlog artefacts only. The one source file added this cycle (`docs/bugs/2026-09-11-…`) is committed **byte-for-byte unmodified** under explicit operator authorization, is documentation rather than product source, and no template, engine, test, or config file was touched. | OK |
| — | P-021 C6: both deferred-scope-expansion entries now carry `requires deliberation: yes`. `9AA34143`'s prior `no` is corrected, and the correction records *why* the deliberation is non-vacuous rather than asserting the flag mechanically. | OK — resolves operator finding 9 |

### Python Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | **The `_tuple_of_str` reuse instruction was a genuine latent P0 and is correctly retracted.** Verified by direct read: `_ARTIFACT_ID_PATTERN` is `^\d+(?:\.\d+)*-[A-Z]+$`, `_tuple_of_str` raises `BacklogUnavailableError` on any member that fails it, and `dag-root` fails it. Had an implementer followed the cycle-2 instruction literally, every shipment record carrying any label — including `173-S` itself — would have become a hard read failure, converting the gate from "blocks one shipment" to "cannot read the workspace". The replacement separates the fail-closed **discipline** (which transfers) from the artifact-ID **syntax** (which does not). | OK — resolves operator finding 5 |
| — | The labels validator's member rules are specified concretely (non-string raises, blank raises, path-separator/`..` raises, bounded length) rather than gestured at, and the traversal clause is justified by the same `closure_complete` glob hazard `_tuple_of_str`'s own docstring records. | OK |
| — | The positive anti-regression test (N7a: `[dag-root, topology-gate]` parses and raises nothing) is the right shape. A negative-only matrix would have passed happily against the broken instruction. | OK |
| — | Genesis now reads three workspace facts instead of one. All three are specified as single-snapshot computations inside the shared helper, so the added probes do not multiply the divergence surface they are meant to close. | OK |
| — | `_prior_shipment_id` is still retained rather than deleted, and T3 is now explicitly told to consume the **raw** adjacency computation rather than the suppressed result — closing the gap where "re-home the function" could have been read as "re-home its suppression too". | OK |
| P3-1 | The shared derivation/closure helper's module location remains unspecified — `topology.py` or a new module. | Advisory, carried. 165.005-T requires the executor to *state* the choice in the task record; either is acceptable. |
| P3-3 | Expected-failure tests must be **strict** xfail. Now load-bearing in a new way: T2's audit expectations sit strict-xfail across a task boundary until T3 flips them, so a non-strict marker would silently hide an early pass. | Already required by 165.001-T and restated in 165.002-T. No change needed. |

### Test Strategy Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | **The `_prior_shipment_id` pin is correctly removed.** Cycle 2 would have preserved retired suppression behaviour as a live unit-test expectation over an internal function — pinning a defective predicate as a tested contract, and directly contradicting D3/F6, which require the audit to report the raw candidate *without* suppression. Re-expressing the knowledge as the **negation** of suppression at the audit surface preserves what the cases actually knew (which candidate exists) while asserting the behaviour the design wants (that it is reported). | OK — resolves operator finding 6 |
| — | Green-per-task is preserved across the new arrangement: T2 lands those cases strict-xfail (green), T3 flips them (green). No task ends red, and T3 cannot land without satisfying them. | OK |
| — | Per-case disposition is still mandatory for all five cases and bulk deletion still forbidden, so narrowing the permitted dispositions to two did not create a deletion loophole. | OK |
| — | **Closure cross-product narrowing is correct, not a coverage reduction.** Closure evidence is evaluated per explicit predecessor; `declared_root`, `genesis`, and `unsequenced` have no predecessor for it to apply to, so those cells could not have distinguished any outcome. Removing them removes vacuous cells while parity stays total over the four states. | OK — resolves operator finding 10 |
| — | Genesis assertions are split per disqualifier (G2/G3/G4) with an explicit instruction to assert G3 over at least two candidates including a later-numbered one. A single composite fixture would have satisfied the old wording while proving only one clause. | OK |
| P3-2 | `audit_sequencing` as a phase name still sits alongside `pre_claim`/`post_claim`/`lifecycle`/`ambient`, which are lifecycle *positions* rather than activities. | Advisory, carried. Registered in `VALID_PHASES` only, never `SCOPED_PHASES`, so it cannot acquire an active-target requirement. |

### Scope Boundary Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | **The F6 deferral escape hatch is removed.** Cycle 2 permitted T2 to close with claim-path numeric residue provided a follow-up stash entry was filed. That would have shipped a shipment whose own stated contract ("no numeric comparison on the claim path in any state") was false at merge. Residue now blocks the task and `173-S`; escalation is to the operator, and additional removal work must stay **inside** `173-S`. | OK — resolves operator finding 7 |
| — | **The template/mirror split is correctly reversed.** A dependency edge orders work; it does not prevent drift. Between the two cycle-2 tasks this repository would have held template sources on the new contract and installed `.github/agents/` mirrors — which the dogfooded agents actually read — on the retired one. Merging into one task and one commit removes the window entirely rather than shortening it. | OK — resolves operator finding 8 |
| — | The merge did not quietly drop scope: the installed-mirror edit surfaces and the recorded parity check survive verbatim in 165.008-T, and the size was raised S → M rather than left understated. `165.010-T` is archived with a forward reference, its inbound edge removed first, and it is off the manifest. | OK |
| — | `FD0CCB42` verified **live** by a fresh `backlogit_stash_get` this cycle (not inferred from the archive or from memory) and present in tracked `.backlogit/stash.jsonl`. The archived `165.007-T` therefore forward-references a real, durable item. | OK — resolves operator finding 9 |
| P2-A | The shipment `size_composition.members` rollup still lists archived, off-manifest `165.007-T` **and now `165.010-T`**, because it derives members from `parent_id` children rather than from `custom_fields.items`. The manifest itself is correct at 9 items. | **Externalized**, not absorbed: stash `9AA34143`, now recording a **second occurrence** in a second consecutive cycle. Fixing it requires modifying backlogit, outside this shipment. The `173-S` record itself now carries a "known tool artefact" note so a future reader does not "reconcile" it by re-adding an archived task. |
| — | Scope fences hold: `86498B64`, `9B582824`, `97B28746`/`50434138`, `58A85283` all remain separate; backlogit is not modified; closure semantics are untouched. | OK |

### Architecture Strategist

| Sev | Finding | Disposition |
|---|---|---|
| — | **The genesis narrowing is the most important correction in this cycle.** "No shipped-terminal shipment exists" is not a bootstrap test, it is a *has-not-shipped-yet* test — and a workspace can hold a dozen queued shipments while satisfying it. Under the old rule every edge-less shipment in such a workspace passes `genesis` **simultaneously**, which is the same unearned-pass failure the feature exists to remove, reintroduced in the state designed to be the safe one. Sole-extancy (G3) converts genesis into a cardinality-1 property that cannot hold for two candidates at once and expires permanently once a second record exists. | OK — resolves operator finding 2 |
| — | The `abandoned` clause (G4) is not pedantry: `abandoned` is terminal-but-not-shipped, so a shipped-history-only probe admits an abandoned-only workspace as a fresh install. Closing G2 without G4 would have left a narrower version of the same hole. | OK |
| — | **Later-numbered candidates are now provably unable to pass silently**, and the plan states the mechanism rather than asserting the property: there is no genesis path at all in a populated workspace, so the only outcomes are `explicit`, `declared_root`, or a block. | OK |
| — | The three-fact genesis probe is correctly pushed into the shared helper as a single-snapshot computation. Three independently-probed facts across two gates would have been three chances to re-diverge — the cycle-2 P2-3 defect multiplied. | OK |
| P2-B | The `dag-root` label still has **no mechanical enforcement**: any actor who can edit a shipment record can declare a root. The genesis narrowing slightly *increases* the pressure on this boundary, because declaration is now the only edge-less pass path in any populated workspace. | **Accepted with handling**, deliberately a contract boundary rather than an oversight. Mitigations: the declaration is durable, diffable, and attributable; `predecessor_source: declared_root` makes every such pass auditable after the fact; and the agent contract (165.008-T, now covering sources *and* mirrors in one commit) prohibits self-declaration. Mechanical enforcement needs a backlogit-side permission model — outside this shipment. |

### Agent-Native Parity Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | Sources and installed mirrors are now one atomic unit, and the contract text requirements are stated once and applied to both, so the two cannot state different things at any commit boundary. | OK |
| — | The agent-facing text must now also state that **genesis is narrow**. This matters specifically for agents: an agent that believes "nothing has shipped, so I am genesis" would form the wrong expectation about its own claimability and could misread a correct `unsequenced` block as a gate defect. 165.008-T requires this explicitly. | OK |
| — | The `173-S` record itself now carries the two-use force authorization in a form Ship can execute against without interpretation: named invocation points, enumerated validity conditions, an explicit expiry, and an explicit statement that a third invocation is unauthorized. | OK |
| P3-4 | 165.008-T sits at `M` (~2h), the top of the 2-hour bound, after absorbing the mirror work. | Advisory. The estimate is defensible because the contract text is *authored once* and mirrored within the same working context rather than re-derived in a second sitting (the cycle-2 split's 1.5h + 1h double-counted context loading). If execution exceeds budget, the correct response is escalation inside `173-S`, **not** re-splitting sources from mirrors — that would reinstate the drift window this cycle closed. |

### Security / Safety Lens

| Sev | Finding | Disposition |
|---|---|---|
| — | **The two-use force authorization is correct and is a safety improvement, not a relaxation.** Verified against `.github/agents/_ship.agent.md`: Ship runs `--phase pre_claim` before branch/worktree creation (L227–229) and again immediately before the claim (L254–255), with the claim gated on both (L258). A "single-use" grant was therefore unsatisfiable, and an unsatisfiable authorization is the *more* dangerous artefact — it pressures the executing agent to either halt mid-protocol or silently stretch one grant across two invocations, unaudited. Naming both invocations makes the real cost visible and auditable. | OK — resolves operator finding 3 |
| — | The per-invocation conditions are genuinely constraining rather than decorative: sole-token, exact-predecessor, HEAD-and-manifest match, and no other topology/check/closure/secrets violation. Each is independently checkable from the gate payload plus git state, so Ship cannot satisfy them by assertion. | OK |
| — | **The third-invocation exclusion is the sharpest part of the fix.** The post-claim `CLAIM_NOT_OBSERVED` retry path (L282–283) genuinely re-runs `pre_claim`, so an unbounded "for the claim of 173-S" grant would have silently covered it. Naming that path and declaring authority exhausted there closes a real, reachable third use. | OK |
| — | Expiry is defined on both the success and the mismatch edge, and the mismatch edge halts to the operator rather than degrading to retry. Combined with self-liquidation via `declared_root` once T2 lands, the grant cannot outlive its purpose. | OK |
| — | `--force` semantics themselves remain unchanged; no agent may self-authorize; the grant remains `173-S`-only with no precedent. | OK |
| — | The rollback correction is a safety finding as much as a documentation one: an operator who believed "revert the engine" sufficed would have left migrated edges being read by the restored numeric engine — a configuration that existed neither before nor after, and the most confusing possible failure state. Data-first ordering plus the ledger makes rollback executable. | OK — resolves operator finding 11 |

## Operator Findings Verification (cycle-2 correction request, twelve findings)

| # | Sev | Operator finding | Resolution | Where |
|---|---|---|---|---|
| 1 | P1 | Durable source integrity — cumulative diff still references an untracked bug report | The existing bug report is committed **byte-for-byte unmodified** as the intake artefact, so `AF2890B7` and the cycle-1 memory now resolve. No edit to its content; no other untracked file added. Stale forward-reference annotations corrected by **append-only** means (see 12). | `docs/bugs/2026-09-11-…`; decision *Historical context*; plan *Provenance*; 165-F record |
| 2 | P1 | Genesis classification — absence of shipped history is insufficient | Replaced with a three-clause non-fail-open rule: G2 shipped history live **or archived**, G3 candidate is the **sole extant nonterminal** shipment, G4 no abandoned record. Queued / abandoned / no-shipped-history cases enumerated; the later-numbered-candidate argument is stated explicitly via cardinality-1. | Decision D1 *genesis rule*; plan §3.1; 165.001-T (N5a–N5e), 165.002-T (G1–G4), 165.005-T, 165.009-T |
| 3 | P1 | Bootstrap authorization — Ship runs `pre_claim` twice | Re-scoped to **exactly two** audited forced invocations (U1 pre-branch, U2 pre-claim), each valid only on sole-token `PREDECESSOR_NOT_SHIPPED`, predecessor exactly `172-S`, HEAD + manifest match, and no other topology/check/closure/secrets violation; both audited; expiry on claim or any mismatch; third invocation explicitly unauthorized. | Decision D6; plan H6; `173-S` record |
| 4 | P1 | Dependency correction — 165.006-T consumes 165.003-T output | Edge `165.006-T <- 165.003-T` added and verified live; plan task table, dependency list, and shipment manifest note updated. | Backlog edge; plan §4 table + T6; `173-S` record; 165.006-T |
| 5 | P1 | Label parsing must not reuse `_tuple_of_str` | Retracted with the verified reason (artifact-ID pattern rejects `dag-root`, bricking every labelled record). A labels-specific fail-closed validator is mandated, with reader-level tests on both polarities including a positive anti-regression. | Plan §3.2; 165.002-T item 2; 165.001-T (N7a–N7f) |
| 6 | P1 | T2/T3 test consistency — no `_prior_shipment_id` pins | `_prior_shipment_id` expectations explicitly forbidden. Historical directional cases re-expressed as **raw `audit_sequencing` candidate** expectations, strict-xfail in T2 and flipped by T3; T2 atomically removes their claim-path meaning. Every task ends green. | 165.002-T disposition rule + per-case table; 165.003-T flip requirement; plan T2/T3 |
| 7 | P1 | Remove the scope escape hatch in 165.002-T | "Record a follow-up stash entry" retracted. Any surviving claim-path numeric inference blocks the task **and** `173-S`; no deferral, no stash, no advisory downgrade; escalation stays inside the shipment. | 165.002-T *Hardening F6*; plan T2; plan F6 |
| 8 | P1 | Atomic template parity | `165.010-T` merged into `165.008-T` (one task, one commit, sources + mirrors), archived with a forward reference, inbound edge removed first, off the manifest; size absorbed S → M; plan, manifest, and references updated. | 165.008-T; archived 165.010-T; `173-S` record; plan §4 + T7 |
| 9 | P1 | Durable closure-defect tracking | `FD0CCB42` **verified live** via fresh `backlogit_stash_get` and present in tracked `.backlogit/stash.jsonl` with `requires deliberation: yes`. `9AA34143` changed to `requires deliberation: yes` per P-021 C6, with the non-vacuous deliberation questions recorded; both re-verified after `backlogit_sync_index`. | Stash `FD0CCB42`, `9AA34143`; 165-F record |
| 10 | P2 | Narrow closure parity tests | Closure-evidence variants applied **only** to `explicit`; `declared_root`, `genesis`, `unsequenced` tested once each, plus one genesis-narrowness parity case. Vacuous cross-product removed; parity remains total over states. | 165.004-T *matrix shape*; plan T4 |
| 11 | P2 | Rollback — code rollback alone is insufficient | Documented explicitly: what is and is not code-reversible; a mandatory **migration ledger** emitted by the audit; **data-first** rollback ordering; and a narrowed claim (manual reconstruction) where no ledger exists. | Plan H4; decision D3; 165.003-T; 165.009-T item 6 |
| 12 | P2 | Reconcile `AF2890B7`'s archival summary | backlogit exposes **no** edit/append path for an archived stash entry (`backlogit_stash_get AF2890B7` → `not_found`), so the archived record is left **byte-for-byte intact** as intake history and the reconciliation is recorded through backlogit's supported **append-only item event log** on the feature it forward-references — final 8-task active set, closure-defect disposition now `FD0CCB42` rather than `165.007-T`, and the source-document tracking-status change. No destructive rewrite. | `165-F` comment event; 165-F description |

## Backlog Integrity Verification

Verified by a **fresh read** after all mutations and a successful
`backlogit_sync_index` — both through backlogit and by independent parse of the
`.backlogit/queue` Markdown records:

* **Manifest of `173-S`** (9 items, order): `165-F`, `165.001-T`, `165.002-T`,
  `165.003-T`, `165.004-T`, `165.005-T`, `165.006-T`, `165.008-T`, `165.009-T`.
  `165.007-T` and `165.010-T` absent; both present in `.backlogit/archive/`.
* **Dependency edges**: `165.001-T → 165.002-T`;
  `165.002-T → {165.003-T, 165.004-T, 165.006-T}`; `165.003-T → 165.006-T`;
  `165.004-T → 165.005-T`; `{165.005-T, 165.006-T} → {165.008-T, 165.009-T}`.
  Verified **acyclic**, **no dangling edges**, and **no manifest-order violation**
  (every prerequisite precedes its dependent in the stored manifest).
* **Sizing**: all eight tasks carry `size`, `complexity`, `size_source: agent`, and
  `size_ruleset_version: ah-stage-sizing-v1`. Recorded values: 165.001-T M/medium,
  165.002-T M/high, 165.003-T M/medium, 165.004-T S/medium, 165.005-T M/high,
  165.006-T S/low, 165.008-T M/medium, 165.009-T S/low. No task exceeds the 2-hour
  bound; the two `complexity: high` tasks are de-risked by a preceding
  test-authoring task rather than split, since splitting would break the atomicity
  the plan requires.
* **Stash persistence**: `FD0CCB42` and `9AA34143` both retrievable by fresh
  `backlogit_stash_get` and present in tracked `.backlogit/stash.jsonl`; both carry
  `REQUIRES DELIBERATION: yes`.
* **Document integrity**: plan and decision frontmatter parse as valid YAML; no
  unresolved template placeholder tokens outside code spans; all 23 repo-relative
  file references across both documents resolve to existing files — including
  `docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md`,
  which resolves for the first time.

## Merged Finding Counts

| Severity | Count | Status |
|---|---|---|
| P0 | **0** | — |
| P1 | **0** | All nine operator P1 findings resolved in-cycle; none deferred |
| P2 | 2 | P2-A externalized to stash `9AA34143` (backlogit rollup member set, second occurrence); P2-B accepted with recorded handling (`dag-root` has no mechanical enforcement) |
| P3 | 4 | P3-1 requires a recorded choice at execution; P3-2 accepted; P3-3 already satisfied; P3-4 advisory budget note on 165.008-T |

Neither open P2 is a same-contract-surface deferral: P2-A requires modifying
backlogit (a different repository surface, explicitly fenced out), and P2-B
requires a backlogit permission model that does not exist. Both are recorded with
handling rather than silently carried.

## Gate Decision

**decision: PASS**

Zero P0 and zero P1 findings. All twelve operator findings from the cycle-2
correction request are resolved in plan revision 3 and the corresponding backlog
records, and all nine P1s are closed in-cycle with no same-surface work deferred.

Harvest is complete and `173-S` is **staging-PR ready**, contingent on Ship using
the **two** audited `pre_claim --force` invocations authorized by decision D6 for
`173-S` only, under the per-invocation conditions recorded on the shipment.
