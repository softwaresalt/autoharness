---
title: "Model routing resolver: a single deterministic source of truth for route resolution (R1-A)"
description: "Plan for the first release unit of the 040-DL model-routing design. Pin today's route-resolution semantics as language-neutral vectors, extract them into one pure module, make verify-workspace delegate to it with unchanged outputs, expose it as a read-only `autoharness routing resolve` CLI, and let the Orchestrator declare invocation routes from that CLI with a declared prose fallback. No new config keys, no schema change, no routing value change."
doc_type: plan
status: reviewed
created: 2026-10-11
source_stash: BF66F08B
source_deliberation: docs/decisions/2026-10-11-model-routing-v2-deliberation.md
deliberation_id: 040-DL
baseline_document: docs/design-docs/model-routing-v2.md
release: "R1-A"
harvested_feature: "207-F"
harvested_shipment: "214-S"
successor_plan: docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md
review_record: docs/reviews/2026-10-11-model-routing-resolver-single-source-plan-review.md
requires_plan_hardening: "yes"
---

# Model routing resolver: a single deterministic source of truth (R1-A)

## Outcome

After this plan ships:

* `src/autoharness/model_routing.py` is the one definition of route resolution (tier
  fallback, role routes, `context_tier`, nested/legacy/tier3 escalation, both-present
  ambiguity, role-scoped same-route guard). It is a pure function over parsed config data.
* Language-neutral JSON vectors pin that behavior, so a later Go port (`F194A1D8`) can run
  the same cases.
* `verify_workspace.py` and the install variable derivation delegate to the module. Public
  outputs (`targeted_checks` shapes, rendered variables) are unchanged.
* `autoharness routing resolve --workspace <path> --site <stage|ship|orchestrator>
  [--kind route|escalation] --json` prints one JSON document and exits `0` (resolved), `1`
  (resolved with a declared degradation, for example a same-route escalation), or `2`
  (unresolved or invalid config; fail closed).
* The Orchestrator declares its Stage and Ship invocation routes from that CLI when it is
  available (`TOOL_OK`) and otherwise follows the existing prose with
  `TOOL_DEGRADED: routing-resolver-cli`. Its config-validation clause validates against the
  schema version matching the document's own `schema_version`. The Stage and Ship
  agents' own escalation-directive prose still resolves by the existing prose until R2, so
  after this release the resolver is the single source for verification, install derivation,
  the CLI, and the Orchestrator, and is not yet the only executed definition.
* No config key, schema, policy, or routing value changes. The dogfood
  `.autoharness/config.yaml` is untouched.

## Problem Frame

Route precedence is implemented in `src/autoharness/verify_workspace.py` as private helpers
(`_model_routing_tier_dict`, `_tier_fallback_dict`, `_resolve_role_route_field`,
`_resolve_context_tier`, `_derive_tier_route_variables`,
`_derive_orchestrator_route_variables`, `_derive_role_route_variables`,
`_effective_escalation_route_for_role`, `_effective_escalation_context_tier_for_role`,
`_escalation_route_has_any_field`, `_add_role_route_resolution_check`,
`_add_escalation_route_resolution_check`) and re-described in prose in the Orchestrator,
Stage, and Ship templates and in `escalation-protocol.instructions.md`. At runtime the
Orchestrator follows the prose by reading `.autoharness/config.yaml`, so an LLM executes the
precedence. The copies have drifted: stale route literals in the Orchestrator mirror and in
the escalation-protocol instruction, and a Stage escalation that resolves to Stage's own
route (`1F13DF5E`, `3C19FA0F`; deliberation `040-DL` Finding 4).

This release removes the duplication without changing behavior. It is the prerequisite for
the catalog and bindings release (`R1-B`), which adds new routing keys. Adding keys on top
of three hand-maintained copies of the precedence would multiply the drift.

Scope boundaries (P-021 C1):

