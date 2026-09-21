---
title: "Plan review attempt 02 - P004-OBSERVATION-GATE"
description: "Immutable per-attempt plan-review artifact recording the SECOND independent review of docs/plans/2026-09-18-p004-observation-gate-plan.md, the FIRST independent review of revision 7, dispatched under the continuing operator authorization that also permitted the revision-7 remediation cycle. GATE RESULT FAIL/BLOCK at P0 2 / P1 19 / P2 4. Revision 7 correctly retires the superseded 176-S / 168-F carriers, removes expected-green characterization entirely and replaces the caller-supplied declaration with a derived expected set. It is STILL NOT SHIPPABLE. The new blocking defect is that the derivation contract depends on a unique per-test AST sentinel that THE INSTALLED ACTOR DOES NOT PRODUCE - manifest variables_used.UNIMPLEMENTED_MARKER is the constant literal raise NotImplementedError(\"...\") with no qualified-test-id - so the gate would derive an empty or non-unique expected set on every real harness and adjudicate NO_OBSERVATION unconditionally. NO FINDING IS CLOSED."
doc_type: review
source: docs/reviews/review-history/2026-09-18-p004-observation-gate-plan-review-attempt-02.md
date: 2026-09-20
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 2
attempt_range: "02"
attempt_conformance: conforming
review_terminal: false
terminal_designation: not-terminal-remediation-authorized
terminal_disposition: FAIL-BLOCKING-P0-AND-P1
terminal_note: "Attempt 02 CONSUMES attempt number 2 and is NOT terminal. The operator directive that dispatched it authorizes a further remediation cycle after recording. This is a FAIL, not a convergence terminal and not a terminal PASS."
verdict_manifest: docs/reviews/2026-09-18-p004-observation-gate-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-p004-observation-gate-plan-review-attempt-01.md
plan_path: docs/plans/2026-09-18-p004-observation-gate-plan.md
plan_id: p004-observation-gate
reviewed_revision: 7
reviewed_content_head: 844cee9c
reviewed_content_state: committed
reviewed_branch: chore/stage-176-s-workflow-defects
plan_mutated_by_this_attempt: false
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 7
decision_state_machine: SM-1
feature_id: null
shipment_id: null
carriers_status: RETIRED-NEVER-EXECUTED
plan_withheld_from_harvest: true
review_cycle: 2
dispatch_mode: multi-agent
degraded_capabilities: []
security_lens_triggered: false
security_lens_note: "No Security Lens trigger fired. O15 (AST containment, grammar and resource bounds) and O18 (non-inert PREPARE registration) are recorded on the PYTHON and ARCHITECTURE axes as robustness-contract gaps in a planning document, not as live exploitable vulnerabilities: no gate code exists yet to attack."
gate_result: FAIL
decision: BLOCK
verdict_is_pass: false
verdict_at_entry: null
verdict_at_entry_disposition: PENDING-INDEPENDENT-REVIEW
verdict_at_entry_plan_revision: 7
verdict_at_entry_manifest_revision: 2
verdict_at_entry_publication_eligible: false
remediation_authorization: authorized-by-operator-directive-after-recording
remediation_performed: false
remediation_cycle_proposed: true
disposition: FAIL-BLOCKING-P0-AND-P1
p0_open: 2
p1_open: 19
p2_open: 4
p3_open: 0
open_findings_count: 25
blocking_findings_count: 21
open_findings: [O1, O2, O3, O4, O5, O6, O7, O8, O9, O10, O11, O12, O13, O14, O15, O16, O17, O18, O19, O20, O21, O22, O23, O24, O25]
blocking_findings: [O1, O2, O3, O4, O5, O6, O7, O8, O9, O11, O12, O13, O14, O15, O16, O17, O18, O19, O20, O21, O22]
closed_predecessor_findings: []
carried_predecessor_findings: [O1, O2, O3, O4, O5, O6, O7, O8, O9, O10]
findings_raised_at_this_attempt: [O11, O12, O13, O14, O15, O16, O17, O18, O19, O20, O21, O22, O23, O24, O25]
revision_7_addressed_pending_review_not_closed: [O1, O2, O3, O4, O5, O6, O7, O8, O9, O10]
finding_id_namespace: "O-prefix, reserved for p004-observation-gate; distinct from the S-prefix namespace of ship-harness-lifecycle-foundation"
cross_plan_findings:
  - finding: O22
    related_plan: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
    related_finding: S35
    note: "O22 and S35 are the SAME underlying defect observed from two plans. It is recorded in both namespaces because each plan is independently blocked by it: this plan's prerequisite cannot be satisfied by an activation task that names nonexistent paths."
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_note: "Revision 7 hardening is stronger than revision 6 - shell-free argv, an environment allowlist, an approval-gated rollback and an explicit AST no-execution rule - but it remains INSUFFICIENT because it hardens a derivation contract whose input the installed actor does not produce (O11), whose structured per-test outcomes the chosen runner cannot supply (O14), and whose evidence digest is self-referential (O16)."
personas_applied:
  - constitution
  - python
  - scope-boundary
  - learnings
  - architecture
  - agent-native-parity
