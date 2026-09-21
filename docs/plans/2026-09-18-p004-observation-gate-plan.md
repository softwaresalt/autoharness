---
title: "P-004 red-phase observation gate"
description: "Replaces the P-004 red-phase precondition's agent-prose observation with a typed, shell-free, machine-checkable gate. The expected test and marker set is DERIVED by the gate from the generated harness itself and is never supplied by a caller. The gate is exposed as ONE registered operation reachable identically from the CLI and over MCP. This plan is WITHHELD FROM HARVEST: it has no live feature, tasks or shipment, and Stage re-harvests it fresh only after 185-S and 187-S have shipped and this plan holds an independent PASS."
doc_type: plan
source: docs/plans/2026-09-18-p004-observation-gate-plan.md
date: 2026-09-18
plan_id: p004-observation-gate
plan_path: docs/plans/2026-09-18-p004-observation-gate-plan.md
plan_role: active-withheld-from-harvest
revision: 7
revision_scope: full-rewrite-current-state-addressing-attempt-01-findings
revision_7_note: "Revision 7 is a REWRITE as a current-state contract, not a correction log. It addresses independent attempt 01 (FAIL against revision 6, findings O1-O10). FOUR STRUCTURAL CHANGES. (1) The superseded carriers are gone: 176-S, 168-F and every live 168 task are ARCHIVED AS RETIRED, never claimed and never executed, because a queued shipment manifest is an executable instruction set and prose deferral is insufficient (O1). This plan now has NO live tasks and NO shipment, and is withheld from harvest. (2) expected_green_characterization is REMOVED ENTIRELY (O3). (3) The expected test and marker set is DERIVED by the gate through safe AST parsing of the generated harness and is NEVER caller-supplied (O4). (4) The commands are shell-free argv specifications with an allowlisted PYTHONPATH=src environment override (O5), the API is typed with an exact result schema (O7), and the gate is ONE registered operation with CLI and MCP parity (O7). Rollback requires fresh live SHA-bound operator approval (O9), and 191-S - which revision 6 named as a prerequisite - is RETIRED, never executed, its deliverable satisfied by direct Ship remediation commits (O2)."
verdict: null
verdict_is_pass: false
verdict_asserted_against_revision: null
disposition: PENDING-INDEPENDENT-REVIEW
publication_eligible: false
publication_eligible_basis: "No independent review has judged revision 7. Attempt 01 returned FAIL against revision 6."
last_independent_verdict: FAIL
last_independent_verdict_attempt: 1
last_independent_verdict_revision: 6
verdict_note: "NO VERDICT IS ASSERTED AGAINST REVISION 7. The verdict manifest at review_manifest is the SOLE AUTHORITY for this plan's review state; this field is a pointer, not a second record. Revision 7 remediates O1-O10 and CLOSES NOTHING."
awaiting_attempt: 2
awaiting_attempt_against_revision: 7
latest_attempt: 1
latest_attempt_reviewed_revision: 6
review_manifest: docs/reviews/2026-09-18-p004-observation-gate-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 7
decision_state_machine: SM-1
source_stash_ids:
  - 76EBDE6D
feature_id: null
shipment_id: null
carriers_status: RETIRED-NEVER-EXECUTED
retired_carriers:
  - 176-S
  - 168-F
  - 168.001-T
  - 168.002-T
  - 168.003-T
  - 168.004-T
  - 168.005-T
  - 168.006-T
  - 168.007-T
  - 168.008-T
  - 168.010-T
  - 168.011-T
  - 168.012-T
retired_carriers_note: "ARCHIVED AS RETIRED, SUPERSEDED, NEVER CLAIMED AND NEVER EXECUTED. They encoded the superseded design that attempt-01 finding O1 blocked. The original defect linkage is preserved on each archived record: THE REQUIREMENT SURVIVES, ONLY THE CARRIER DOES NOT. These records are NEVER RESTORED; re-harvest is forward-only."
unit_role: gate-implementation
supersedes_plan: docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
harvest_gate: "Stage re-harvests a FRESH feature, task set and shipment only after BOTH 185-S and 187-S have shipped AND this plan holds an independent PASS. No empty queued shipment is created in the interim."
depends_on_units:
  - 185-S
  - 187-S