* In scope: the resolver module, vectors, delegation, CLI, the Orchestrator directive.
* Out of scope: new config keys (R1-B), escalation `chain` and review diversity (R2/R3),
  switching the Stage and Ship escalation-directive prose to the CLI (R2), Stage and
  Orchestrator route data (`3C19FA0F`, `1F13DF5E`), the stale
  `escalation-protocol.instructions.md` prose (recorded as an R2 follow-up), removal of
  frontmatter route fields (`79021C29`).

## Requirements Trace

| # | Requirement (040-DL decision) | Unit |
|---|---|---|
| RA1 | Today's resolution semantics are pinned as language-neutral vectors before any refactor (D5) | A1 |
| RA2 | One pure module implements those semantics, with no I/O (D5) | A2 |
| RA3 | `verify_workspace` and install derivation delegate to it; public outputs unchanged (D5, D10) | A3 |
| RA4 | Read-only `routing resolve` CLI with a pinned document shape and fail-closed exit codes (D5, D9) | A4 |
| RA5 | Orchestrator declares routes from the CLI with a declared prose fallback; validates config against the matching schema version (D5, D9, P-012) | A5 |
| RA6 | No new config keys, schema, policy, or routing-value change (D1, D11) | all (guard in A3 and A5 acceptance) |

## Planned Resolver Contract (shared with R1-B)

Defined here so R1-B can extend it. Names are the planned public surface of
`src/autoharness/model_routing.py`.

```python
ROUTE_FIELDS = ("model_family", "model_provider", "reasoning_effort", "context_tier")
ROLE_DEFAULT_TIER = {"orchestrator": "tier2", "stage": "tier3", "ship": "tier2"}

@dataclass(frozen=True)
class ResolvedRoute:
    site: str                          # "stage", "ship", "orchestrator"
    kind: str                          # "route" | "escalation"
    model_family: str
    model_provider: str
    reasoning_effort: str
    context_tier: str                  # never empty; "default" when unset everywhere
    tier_class: str | None             # "tier1" | "tier2" | "tier3" | None when unknown
    resolution_chain: tuple[str, ...]  # ordered provenance, e.g. ("stage.model_family", "tier3.model_provider")
    degraded: tuple[str, ...]          # e.g. ("ESCALATION_DEGRADED: same-route",)
    errors: tuple[str, ...]            # e.g. ("AMBIGUOUS_ESCALATION_CONFIG", "ROUTING_UNRESOLVED: model_family")
    def to_document(self) -> dict[str, Any]: ...

def resolve_site(config: Mapping[str, Any], site: str, *, kind: str = "route",
                 installed_roles: frozenset[str] = frozenset()) -> ResolvedRoute: ...
```

Rules reproduced exactly from today's code (no new behavior):

* A tier may be a plain string (treated as `model_family`; no other field) or a mapping
  whose `model` backs `model_family` when `model_family` is unset.
* A role route resolves each field independently: role block, then the role's default tier,
  then (for `context_tier` only) the terminal `default`.
* Escalation: nested `<role>.escalation` if it declares any of `model_family`,
  `model_provider`, `reasoning_effort`; else legacy flat `escalation`; each unset field
  falls back to `tier3` and never to the other source. Both nested and flat declared is
  `AMBIGUOUS_ESCALATION_CONFIG`.
* Same-route guard compares `(model_family, model_provider, reasoning_effort)` only,
  role-scoped; a field unset on either side carries no signal; `context_tier` is excluded.
* Unresolved `model_family` is an error. Empty `model_provider`/`reasoning_effort` is valid
  ("leave empty to use the model default").

CLI document (`schema_version: "1.0.0"`, keys pinned by the A4 test): `schema_version`,
`site`, `kind`, `resolved` (the four fields plus `tier_class`), `resolution_chain`,
`degraded`, `errors`, `exit_code`. Publishing a JSON Schema for this document is deferred
to R2/R3, when more consumers exist; the keys are pinned by test until then.

## Implementation Units

Execution posture for every unit: characterization-first. A1 pins today's behavior while the
old code is still the only implementation; A2 to A5 then move behavior without changing it.
Canonical test gate for every code unit:
`$env:PYTHONPATH='src'; python -m unittest discover -s tests`.

