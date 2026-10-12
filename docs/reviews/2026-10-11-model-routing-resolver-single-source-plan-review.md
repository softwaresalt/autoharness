---
title: "Plan review: model routing resolver single source of truth (R1-A)"
description: "Multi-persona plan review of docs/plans/2026-10-11-model-routing-resolver-single-source-plan.md, run as a single-agent declared-degradation pass. Cycle 1 produced two P2 findings that were fixed; cycle 2 passes."
doc_type: review
review_target: docs/plans/2026-10-11-model-routing-resolver-single-source-plan.md
dispatch_mode: single-agent-declared-degradation
decision: PASS
review_cycles: 2
reviewed_utc: 2026-10-12
---

# Plan review: model routing resolver single source of truth (R1-A)

Review gate for `docs/plans/2026-10-11-model-routing-resolver-single-source-plan.md`
(deliberation `040-DL`, stash `BF66F08B`). Dates are UTC.

dispatch_mode: single-agent-declared-degradation

decision: PASS

## Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch` — this Stage session exposes no reviewer
  subagent dispatch surface. Declared fallback: single-agent persona pass. Every selected
  persona below was applied inline against its rubric, with one finding list per persona.
* `TOOL_DEGRADED: model-specific-review-routing` — `model_routing.anchor_review` is not
  dispatchable from this session. Declared fallback: same-model rubric pass for the
  cross-model personas. No persona was skipped.

## Persona coverage

| Persona | Mode | Triggered | Findings |
|---|---|---|---|
| Constitution Reviewer | inline pass | always-on | none |
| Python Reviewer | inline pass | always-on | A-F3 (P3, fixed), A-F4 (P3) |
| Scope Boundary Auditor | inline pass | always-on | A-F2 (P2, fixed) |
| Learnings Researcher | inline pass | always-on | A-F6 (P3) |
| Architecture Strategist | inline pass, same-model fallback | always | A-F1 (P2, fixed), A-F2 (P2, fixed) |
| Agent-Native Parity Reviewer | inline pass, same-model fallback | triggered: the plan adds an agent-facing CLI used by the Orchestrator | A-F5 (P3) |
| Security Lens Reviewer | inline pass, same-model fallback | not triggered: no auth, secrets, or trust-boundary surface; no routing value changes | none |

## Findings

### Cycle 1 (decision before revision: ADVISORY)

* **A-F1 [P2] Architecture.** A4's fail-closed precheck listed missing, empty, and
  version-less configs but omitted schema validation. The Orchestrator's H6 clause requires
  validating against the schema before resolving routes, so a schema-invalid config could
  have produced a resolved route and exit `0`. **Fixed:** A4's Change and Tests now apply the
  full precheck including validation against the schema version matching the config's own
  `schema_version` (the `verify_workspace` path; `jsonschema` is already a runtime
  dependency).
* **A-F2 [P2] Scope/Architecture.** The Outcome called the module the single source of
  truth, but the Stage and Ship escalation-directive prose still resolves by hand until R2.
  The claim over-stated the release. **Fixed:** the Outcome states exactly which consumers
  use the resolver, and the out-of-scope list names the Stage/Ship prose switch as R2.
* **A-F3 [P3] Python.** Reuse the existing `context_tier` enum constant. **Fixed:** A2 names
  `frontmatter_contract.CONTEXT_TIER_VALUES`.
* **A-F4 [P3] Python.** A3's delegation test asserts delegation by patching, which is
  brittle. **Acknowledged:** the implementer may assert by call recording; not blocking.
* **A-F5 [P3] Agent-Native Parity.** The CLI's exit-code contract (`0`/`1`/`2`) is documented
  in `USAGE` and the CHANGELOG by A4 but in the tuning guide only in R1-B's B11.
  **Acknowledged.**
* **A-F6 [P3] Learnings Researcher.** No contradiction with
  `docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md`: A5 preserves the
  directive tokens the verifier requires and uses an existence-gated fallback. No P0/P1.

### Cycle 2 (re-review after the fixes)

Re-read A4, A2, the Outcome, and the out-of-scope list; the dependency graph is unchanged
and acyclic (`A1 -> A2 -> A3`, `A2 -> A4 -> A5`); every unit stays within the file budget
(A4 has three files, one being a single-entry CHANGELOG). No new P0 to P3 findings.

## Hardening and verification gaps