personas_not_applied:
  - security-lens
tags:
  - "plan-review"
  - "attempt"
  - "fail"
  - "revision-7"
  - "derivation-contract-unproducible"
  - "portfolio-2026-09-18"
---

# Plan review attempt 02 — P-004 red-phase observation gate

## Reviewed subject

`docs/plans/2026-09-18-p004-observation-gate-plan.md` at **revision 7**,
committed base `844cee9c` on branch `chore/stage-176-s-workflow-defects`,
together with the governing decision at revision 7 (`SM-1`), the archived
`176-S` / `168-F` / `168.*` retirement records, and the mutable verdict manifest
at manifest revision 2.

This is the **first** independent review of revision 7. The plan has **no live
feature, tasks or shipment** and is withheld from harvest, which is itself the
structural remediation of `O1`.

## What revision 7 got right

* Retiring `176-S`, `168-F` and the `168.*` task set removes a live executable
  instruction set that specified a superseded architecture. This is the correct
  response to `O1` and is materially better than prose deferral.
* `expected_green_characterization` is **removed**, not renamed or deferred.
* The expected set is **derived** rather than caller-supplied, and callers are
  restricted to identifiers.
* The commands are stated as shell-free argv with an explicit, closed
  environment allowlist and explicit spawn / timeout / signal / decode mappings.
* Rollback requires fresh, live, SHA-bound approval with a dark/AFK halt.

**None of this makes the gate implementable**, for the reasons below.

## Findings

### `O11` — the actor does not produce the sentinel the gate derives from, and label mutation bypasses the gate (P0, BLOCKING)

The derivation contract requires that each generated harness test function
contain a **unique** sentinel:

```python
raise NotImplementedError("P004:<qualified-test-id>")
```

The installed actor renders this marker from the manifest variable
`UNIMPLEMENTED_MARKER`. Its live value is:

```
raise NotImplementedError("...")
```

A **constant literal with an ellipsis** — no `P004:` prefix, no qualified test
ID, and identical in every generated test. Against a real harness the gate
would derive **zero** sentinels matching its grammar, hit its own "at least one
expected test required" rule, and return `NO_OBSERVATION` unconditionally. The
plan's central mechanism has no producer, and the plan asserts the producer
exists.

Separately, the plan's surface declaration depends on task labels that Stage
edits directly through the backlog tool. A label mutation performed outside any
gate silently changes what the future gate will consider in scope, so the
authoritative input to a policy gate is writable by an unaudited path.

### `O12` — an unconditional `raise` makes the RED test vacuous (P1, BLOCKING)

A generated test whose body unconditionally raises fails **regardless of the
subject under test**. Such a test proves that a line of code runs, not that a
contract is unmet. The plan treats "every expected harness test fails with its
own marker" as evidence of a genuine RED phase, but an unconditionally-raising
test satisfies that condition even when the implementation is complete and
correct. The RED phase is therefore non-falsifiable as specified.

### `O13` — the expected set is neither shipment-scoped nor producer-owned (P1, BLOCKING)

The gate is invoked with a `shipment_id`, but derivation walks "the configured
test roots" wholesale. Nothing binds a discovered sentinel to the shipment
being gated, so tests generated for a *different* shipment enter the expected
set and block it. No producer owns the mapping from shipment to expected tests,
and no record carries it.

### `O14` — default `unittest` output cannot supply complete structured per-test results (P1, BLOCKING)