### A1: Pin today's route-resolution semantics as language-neutral vectors

**Files (2):** `tests/fixtures/model_routing/existing-semantics.json` (new),
`tests/test_model_routing_existing_semantics_vectors.py` (new).

**Change:** Author about 14 cases as JSON (`config` in, expected resolution out): tier-only
config; role override with only some fields; Stage with no route (falls to `tier3`); Ship
(falls to `tier2`); Orchestrator `context_tier` falling to `tier2`; a legacy plain-string
tier; unset `model_family`; nested escalation with partial fields (per-field `tier3`);
legacy flat escalation used when no nested; both-present `AMBIGUOUS_ESCALATION_CONFIG`;
same-route guard true; same family but different provider (not degraded); `context_tier`
difference only (still same-route); installed-role widening. The test runs each case through
the **current** `verify_workspace` helpers and asserts the fixture, so it passes on main
today and fails if any later refactor changes behavior.

**Tests (scenarios):** every vector equals current-helper output; vector ids are unique; the
fixture is valid JSON with no Python-specific constructs.

**Acceptance criteria:** the test passes against unmodified `verify_workspace.py`; no
production file is modified.

**Harness surface:** `harness-surface:none` (no `src/` file). **Size/complexity:** `S` /
`medium`. **Depends on:** none.

### A2: Pure resolver module

**Files (2):** `src/autoharness/model_routing.py` (new),
`tests/test_model_routing_resolver.py` (new).

**Change:** Implement `ResolvedRoute` and `resolve_site` per the planned contract. Reuse the
single `context_tier` enum, `frontmatter_contract.CONTEXT_TIER_VALUES` (194-F H-C5), rather
than a second copy. No I/O, no imports from `verify_workspace` (avoid a cycle).

**Tests (scenarios):** the A1 vectors parametrized against `resolve_site`; ambiguity returns
the error with no per-role resolution; unresolved `model_family` returns
`ROUTING_UNRESOLVED`.

**Acceptance criteria:** every A1 vector passes through `resolve_site`; the module performs
no file or environment access (asserted by a test that runs it on plain dicts only).

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** A1.

### A3: Delegate verify_workspace and install derivation to the resolver

**Files (2):** `src/autoharness/verify_workspace.py`,
`tests/test_verify_workspace_resolver_delegation.py` (new).

**Change:** Replace the bodies of the helpers listed in the Problem Frame with calls into
`model_routing`, keeping every function name, signature, and return shape so existing tests
and the install variable derivation keep working. Do not touch check keys or error strings
(tests and `verify-harness` consume them).

**Tests (scenarios):** the A1 characterization test still passes unchanged; a delegation test
asserts each helper returns a value computed by `model_routing` (by patching the module and
asserting it is called); the existing `test_route_variable_precedence`,
`test_context_tier_resolution`, `test_escalation_*`, and `test_verify_workspace` suites pass
unmodified.

**Acceptance criteria:** the whole suite passes with no edits to any pre-existing test; the
diff to `verify_workspace.py` removes logic (net deletions) and adds no new check key.

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** A2.

### A4: `autoharness routing resolve` CLI

**Files (3):** `src/autoharness/cli.py`, `tests/test_cli_routing_resolve.py` (new),
`CHANGELOG.md` (one entry).

**Change:** Add a `routing` command with a `resolve` subcommand modeled on `harness resolve`
(argparse, `allow_abbrev=False`, one JSON document plus LF on stdout, nothing on stderr after
a successful parse). `--workspace` is required and non-empty. The command reads
`.autoharness/config.yaml` with `yaml.safe_load`, then applies the E8B5B3C5/H6 fail-closed
precheck in full: a missing, unparseable, empty, or `schema_version`-less config, or a config
that fails validation against the schema version matching its own `schema_version` (the same
`resolve_contract_schema_path` plus `Draft7Validator` path `verify_workspace` uses; `jsonschema`
is already a runtime dependency), yields a document with `errors` and exit `2`. There is no
last-known-good fallback. Add the command to `USAGE`.