depends_on_units_note: "185-S delivers the operation registry and transport substrate (via the archived 184-S) that this gate registers into. 187-S delivers the harness-surface resolver this gate calls as a precondition. Neither has shipped."
retired_prerequisite_shipment: 191-S
retired_prerequisite_note: "Revision 6 named 191-S as a prerequisite for actor P-004 conformance. 191-S is RETIRED, NEVER CLAIMED AND NEVER EXECUTED; the conformance it was to deliver was achieved directly by Ship review-remediation commits 1cb0dc8140a809d63c3193d58431cd14408788b7 and b8ac632a93751fb29c51a8e5bf0f5e036b65cfb3. Nothing here may be read as claiming 191-S shipped."
gate_module: src/autoharness/gates/red_phase.py
gate_operation_id: harness/p004-gate
gate_cli: "autoharness op harness p004-gate --shipment <id> --json"
expected_set_is_caller_supplied: false
expected_green_characterization: removed
resolver_module: src/autoharness/harness_surfaces.py
resolver_consumption: direct-python-function-call
resolver_state_is_persisted: false
no_harness_maps_to: NO_OBSERVATION
requires_plan_hardening: true
hardening_rationale: "Implements a mandatory policy gate that every future shipment traverses, spawns subprocesses, parses source with AST, and registers a new operation on the CLI and MCP surfaces simultaneously. A false PASS here silently disables P-004 workspace-wide."
tags:
  - p-004
  - gate
  - policy
  - python
---

# P-004 red-phase observation gate

## Status — withheld from harvest

**This plan has no live feature, no live tasks and no shipment.** The carriers
that once held them — `176-S`, `168-F` and the `168.00x-T` / `168.01x-T` task
set — are **archived as retired, superseded, never claimed and never
executed**. They encoded the superseded design, and attempt-01 finding `O1`
held that leaving them live while deferring them in prose is insufficient,
because **a queued shipment manifest is an executable instruction set, not
commentary**.

**Re-harvest is forward-only.** Stage creates a **fresh** feature, task set and
shipment against the then-current repository state, and only when **all three**
hold:

1. `185-S` has shipped — the operation registry and transport substrate exist;
2. `187-S` has shipped — the harness-surface resolver exists;
3. this plan holds an **independent PASS**.

The archived records are **never restored**, and **no empty queued shipment**
is created in the interim.

## The defect

P-004 requires that, before Ship executes a task, the generated harness is
observed **RED**. Today that observation is performed by agent prose: the agent
runs commands, reads output and asserts a conclusion. Nothing is typed, nothing
is machine-checkable, and a misread — or an invented — conclusion silently
disables the gate for every shipment in the workspace.

## Contract

### What P-004 requires — stated once, exactly

A gate result of `RED_CONFIRMED` requires **all four**, with no exceptions:

1. the canonical compile command succeeds;
2. the canonical unittest command exits **non-zero**;
3. **every** expected harness test fails **with its own expected marker**;
4. **no unexpected failure or error exists.**

**There is no expected-green characterization.** The concept is removed from
this plan entirely, not deferred and not renamed. Established unrelated tests
may pass — whole-suite discovery is retained — but passing is never *asserted*
about any test, and the gate never characterizes a green outcome as expected.

### The expected set is derived, never supplied

The caller supplies **identifiers only**. It never supplies test IDs, markers,
argv, environment or an expected set.

* Each generated harness test function in the configured test roots contains a
  unique sentinel:

  ```python
  raise NotImplementedError("P004:<qualified-test-id>")
  ```

* The gate parses those roots with a **safe AST walk** — `ast.parse` only, with
  **no import, no execution and no evaluation** of the parsed source.
* For each discovered sentinel, the marker payload after `P004:` MUST equal the
  **qualified discovered test ID** of the function containing it. A mismatch is
  a derivation failure.
* **At least one** expected test must be derived.

### Outcome classification

| Final gate token | Reached when |
|---|---|
| `RED_CONFIRMED` | all four requirements above hold |
| `RED_NOT_CONFIRMED` | observation completed, but any requirement fails — compile failure, an expected harness test that passes, a marker that does not correlate, or any unexpected failure or error |
| `NO_OBSERVATION` | no trustworthy observation could be taken |