The result schema requires, per test, a `qualified_id`, an `outcome` drawn from
`fail | error | pass | skip`, the `marker_seen` and whether it correlates. The
plan obtains this by running `python -m unittest discover -s tests` and reading
its output. Default `unittest` output does not emit a complete per-test record:
passes are dots, skip reasons are aggregated, and failure text is
human-formatted with no stable machine contract. The schema cannot be populated
from the specified command, and the plan names no `TestResult` subclass,
no result-collecting harness and no alternative runner.

### `O15` — AST containment, grammar and resource bounds are undefined (P1, BLOCKING)

The plan correctly forbids import, execution and evaluation. It does not say:

* which paths may be parsed, or how they are contained — there is no
  workspace-root containment rule for the AST walk at all;
* what syntactic forms count as a sentinel — only a bare `raise` statement, or
  also one inside a conditional, a `try`, a nested function, a decorator or a
  class body;
* what qualifies a function as a "harness test function";
* any bound on file size, file count or recursion depth.

A syntax error in any file under the roots is likewise unmapped.

### `O16` — the evidence digest is self-referential (P1, BLOCKING)

`evidence_sha256` is defined as binding "the canonical JSON of the whole
result", and it is itself a field of that result. The definition is circular and
cannot be computed as written. The plan does not state the exclusion rule that
would make it well-defined.

### `O17` — the `OperationResult` adapter and transport schema are missing (P1, BLOCKING)

The gate is to be registered as one typed operation `harness/p004-gate` through
the `184-S` substrate, from which the CLI and MCP forms are "derived, not
separately implemented." The plan defines `P004GateResult` but never defines how
it maps onto the substrate's `OperationResult` envelope, what the transport
schema is, how exit codes derive from the token, or what the MCP tool signature
looks like. "Derived" is asserted, not specified, which is the same
unwired-prose defect `O7` raised at attempt 01.

### `O18` — PREPARE registration is not inert (P1, BLOCKING)

The rollout puts "implement `red_phase.py` **and register the operation**,
inert" in the PREPARE step. Registering an operation in a registry makes it
**discoverable and invocable** on both the CLI and MCP surfaces. That is not
inert, and it violates the PREPARE → VERIFY → ACTIVATE invariant the governing
decision's `D2` establishes, under which the activation commit is the single
moment a consumer becomes live.

### `O19` — the ACTIVATE unit does not enumerate its paths, files or manifest entries (P1, BLOCKING)

ACTIVATE is described as "one atomic commit wiring the operation into the
policy text, the Ship skill template and its installed mirror, with the harness
manifest refreshed." No path is named, no file count is given, and no manifest
entry is identified. `D11` requires the manifest to be a member of the commit
and of the rollback unit, and requires checksum parity verification per
refreshed entry — none of which can be checked against an unenumerated set.

### `O20` — the operation exposes resolver roots while claiming identifier-only inputs (P1, BLOCKING)

The plan states that callers "supply identifiers only", then gives
`evaluate_red_phase` the parameters `workspace_root`, `autoharness_home` and
`shipment_id`. Two of those three are **filesystem roots**, and they are
precisely the trust anchors the resolver's containment contract is built on. If
the operation is reachable over MCP, a caller supplies the roots the
containment checks are performed against, which inverts the trust boundary.

### `O21` — the policy command and the classification contradict each other (P1, BLOCKING)

The plan requires the canonical unittest command to exit **non-zero** as a
condition of `RED_CONFIRMED`, and simultaneously requires that established
unrelated tests may pass and that whole-suite discovery is retained. It also
requires that "no unexpected failure or error exists." On a workspace whose
established suite is green, the only source of a non-zero exit is the expected
harness failures — but the plan does not say that, and the stated conditions
are checkable in an order that yields different verdicts. The same tension
appears between the `SM-1` table in the governing decision and this plan's
outcome table.

### `O22` — `181.005-T` names paths that block this plan's prerequisite (P1, BLOCKING)

This plan's harvest gate requires `187-S` to have shipped. `187-S`'s activation
task, `181.005-T`, specifies `templates/agents/ship.md.tmpl` and
`.github/agents/ship.md`. **Neither exists**; the real artifacts are
`templates/agents/_ship.agent.md.tmpl` and `.github/agents/_ship.agent.md`.
This plan's prerequisite therefore cannot be satisfied as its owner currently
specifies it. Recorded here as well as in the lifecycle namespace (`S35`)
because each plan is independently blocked by it.

### `O23` — the `PR-3` environment override is not guaranteed (P2)