**Tests (scenarios):** dogfood-shaped fixture config resolves Stage and Ship and escalation
with the expected tuples; same-route escalation gives exit `1` with `ESCALATION_DEGRADED`;
missing config gives exit `2`; a schema-invalid config gives exit `2`; the document key set
is exactly the pinned set.

**Acceptance criteria:** exit codes and key set pinned by test; running it against this
workspace prints Stage `claude-sonnet-5.5`/`anthropic`/`xhigh`/`default` and Ship
`claude-haiku-5.5`/`anthropic`/`xhigh`/`long_context` (recorded in closure, not asserted by
a test that would encode operator data).

**Harness surface:** `harness-surface:harness-architect`. **Size/complexity:** `M` /
`medium`. **Depends on:** A2.

### A5: Orchestrator declares routes from the CLI, with a declared fallback

**Files (triple + test):** `templates/agents/_orchestrator.agent.md.tmpl`,
`.github/agents/_orchestrator.agent.md`, `.autoharness/harness-manifest.yaml` (checksum
refresh), `tests/test_orchestrator_routing_cli_directive_contract.py` (new).

**Change:** At the Stage and Ship invocation sites, first resolve via
`autoharness routing resolve --workspace . --site stage|ship --json` (log `TOOL_OK:
routing-resolver-cli`); on CLI failure log `TOOL_DEGRADED: routing-resolver-cli` and follow
the existing prose resolution; a CLI exit `2` halts that invocation (fail closed). Replace
the schema-validation wording that names only `schemas/harness-config.schema.json` with "the
schema version matching the document's own `schema_version`" (versioned mirror), because the
root schema tracks only the current version. Preserve every token required by
`_add_orchestrator_invocation_routing_directive_check` (`context_tier`,
`ROUTING_DEGRADED: context_tier` at both sites). Do **not** edit any route literal in the
prose (those belong to `1F13DF5E`, which awaits an operator decision), and do not change
Step 0 (shared with `209-S`).

**Tests (scenarios):** both sites name the CLI and the `TOOL_DEGRADED` fallback; required
tokens are still present at both sites; the versioned-mirror clause is present; template and
mirror both carry the markers; manifest checksum matches the committed mirror.

**Acceptance criteria:** the existing orchestrator directive checks and the paired-edit
marker tests pass; the manifest checksum equals the committed mirror.

**Harness surface:** `harness-surface:none` (no `src/` file). **Size/complexity:** `M` /
`low`. **Depends on:** A4.

## Dependency Graph

```text
A1 -> A2 -> A3
A2 -> A4 -> A5
```

No cycles. A3 and A4 are independent after A2 and touch different production files; they are
ordered A3 then A4 only for review simplicity.

## Decisions and Rationale

* **Characterize before extracting (A1 first).** The refactor target is a 5.9k-line file
  with many pinned tests. Vectors generated from the current helpers make "behavior
  preserved" checkable by something other than the existing tests alone, and they double as
  the Go-parity contract.
* **Pure function over parsed data.** Keeps the resolver testable without a workspace and
  portable.
* **CLI is read-only and fail-closed.** Mirrors `harness resolve`; no stale fallback
  (E8B5B3C5).
* **Prose stays as the declared fallback.** Runtimes without the CLI do not regress; the
  degradation is visible (P-012).
* **No JSON Schema for the CLI document yet.** Pinned keys are enough for one consumer;
  publishing now would freeze a contract before R1-B and R2 shape it.

## Risks and Caveats