`NO_OBSERVATION` is reached by: discovery failure, a unittest loader error, an
empty derived expected set, a marker/ID correlation failure, or a
harness-surface resolver precondition that did not return `HARNESS_READY`.
**`NO_OBSERVATION` is classified FAIL, never PASS.**

Any **unexpected** failure, error **or skip of an expected harness test**
blocks. A skip is not a pass and is not ignorable: an expected harness test
that is skipped was not observed failing.

### Resolver precondition

The gate calls `resolve_harness_surfaces` in
`src/autoharness/harness_surfaces.py` **directly as a Python function** and
emits the returned `inputs_sha256` into its own evidence. It does **not** shell
out to the resolver CLI and does **not** read any persisted readiness state —
none exists.

| Resolver state | Gate behaviour | Error-detail exit |
|---|---|---|
| `HARNESS_READY` | proceed to command execution | — |
| `NO_HARNESS` | **no command is executed**; final token `NO_OBSERVATION` | 1 |
| `UNRESOLVED` | **no command is executed**; final token `NO_OBSERVATION` | 2 |

`NO_HARNESS` and `UNRESOLVED` are **preserved as distinct error detail with
distinct exit codes** even though both collapse to the same final gate token.
Neither executes any command.

### Commands — shell-free argv specifications

Compilation:

```
argv = ["python", "-m", "py_compile", "src/autoharness/cli.py"]
env  = inherited, unmodified
```

Test execution — the canonical command is
`PYTHONPATH=src python -m unittest discover -s tests`. The leading
`PYTHONPATH=src` is **not a shell construct** and is not passed to a shell. It
is parsed against a **closed allowlist of environment assignments** —
`PYTHONPATH` only — and applied as an environment override:

```
argv = ["python", "-m", "unittest", "discover", "-s", "tests"]
env  = inherited + {"PYTHONPATH": "src"}
```

An assignment prefix naming any variable outside the allowlist is a
**derivation failure**, not a silently-dropped token.

Both invocations run with `shell=False`, `cwd` = the workspace root, and a
bounded timeout. Every outcome is mapped explicitly:

| Condition | Mapping |
|---|---|
| Spawn failure (`FileNotFoundError`, `PermissionError`) | `NO_OBSERVATION` |
| Timeout expiry | `NO_OBSERVATION` |
| Terminated by signal | `NO_OBSERVATION` |
| Output decode failure | `NO_OBSERVATION` |
| Clean exit, any code | observation proceeds; the code is recorded |

**The caller never supplies argv or env.** Both are constructed by the gate
from the canonical specification above.

## Typed API

Module `src/autoharness/gates/red_phase.py`:

```python
class ResolverPrecondition(str, Enum):
    HARNESS_READY = "HARNESS_READY"
    NO_HARNESS = "NO_HARNESS"
    UNRESOLVED = "UNRESOLVED"

class GateToken(str, Enum):
    RED_CONFIRMED = "RED_CONFIRMED"
    RED_NOT_CONFIRMED = "RED_NOT_CONFIRMED"
    NO_OBSERVATION = "NO_OBSERVATION"

@dataclass(frozen=True)
class ExpectedTest:
    qualified_id: str
    marker: str
    source_path: str          # root-relative, redacted

@dataclass(frozen=True)
class ObservedTest:
    qualified_id: str
    outcome: str              # "fail" | "error" | "pass" | "skip"
    marker_seen: str | None
    marker_correlates: bool

@dataclass(frozen=True)
class CommandObservation:
    argv: tuple[str, ...]
    env_overrides: Mapping[str, str]
    exit_code: int | None
    duration_ms: int
    failure_mode: str | None  # spawn | timeout | signal | decode | None

@dataclass(frozen=True)
class P004GateResult:
    schema_version: int
    token: GateToken
    reason_code: str
    shipment_id: str
    resolver_precondition: ResolverPrecondition
    resolver_inputs_sha256: str | None
    expected: tuple[ExpectedTest, ...]
    observed: tuple[ObservedTest, ...]
    unexpected_failures: tuple[str, ...]
    commands: tuple[CommandObservation, ...]
    evidence_sha256: str
    errors: tuple[str, ...]

def evaluate_red_phase(
    *,
    workspace_root: Path,
    autoharness_home: Path,
    shipment_id: str,
) -> P004GateResult: ...
```