The test command is specified as inheriting the ambient environment plus
`{"PYTHONPATH": "src"}`. Nothing guarantees the override survives — an ambient
`PYTHONPATH` may be prepended or appended by the spawning layer, and the plan
does not say whether the value replaces or merges. Two implementations would
import different modules from the same specification.

### `O24` — archived `168.009-T` omits the retirement markers its siblings carry (P2)

`168.009-T` is archived and is titled `P-004 T0 (BOOTSTRAP)` — a task whose
stated purpose was to make `176-S` executable. Its siblings retired at revision
7 carry `retired`, `superseded`, `never-executed` labels and
`retired_never_executed: true`. `168.009-T` carries none of them, and its labels
remain `[bootstrap, p-004, policy, docs]`. It is now an orphan referencing a
retired shipment without any record of why it is inert.

### `O25` — the archived `176`/`168` records carry copied, contradictory rationale (P2)

The retirement clauses assert both that the design is superseded and must never
be restored, and that the requirement is merely deferred pending a re-harvest
gate. The `NOREVIVE` and `REHARVEST` clauses state different things about the
same records, and the text is identical across thirteen records, so the
contradiction is reproduced thirteen times rather than reasoned once.

## Carried open without re-argument

`O1`–`O10` are **carried OPEN**. Revision 7 lists all ten as
`findings_addressed_pending_review`, and the remediation is substantive —
particularly `O1`, whose carriers are genuinely gone, and `O3`, whose subject is
genuinely removed. **Addressed is not closed.** This attempt closes none of
them because the remediation is not independently verifiable while the
derivation contract has no producer (`O11`), the result schema cannot be
populated by the specified runner (`O14`) and the operation's transport
contract is unspecified (`O17`). `O4` in particular cannot be closed by a
derivation rule whose sentinel nothing emits.

## Persona coverage

| Persona | Applied | Principal contributions |
|---|---|---|
| Constitution | yes | `O18` (non-inert PREPARE vs `D2`), `O19` (`D11` enumeration), `O21` |
| Python | yes | `O11` (marker ground truth), `O14` (`unittest` result surface), `O15` (AST bounds), `O16` (digest circularity), `O23` |
| Scope boundary | yes | `O19`, `O22` (cross-plan prerequisite), `O24`, `O25` |
| Learnings | yes | Cited `P-007` `G1`–`G9` as the approval pattern revision 7 correctly adopted; cited attempt-01 `O1` as the precedent for treating a queued manifest as executable |
| Architecture | yes | `O13` (shipment scoping), `O17` (transport schema), `O20` (trust-boundary inversion) |
| Agent-Native Parity | yes | `O17`, `O20` — the CLI and MCP forms are asserted to be derived but nothing enforces the parity |
| Security Lens | no | Not triggered; see `security_lens_note` |

`dispatch_mode: multi-agent`. No capability ran degraded at this attempt.

## Gate result

**FAIL / BLOCK**, under the standing decision rule (`P0` or `P1` present is
`FAIL`; `P2`-only is `ADVISORY`; `P3`-or-none is `PASS`).

Counts: `P0` 2, `P1` 19, `P2` 4, `P3` 0 — **25 findings open**, 21 blocking.

**No finding was closed at this attempt.** No severity was lowered, and no
finding was deferred or waived.

`SM-2` `HARVEST_ADMITTED` remains **SHUT**. The plan is **not
publication-eligible**, and its harvest gate is independently shut: `185-S` and
`187-S` have not shipped.

## Authorization boundary

This attempt **consumed attempt number 2** and is **not terminal**. The
operator directive that dispatched it authorizes a further remediation cycle
after recording.

This review **performed no remediation**: no plan, source, template, skill,
manifest, test, backlog carrier, stash entry, checkpoint or GitHub object was
mutated. Only this immutable artifact and the mutable verdict manifest were
written.

## Scope statement

Reviewed: the plan at revision 7; the governing decision at revision 7 and its
`SM-1` table; the archived `176-S`, `168-F` and `168.*` retirement records;
`.autoharness/harness-manifest.yaml` as ground truth for `O11`; and
`181.005-T` as it bears on this plan's harvest prerequisite (`O22`).

Not reviewed: the harness-architect actor's content beyond the marker variable;
the `184-S` / `185-S` operation substrate; the lifecycle plan except where it
gates this one.