| Risk | Mitigation |
|---|---|
| The refactor changes a verify result subtly | A1 vectors run against the old helpers first; A3 forbids editing any pre-existing test; net-deletion acceptance criterion. |
| `verify_workspace` result shapes carry extra keys (`per_role`, `resolved_escalation_*`) that vectors miss | A1 includes a case per shape consumer; A3 asserts the shape through the existing suite. |
| Merge conflict with the queued `209-S` to `213-S` chain on the Orchestrator pair and the manifest | Shipment sequenced after `213-S`; A5 avoids Step 0 and route literals; rebase at claim time. |
| New Python surface while the operator steers toward Go | Pure module plus JSON vectors; thin CLI; cross-read with `039-DL`; not held by `207-S`. |
| The Orchestrator CLI call is unavailable in some runtimes | Declared `TOOL_DEGRADED` fallback to the existing prose. |
| A3 touches many lines of a huge file | Size `M`; one concern; whole-suite gate. |

## Plan Hardening Signals (REQUIRED)

* Public API, schema, or contract change: **present**. A new CLI command and a pinned JSON
  document shape; the verification refactor touches a fail-closed gate (P-013.5/P-013.6).
* Security, auth, permission, or compliance-sensitive behavior: **absent**. The resolver
  grants no authority; it reads config and returns a route. (It does not enable any
  cross-provider route; no routing value changes.)
* Migration, backfill, destructive data/config action, or irreversible step: **absent**. No
  config or schema change; the diff is reversible by revert.
* External integration, operator checkpoint, or external dependency: **absent**. The
  Orchestrator's use of the CLI depends on the runtime exposing a terminal; fallback is
  declared.
* High runtime, rollout, or rollback risk: **present**. A behavior-preserving refactor of
  verification logic whose failure would turn fail-closed gates red or, worse, green.

Requires plan hardening: yes

## Runtime Verification and Closure

| Unit | Runtime surface | Verification before absorption |
|---|---|---|
| A3 | `autoharness verify-workspace` | Run it on this workspace before and after; the JSON report is identical except no new keys (record both hashes in closure). |
| A4 | `autoharness routing resolve` | Run for `stage`, `ship`, `orchestrator`, and `--kind escalation` against this workspace; run once against a copy with the config removed and confirm exit `2`. |
| A5 | Orchestrator invocation directive | Confirm the template/mirror/manifest triple; confirm the CLI path and the declared fallback are both stated. |

Closure artifact: the shipment closure record under `docs/closure/` with the before/after
verify-workspace comparison. Rollback trigger: any difference in the verify-workspace report
or any pre-existing test needing an edit. Rollback: revert the shipment PR (additive module
and CLI; no data migration). Owner: Ship, validated by the operator at merge.

## Plan Hardening

**Required:** yes. Two signals are present: a new CLI contract and a behavior-preserving
refactor of a fail-closed verification gate. Hardening recorded 2026-10-12 (UTC).

**Learnings and instructions consulted:**

* `docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md` (P-013.5 gating
  pattern: existence-gated checks, per-check red/green pairs, directive tokens).
* `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md` (not
  triggered here, but confirms no schema file may be touched in this release).
* `docs/design-docs/2026-08-20-template-dogfood-paired-edit-maintenance-contract.md`
  (`_orchestrator` is a paired-edit pair; manifest checksum triple).
* `.github/policies/workflow-policies.md` P-013.5, P-013.6, P-012, P-004 (marker convention,
  `harness-surface` rule).
* `.github/instructions/escalation-protocol.instructions.md` (resolution order and
  same-route guard definition the vectors must match).
* `.github/instructions/role-enforcement.instructions.md` (skill inheritance; unchanged).

**Protected invariants:**

* I1 verify-workspace output for this workspace is identical before and after A3 (no new
  key, no changed value), and the per-case check dicts recorded by the A1 vectors are
  identical after the refactor.
* I2 no pre-existing test is edited by any unit in this plan.
* I3 an invalid, missing, empty, or `schema_version`-less config makes the CLI exit `2`; no
  last-known-good fallback (E8B5B3C5/H6).
* I4 the P-013.5 directive tokens (`context_tier`, `ROUTING_DEGRADED: context_tier`) remain
  at both Orchestrator invocation sites.
* I5 the CLI is read-only: it writes nothing to disk and nothing to stderr after a
  successful parse.