Plan hardening was required (`Requires plan hardening: yes`) and is present
(`## Plan Hardening`: invariants I1 to I6, `ProposedAction`/`ActionRisk` table, added
verification, closure and rollback detail, capability-risk declaration). Runtime
verification and closure are specified for every runtime surface (A3, A4, A5). No gaps.

## Gate decision

No P0 or P1 findings; the two P2 findings were fixed and re-verified. Decision: **PASS**.
P3 items are acknowledged for awareness.

## Addendum: PR #513 review-fix cycle 1 (2026-10-12 UTC)

Append-only. The cycle 1 and cycle 2 records and the verdict above are unchanged. After the
staging PR (#513) received a Copilot review (review 5487147517, HEAD `cc06f41e`), Stage fixed
the findings that touch this plan and re-checked only the changed units as a single-agent
delta pass (same `TOOL_DEGRADED` declarations as above).

| Review thread | Change to this plan or its tasks | Commit |
|---|---|---|
| `PRRT_kwDORzpWpM6rWUXL` (empty `model_provider`) | A1 gains an empty `model_provider`/`reasoning_effort` vector and A2 a no-error scenario, pinning the rule this plan already stated; the error was in deliberation D4, now corrected | `82c8308c` |
| `PRRT_kwDORzpWpM6rWUYJ` (purity not enforced) | A2 adds the `forbid_io()` guard, `guarded_resolve`, the static import allowlist, and negative self-tests; invariant I7; A4's read-only claim (I5) is asserted by a tree-snapshot test | `b62cb4d1` |
| Operator answer to `040-DL` OQ1 to OQ9 | The `040-DL` defaults were accepted on 2026-10-12; no R1-A unit changed (it was never gated on an OQ) | `96a4503b` |

Delta persona pass over the changed units:

* **Python Reviewer.** The guard is stdlib only (`contextlib`, `unittest.mock`, `ast`) and
  runs under the canonical `unittest discover` gate. It replaces the `os.environ` attribute
  rather than using `patch.dict`, which avoids the hazard `tests/_env_patch.py` documents.
  The guard records violations so a swallowed `AssertionError` still fails at exit, and the
  static allowlist covers the import-time and function-local-import bypasses.
* **Scope Boundary Auditor.** The guard is a test helper, not a production change; A2 now
  lists three files (within the file budget A4 already uses) and stays one concern (the pure
  resolver and the proof that it is pure). No new config key, schema, or routing value.
* **Constitution Reviewer and Learnings Researcher.** No conflict. The negative self-tests
  follow the per-check red/green-pair posture of
  `docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md`.
* **Architecture Strategist.** The dependency graph is unchanged and acyclic
  (`A1 -> A2 -> A3`, `A2 -> A4 -> A5`), and the backlog edges match it exactly.

New findings: **A-F7 [P3]** A2 now carries the resolver, the guard, and the allowlist; size
stays `M` and it remains one sitting, acknowledged. **A-F8 [P3]** the runtime guard cannot
intercept the import machinery's own reads; the static allowlist is the declared complement,
acknowledged. No P0, P1, or P2 findings. The delta check supports the existing verdict:
the plan remains **PASS**.

## Addendum: PR #513 review-fix cycle 2 (2026-10-12 UTC)

Append-only. The cycle 1 and cycle 2 records, the cycle 1 addendum, and the verdict above are
unchanged. The staging PR (#513) received a second Copilot review (review 5494415746, HEAD
`e0051e68`). One of its three findings touches this plan; Stage fixed it and re-checked only
the changed units as a single-agent delta pass (same `TOOL_DEGRADED` declarations as above).

| Review thread | Change to this plan or its tasks | Commit |
|---|---|---|
| `PRRT_kwDORzpWpM6rkjEC` (alias detection only in `verify-workspace`, so the CLI could succeed for a forbidden 1.2.0 config) | Verified: `yaml.safe_load` erases anchors, aliases, and merge keys and the result is schema-valid plain data, while `yaml.parse` still exposes them. New unit **A2a** (`207.006-T`, `S` / `medium`) owns one shared function `model_routing_yaml.check_model_routing_yaml(raw_text, schema_version)`; A4 (`207.004-T`) calls it on the raw text **before** schema validation and exits `2` with `ROUTING_ANCHOR_UNSUPPORTED` for a 1.2.0 config, gains the CLI exit-`2` regression test, a 1.1.0-not-rejected case, and a delegation assertion; invariant I8 added; graph is now `A1 -> A2 -> A3` and `A2 -> A2a -> A4 -> A5` | `7ba1193a` |

Delta persona pass over the changed units:

* **Architecture Strategist.** The guard has one owner and two consumers (A4 here, R1-B B6
  across the shipment edge), and lands in R1-A because A4 is the first consumer and `215-S`
  blocks on `214-S`; placing it in R1-B would have shipped a CLI that accepts what
  `verify-workspace` rejects. It is a separate module because it imports `yaml`, which the A2
  static import allowlist forbids in the pure resolver, so resolver purity is untouched. The
  backlog edges are `207.006-T` after `207.002-T` and `207.004-T` after both; the `214-S`
  manifest order (`207-F`, `.001`, `.002`, `.003`, `.006`, `.004`, `.005`) honors every
  edge; the graph is acyclic and `autoharness gate dag-readiness` still reports
  `cycle_detected: false` and `ready_set: [209-S]`.
* **Python Reviewer.** The scan walks `yaml.parse` events, bounded to the `model_routing`
  value; a merge key is a plain `<<` scalar in key position, so a quoted `"<<"` key is not
  flagged. A scratch probe (not committed) confirmed that `yaml.parse` does not raise on an
  undefined alias while `yaml.safe_load` raises `ComposerError`, so the guard also reports the
  baseline-shaped document. A YAML syntax error is returned as `parse_error`, never raised.
* **Scope Boundary Auditor.** A2a adds two new files and one concern; A4 stays at three files
  and one concern; no config key, schema, policy, or routing value changes. D9 is read with
  D2's gate (error at 1.2.0, advisory below) and the row is annotated accordingly; a 1.1.0
  config with aliases is not rejected.
* **Constitution Reviewer and Learnings Researcher.** No conflict. The guard tests reuse the
  A2 `forbid_io()` harness, so the "pure over text" claim is asserted, not stated; the CLI
  read-only claim (I5) still rests on the tree-snapshot test, now including the guard
  scenarios.

New findings: **A-F9 [P3]** the CLI does not emit the advisory `warnings` for configs below
1.2.0 (its pinned document key set is unchanged); `verify-workspace` owns the advisory,
acknowledged. **A-F10 [P3]** the CLI's alias rejection is only reachable end to end once R1-B
makes 1.2.0 a valid version; A4's regression test reaches it now because the guard runs
before schema validation, acknowledged. **A-F11 [P3]** one new task (`207.006-T`), so `214-S`
holds six tasks (histogram `M:4`, `S:2`), acknowledged. No P0, P1, or P2 findings. The delta
check supports the existing verdict: the plan remains **PASS**.

## Addendum: PR #513 review-fix cycle 3 (2026-10-12 UTC)

Append-only. The cycle 1 and cycle 2 records, both earlier addenda, and the verdict above are
unchanged. The staging PR (#513) received a third Copilot review (review 5494859553) with one
finding, thread `PRRT_kwDORzpWpM6rlcW8` on `.backlogit/queue/215-S.md`. It concerns the R1-B
shipment, not an R1-A unit; Stage fixed it in the R1-B artifacts (commit `2f851bc2`; see the
R1-B review record's cycle 3 addendum) and ran a delta check on this plan's side only.

* **What changed here: nothing in R1-A.** `214-S` is byte-identical in membership and order
  (`207-F`, `.001`, `.002`, `.003`, `.006`, `.004`, `.005`; six tasks, `M:4`, `S:2`), and no
  `207.*` task body changed.
* **Cross-plan dependency check.** R1-A unit A5 (`207.005-T`) already specifies the
  Orchestrator wording this finding concerns ("the schema version matching the document's
  own `schema_version`", versioned mirror), so it is the Orchestrator owner of the new R1-B
  invariant I11 (every agent-executed config validator selects the schema by the document's
  own version). The R1-B unit B4a (`208.014-T`) supplies the `workspace-discovery`
  counterpart before B5, and B8/B9 the install and tune counterparts. No A5 change was
  needed, and A5 still does not edit any route literal or Step 0.
* **Graph.** `autoharness gate dag-readiness --json` reports `cycle_detected: false` and
  `ready_set: [209-S]`; the `214-S` manifest order honors every `207.*` edge.

New finding: **A-F12 [P3]** A5 is now cross-referenced as the Orchestrator owner of R1-B
invariant I11; its text, size (`M` / `low`), and acceptance criteria are unchanged,
acknowledged. No P0, P1, or P2 findings. The delta check supports the existing verdict: the
plan remains **PASS**.