`resolver_precondition` is carried **separately** from `token`, so a
`NO_OBSERVATION` caused by an unusable harness surface is distinguishable from
one caused by a loader error. `evidence_sha256` binds the canonical JSON of the
whole result with domain separation, and `resolver_inputs_sha256` carries the
resolver's own digest unmodified.

## One registered operation

The gate is registered as **exactly one** typed operation, `harness/p004-gate`,
through the registry and transport substrate delivered by the archived `184-S`
and shipped by `185-S`. From that single registration the CLI form
`autoharness op harness p004-gate` and the MCP form are **derived**, not
separately implemented.

**Human and agent paths use the same operation.** The Ship skill invokes the
operation and records the returned `P004GateResult` **verbatim**; it does not
run unittest itself, does not parse runner output and does not re-derive the
expected set. This is what prevents the prose surface and the executable
surface from diverging.

## Rollout — TDD order

1. **RED** — failing contract tests for derivation, classification, command
   specification and the resolver precondition. Negative tests must be
   **non-vacuous**: each asserts a specific wrong outcome is *not* produced, and
   composed states are exercised — a passing expected test alongside a failing
   one, a correct marker alongside a mismatched one, an unexpected error
   alongside a correct expected failure.
2. **PREPARE** — implement `red_phase.py` and register the operation, inert.
3. **VERIFY** — evidence over every classification row, every command failure
   mode and every resolver precondition.
4. **ACTIVATE** — one atomic commit wiring the operation into the policy text,
   the Ship skill template and its installed mirror, with the harness manifest
   refreshed in the same commit and the same rollback unit (`D11`).

**Careful mode and freeze scope.** The activation commit freezes its scope to
the enumerated files; no opportunistic edit enters it.

## Rollback

Rollback is a `git revert` of the single ACTIVATE commit, restoring the policy,
the skill template, the installed mirror and the manifest entry **together as
one unit**.

**It requires FRESH, LIVE operator approval, obtained immediately before the
revert command is issued and bound to the exact activation commit SHA.** The
approval must name that SHA and is re-validated in the moment the command is
about to run. An approval obtained earlier in the session, or for a different
SHA, is not an approval. If the operator is unreachable, dark or AFK, the agent
**halts and reports**. Proceeding without that approval is a P-005 violation.
**There is no unconditional revert path.**

## Out of scope

The harness-architect actor's content or conformance; the harness-surface
resolver itself (`187-S`); the operation registry and transport substrate
(`184-S` / `185-S`); any change to the canonical commands; any change to P-002,
gate semantics, grants, `--force` or waivers.

## Risks

| Risk | Mitigation |
|---|---|
| A false `RED_CONFIRMED` silently disables P-004 workspace-wide | Four independent requirements, all derived; `NO_OBSERVATION` is FAIL; non-vacuous negative tests |
| AST parsing executes untrusted source | `ast.parse` only — no import, no execution, no evaluation |
| A caller injects an expected set or argv | Callers supply identifiers only; argv and env are constructed by the gate |
| The prose and executable surfaces diverge | One registered operation; the skill records the result verbatim |
| Rollback destroys working state without consent | Fresh, live, SHA-bound approval revalidated immediately before the command |

## Hardening review

### Adversarial questions

* *Can a shipment pass the gate with no harness tests?* No — an empty derived
  expected set is `NO_OBSERVATION`, which is FAIL.
* *Can a skipped harness test be counted as failing?* No — skip is a distinct
  observed outcome and blocks.
* *Can `PYTHONPATH=src` be turned into shell injection?* No — it is parsed
  against a closed allowlist into an environment override; `shell=False`
  throughout.
* *Can a stale readiness answer authorize execution?* No — the resolver
  persists nothing and is called directly at evaluation time.

### Blast radius

A mandatory policy gate traversed by every future shipment; subprocess
execution; AST parsing of workspace source; simultaneous CLI and MCP surface
registration.

### Verification floor

Targeted RED and GREEN on the gate's own test modules; the full canonical
suite; the canonical compile command; and evidence covering every
classification row, every command failure mode and every resolver precondition
state.