* I6 `context_tier` is never part of the same-route comparison.

**Risky actions:**

| ProposedAction | ActionRisk | Approval | Rollback |
|---|---|---|---|
| A3: replace helper bodies in `verify_workspace.py` | high (a fail-closed gate could turn permissive) | PR review plus the I1 golden comparison | revert the shipment PR |
| A4: add the `routing` CLI command | low | PR review | revert |
| A5: edit `_orchestrator` template, mirror, and manifest checksum | medium (paired-edit pair; checksum mismatch fails verify) | PR review | revert; re-run checksum refresh |

**Added verification (tightens the plan):**

* A1 vectors additionally record, for every case, the full `role_route_resolution` and
  `escalation_route_resolution` targeted-check dicts (including `per_role`, `ambiguous`, and
  `same_route_roles`) as produced by the current code, and A3 asserts equality after the
  refactor. This catches a changed result shape that per-helper vectors miss without adding
  files to A1. The whole-report before/after `verify-workspace` comparison for this
  workspace is a closure-time runtime verification (see the table above), not a committed
  fixture.
* A3 acceptance is stated as a negative as well: the diff must add no new `targeted_checks`
  key and must modify no file under `tests/` other than the new delegation test.
* A4 pins UTF-8 and LF output (as `harness resolve` does) and asserts nothing is written to
  stderr on a successful parse, on Windows and Linux.
* A4 maps exit codes explicitly: `0` resolved; `1` resolved with a declared degradation (the
  caller must use the route **and** surface the degradation); `2` unresolved or invalid
  (the caller halts that invocation).
* A5 states the `autoharness` executable-not-found case as `TOOL_DEGRADED`
  (`routing-resolver-cli`), not a silent skip, and states that exit `1` is not a failure.

**Closure and rollback detail:** monitoring signal is the shipment closure comparison of
`verify-workspace` before and after; rollback trigger is any I1 difference or any
pre-existing test edit; rollback is a revert of the single shipment PR; owner is Ship;
validation window is the PR review plus the first Orchestrator Stage/Ship invocation after
merge.

**Review-gate capability risks:** the Stage session that authored this plan has no reviewer
subagent dispatch surface, so plan review runs as `single-agent-declared-degradation`
(every selected persona applied inline, P-012 declared). The anchor reviewer route
(`model_routing.anchor_review`) is not dispatchable from this session, so the cross-model
personas run same-model with `TOOL_DEGRADED: model-specific-review-routing`. The review
section must carry literal `dispatch_mode:` and `decision:` markers; harvest halts without
them.

**Unresolved operator decisions that block safe execution:** none. Items needing operator
authority for later releases are recorded in `040-DL` (OQ1 to OQ9) with defaults; none
blocks R1-A.

## Plan Review

Review record: `docs/reviews/2026-10-11-model-routing-resolver-single-source-plan-review.md`
(two cycles; recorded 2026-10-12 UTC).

dispatch_mode: single-agent-declared-degradation

decision: PASS

* **Gate decision:** no P0 or P1 findings. Cycle 1 produced two P2 findings (A4 omitted
  schema validation from the fail-closed precheck; the Outcome over-claimed "single source
  of truth" while Stage/Ship escalation prose is unchanged) and three P3 findings. Both P2
  findings were fixed in this plan and re-verified in cycle 2.
* **Plan hardening:** required (`Requires plan hardening: yes`) and satisfied
  (`## Plan Hardening`).
* **Persona coverage:** Constitution, Python, Scope Boundary, Learnings (always-on, inline
  pass); Architecture Strategist and Agent-Native Parity (cross-model, same-model fallback,
  `TOOL_DEGRADED: model-specific-review-routing`); Security Lens judged not triggered. Every
  selected persona was covered under
  `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
* **Findings:** A-F1 and A-F2 (P2, fixed); A-F3 (P3, fixed); A-F4, A-F5, A-F6 (P3,
  acknowledged).
* **Runtime verification and closure:** specified for A3, A4, and A5; no gaps.

