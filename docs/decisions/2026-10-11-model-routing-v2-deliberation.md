---
title: "Model routing v2: deterministic route resolver, tier-delta catalog, and subagent site bindings"
description: "Deliberation for stash BF66F08B (040-DL). Evaluates the docs/design-docs/model-routing-v2.md baseline against the shipped P-013/P-013.5/P-013.6 routing contract and decides an improved, staged mechanism: one deterministic resolver, a YAML-anchor-free tier-delta route catalog, manifest-registered subagent site bindings, and drift/unknown-key verification (schema 1.2.0), followed by an escalation chain and a review-diversity invariant. Phase-level routing is deferred behind an explicit promotion rule."
topic: "How should autoharness model routing evolve beyond role plus tier routes, using model-routing-v2.md as the baseline proposal?"
depth: "deep"
decision_status: "decided"
promoted_to: "plan"
doc_type: decision
source_stash: BF66F08B
deliberation_id: 040-DL
baseline_document: docs/design-docs/model-routing-v2.md
linked_artifacts:
  - "docs/design-docs/model-routing-v2.md"
  - "docs/plans/2026-10-11-model-routing-resolver-single-source-plan.md"
  - "docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md"
  - "docs/reviews/2026-10-11-model-routing-resolver-single-source-plan-review.md"
  - "docs/reviews/2026-10-11-model-routing-catalog-bindings-plan-review.md"
tags:
  - "model-routing"
  - "p-013.5"
  - "p-013.6"
  - "schema-1.2.0"
  - "route-resolver"
  - "stage-deliberation"
---

# Model routing v2: deterministic route resolver, tier-delta catalog, and subagent site bindings

Deliberation artifact for stash `BF66F08B` (backlogit deliberation `040-DL`).
Recorded in UTC on 2026-10-12 (local intake date 2026-10-11).
Operator request, verbatim: "Design an improved model routing mechanism using this
document as the baseline proposal @docs\design-docs\model-routing-v2.md".

## Problem Frame

The baseline proposal (`docs/design-docs/model-routing-v2.md`, 50 lines) describes a
richer `model_routing` block:

* base `tier1`/`tier2`/`tier3` expressed as YAML anchors, with `tier3` pointing at a GPT
  architect;
* per-role sub-routes: Orchestrator `subagents` (`dispatcher`, `checkpoint_manager`,
  `conflict_evaluator`), Stage `phases` (`discover`, `architect`, `review`, `repair`,
  `materialize`), Ship `phases` (`context_slice`, `implement`, `verify_triage`);
* a Ship `escalation` with `max_cycles` and a cross-family `fallback`;
* a cross-family `anchor_review` (Claude reviews the GPT architect);
* capability-pack `subagents` (`backlogit_ops`, `engram_curator`, `graphtor_indexer`,
  `security_auditor`).

The shipped routing contract this must be reconciled with is: P-013 tiers, P-013.5
invocation-time enforcement (`ROUTING_DEGRADED`, per-sub-field tier fallback, skills as leaf
executors that inherit the invoking agent's route), P-013.6 escalation (nested per-role
`escalation`, legacy flat fallback, same-route `ESCALATION_DEGRADED`, analysis-only handoff
and the authority-preservation invariant), `context_tier` as a separate route field (200-S),
the fresh-config-read rule (E8B5B3C5), and the frontmatter-conformity contract (037-DL).

**Success criteria for the design.**

* Every proposed construct maps to an enforcement point that exists or is planned, so no
  config key can be accepted by the schema and then silently ignored.
* No regression to P-001, P-009, P-013.1 to P-013.6, P-014, P-018, P-021 and no new
  authority for any agent (escalation stays reasoning-only).
* A single definition of route resolution, instead of the current prose-in-N-places.
* Backward compatible for installed workspaces; nothing is a hard cutover.
* Every resulting task fits the 2-hour rule and one width family.

**Scope boundaries (out of scope here).** Changing any routing value in
`.autoharness/config.yaml` (operator data); the Stage/Orchestrator route decisions already
captured as `3C19FA0F` and `1F13DF5E`; removing frontmatter route fields (`79021C29`); the
work-attribute (size by complexity) router and its proposed P-013.7 (`9B582824`); Go
runtime distribution (`F194A1D8` / `039-DL`).

## Research Findings

All findings are from direct reads of the repository on 2026-10-12 (UTC) unless noted.

### Finding 1: the baseline does not load, and only partly validates when repaired

* As written, `yaml.safe_load` raises `ComposerError: found undefined alias
  'claude-tier1-fast'`. The 50-line document defines no anchors, so the catalog (names,
  `model_family`, `model_provider`, `reasoning_effort`, `context_tier`) is unspecified.
* Defining the six anchors in a hypothetical sibling block and validating the resulting
  `model_routing` against `schemas/harness-config.schema.json` yields **7 schema errors**:
  `orchestrator.subagents`, `stage.phases`, `ship.phases`,
  `ship.escalation.{max_cycles,fallback}` (all rejected by `additionalProperties: false`),
  and `tier1`/`tier2`/`tier3` (tier objects must carry `model` or be a plain string).
* Conversely, a top-level `model_routing.subagents` block **passes** validation, because
  `model_routing` itself does not set `additionalProperties: false`. Nothing consumes it, so
  it would be silently inert. That is an existing hazard any new routing key inherits.
* The baseline and the current dogfood values disagree: baseline `tier2` is Sonnet 5.5
  `medium` while config `tier2` is `high`; baseline Ship starts on Sonnet and escalates to
  Sonnet `high`/`long_context`, while config Ship starts on Haiku `xhigh`/`long_context`
  and escalates to Sonnet `medium`.

### Finding 2: most baseline names are not routing sites in this harness

* None of `dispatcher`, `checkpoint_manager`, `conflict_evaluator`, `backlogit_ops`,
  `engram_curator`, `graphtor_indexer` exist as agent files, templates, or skills
  (`rg` across `templates/`, `.github/`, `src/`, `schemas/`). The Orchestrator performs
  dispatch, checkpointing, and circuit-breaking inline; backlogit, engram, and graphtor are
  MCP tool servers, not model invocations.
* `security_auditor` maps onto two existing agents: `security-reviewer` and
  `security-lens-reviewer`.
* Stage and Ship phases are steps inside one agent session. Their work is done by skills
  (`deliberate`, `spike`, `impl-plan`, `plan-harden`, `plan-review`, `harvest`) that are
  leaf executors and inherit the session route (`role-enforcement.instructions.md`
  Skill-Delegation Model Inheritance; P-013.5 Skill inheritance). A model cannot change
  mid-session, so a phase is a routing site only if it is executed as an isolated agent
  invocation. None are today.
* The exception is the review family: `review` and `plan-review` have a bounded one-hop
  exception and already spawn persona subagents, with `model_routing.anchor_review`
  assigned to one cross-model persona. The baseline's Stage `review` phase ("Claude checks
  Sol") is therefore already expressible with today's config alone.

### Finding 3: subagent routing exists only as stale install-time frontmatter

A read-only probe of `.github/agents/**` against `.autoharness/config.yaml` shows:

| Surface | Declared route | Matches current config? |
|---|---|---|
| `_stage` | `claude-sonnet-5.5` / `anthropic` / `xhigh` / `default` | yes |
| `_ship` | `claude-haiku-5.5` / `anthropic` / `xhigh` / `long_context` | yes |
| `_orchestrator` | `claude-opus-5.5` / `anthropic` / `high` | **no** (config: `claude-sonnet-5.5`; tracked as `1F13DF5E`) |
| 11 subagents (reviewers, `learnings-researcher`) | `gpt-5.6-luna`, empty provider and effort | **no**, matches neither current `tier1` nor `tier2` |
| 2 subagents (`security-reviewer`, `security-lens-reviewer`) | `claude-sonnet-5`, empty provider and effort | **no** |

`verify-workspace` checks `model_family`/`model_provider` only for the three pipeline
agents (P-013.5 clause a), so this subagent drift is invisible to verification. The
templates render subagent frontmatter from `TIER_1_*`/`TIER_2_*` variables, so the only
per-subagent control today is the tier chosen when the template was written.

### Finding 4: resolution logic is duplicated and already drifting

Route precedence is implemented or described in: the `_derive_*`/`_effective_*` helpers in
`src/autoharness/verify_workspace.py` (install-time derivation and verify checks); agent
prose in the Orchestrator, Stage, and Ship templates and installed mirrors; and
`escalation-protocol.instructions.md`. At runtime the Orchestrator resolves routes by
reading `.autoharness/config.yaml` and following prose, so the precedence is executed by an
LLM. Observed drift: `escalation-protocol.instructions.md` still states the workspace's
resolved escalation as a flat `gpt-6-sol`/`openai` route and Stage as `claude-opus-5.5`,
while config declares no flat escalation, Stage is `claude-sonnet-5.5`, and Ship carries a
nested escalation; the Orchestrator mirror still names `claude-opus-5.5` (`1F13DF5E`); and
the Stage escalation resolves to `tier3`, identical to Stage's own route, so every Stage
auto-escalation is a same-route no-op (`3C19FA0F`). Eight commits have touched routing
values in `.autoharness/config.yaml`, several of them operator hand-edits.

### Finding 5: the baseline's own semantics collide with shipped contracts

* `tier3: *gpt-tier3-architect` makes every `tier3` fallback GPT: the Stage default, the
  escalation default, and the P-013.3 Tier2-to-Tier3 target. With `stage` also set to the
  same alias and no `stage.escalation`, Stage escalation resolves to its own route, the
  `3C19FA0F` same-route no-op again.
* `max_cycles: 2` means the escalated route re-attempts the work. P-013.6 defines
  escalation as an analysis-only handoff ("not a fourth attempt"), guarded by the
  authority-preservation invariant. `max_cycles` is an authority change, not a routing
  parameter. Retry budgets already live in Stop Conditions and the circuit breaker.
* `anchor_review` already exists with `required: [model_provider, model_family]`,
  `additionalProperties: false`, and no `context_tier`. The current dogfood value is
  `openai`/`gpt-6.1-sol`, which is cross-family relative to the Claude Stage. The
  baseline "flip to Claude" only makes sense because the baseline also moves Stage to GPT.
  The real requirement is relative: the reviewer family must differ from the author
  family. A hard-coded flip does not encode that.
* YAML anchors and the `<<` merge key are resolved at parse time. Routes are also read by
  agents from raw text, rendered by `{{VAR}}` templates (not a YAML dump), edited by hand,
  and will be parsed by a future Go runtime (`F194A1D8`). Aliases are invisible to
  `rg`/agent reading, are not preserved by install/tune rendering, and merge keys are
  YAML 1.1 only.

### Finding 6: schema discipline is a recurring failure class

Published schema mirrors must never be edited in place (`docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`,
`docs/compound/2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md`).
The `context_tier` change (D-C5) already mutated `schemas/harness-config/1.1.0.schema.json`
in place under a documented exception. Any new routing keys must publish a new `1.2.0`
mirror and add a pinned-bytes test for `1.1.0`.

### Finding 7: what the baseline gets right

* A reusable, named route catalog reduces the nine near-duplicate four-field route blocks.
* The cross-family review idea matches the repository's own multi-model review direction.
* A fallback target when the primary escalation route is unavailable is a real gap: with
  one route per role there is no recovery from `ESCALATION_DEGRADED` other than operator
  halt.
* A `security_auditor` route points to a real need for per-subagent control.

## Overlap and Bounding Against Existing Owners

| Entry | Owns | This work's relationship |
|---|---|---|
| `036-DL` (`context_tier`) | `context_tier` on routes and frontmatter; shipped in 200-S | Reuse as-is. Catalog routes and bindings carry `context_tier`; the same-route guard still excludes it. No re-decision. |
| `037-DL` (frontmatter conformity) | Contract for agent/skill frontmatter; tune proposes, never auto-applies | Reuse the contract and the managed-versus-workspace-authored split for the new subagent drift check. |
| `79021C29` (remove frontmatter routing fields) | Whether frontmatter keeps route values | Not decided here. R1 treats frontmatter as an install-time default and adds a drift check, which stays correct whether or not the fields are later removed. |
| `1E6C8576` (per-skill/subagent/activity routing, multi-level escalation) | The same ask in stash form | Its design content is consumed by this deliberation. The entry is not edited here; disposition is left to the operator (see Open Questions). |
| `9B582824` (cost-per-unit-of-work epic) | `task-executor` agent, work-attribute router, proposed P-013.7 | Phase-level routing depends on its component A (isolated executor). Bounded as R4. The resolver reserves a precedence slot for a derived route so P-013.7 can plug in later; this work claims no P-013.7. |
| `3C19FA0F` (Stage escalation same-route) | Operator decision on the Stage escalation route | Not decided here. R2's chain gives that decision a mechanism; the value stays with the operator. |
| `1F13DF5E` (Orchestrator/Stage mirror alignment) | Mechanical mirror alignment, pending operator confirmation of the Orchestrator route | Untouched. R1's drift check will detect this class in future. |
| `F194A1D8` / `039-DL`, hold gate `207-S` | Python-to-Go runtime and distribution re-plan | The resolver is authored as a pure function with language-neutral JSON conformance vectors so a Go port can reuse them. R1 is not held by `207-S`. |
| P-013 / P-013.5 / P-013.6 | Routing contract | Amended, not replaced (see D8 to D10). |

## Options Evaluated

### Option A: adopt the baseline as written

Merge the block into `.autoharness/config.yaml` and the schema.

* Pro: no design work; operator intent is explicit.
* Con: does not load; fails the schema in 7 places; binds to non-existent sites;
  `tier3` as GPT breaks every tier-3 fallback; `max_cycles` changes escalation authority;
  anchors are lost by install/tune and unreadable to agents.

### Option B: baseline semantics with a schema and loader rewrite

Keep phases and subagents as first-class config keys, add loader support, define the anchor
catalog.

* Pro: closest to the baseline's intent.
* Con: phases are not invocation boundaries, so the keys would validate and then do
  nothing, or force a large restructuring of Stage and Ship into isolated phase agents
  (that is `9B582824` component A, not a routing change). Each phase agent adds context
  re-transmission, which `9B582824` identifies as the dominant cost, so the cost goal is
  likely defeated. A cheap-model `materialize` phase also touches the harvest integrity
  step (P-003, size and complexity judgment).

### Option C: data-only change on today's mechanism

Re-point `stage`, `stage.escalation`, `ship.escalation`, and `anchor_review` at the desired
providers. No code.

* Pro: zero risk; achieves cross-family Stage-versus-reviewer today.
* Con: leaves every observed gap open: stale subagent routes, duplicated resolution,
  silently inert unknown keys, no per-subagent binding, no fallback when an escalation
  route is unavailable.

### Option D (chosen): resolver, catalog, bindings, drift verification, then staged extensions

* One deterministic resolver is the single definition of precedence, consumed by verify,
  install/tune derivation, a read-only CLI, and (through the CLI) the Orchestrator.
* A named catalog of **tier deltas** replaces anchors and phase aliases.
* **Bindings** assign a route to registered subagent sites.
* Verification and tune close the drift and silent-inert gaps.
* Escalation chain and review-diversity invariant follow as separate releases; phases are
  deferred behind a promotion rule.
* Pro: fixes observed defects first, is additive, preserves every shipped contract,
  decomposes into 2-hour tasks. Con: it delivers less than the full baseline in the first
  release, and a second cross-provider decision remains the operator's.

## Trade-off Comparison

| Criterion | A: as written | B: rewrite | C: data only | D: staged mechanism |
|---|---|---|---|---|
| Loads and validates | No | After rewrite | Yes | Yes |
| Every key has an enforcement point | No | No (phases) | Yes | Yes, by registry |
| Fixes subagent/frontmatter drift | No | Partly | No | Yes |
| Single resolution definition | No | No | No | Yes |
| Preserves skill-inherits-route | No | Needs isolation | Yes | Yes |
| Preserves P-013.6 analysis-only | No | No | Yes | Yes |
| Backward compatible | No | Partly | Yes | Yes (additive 1.2.0) |
| Cost risk | High | High | None | Low |
| Provider/availability exposure | Large | Large | Operator data | Operator data, explicit degradation |
| 2-hour decomposable | No | No | n/a | Yes |

## Decision

Adopt **Option D**, as the decisions below. Each carries its rationale and rejected
alternatives.

### D1: extend `model_routing` additively; publish schema 1.2.0

Keep the single `model_routing` block as the source. Add optional keys in a **new**
`schemas/harness-config/1.2.0.schema.json` mirror, update the root schema,
`SCHEMA_CONTRACTS["config"]`, and `CONTRACT_MIGRATIONS`, and pin `1.1.0` bytes with a
`test_legacy_1_1_0_mirror_preserved_unchanged`-style test.

* Rejected: a parallel `model_routing_v2` block (two sources of truth, a new both-present
  ambiguity class); renaming or removing existing keys (hard cutover, the rejected
  Option C of the F02FD596 decision); mutating `1.1.0` in place (third-occurrence bug
  class).

### D2: no YAML anchors, aliases, or merge keys; a tier-delta route catalog

`model_routing.routes` is a map of named routes. Each entry is a **delta over a tier**:

```yaml
model_routing:
  routes:
    ingest:    { tier: tier1, context_tier: long_context }
    repair:    { tier: tier2, reasoning_effort: high, context_tier: long_context }
    reviewer:  { tier: tier3 }
    architect: { tier: tier3, model_provider: openai, model_family: gpt-6.1-sol, reasoning_effort: high }
```

* `tier` is required (`tier1`, `tier2`, `tier3`). Unset fields inherit per field from that
  tier. The tier is retained as the route's capability class for P-013.2 ceiling checks and
  telemetry. A route is a targeted override, never a parallel tier taxonomy (the P-013.5
  invariant).
* Names match `^[a-z][a-z0-9_-]{0,47}$` and must not equal `tier1`/`tier2`/`tier3`.
* `verify-workspace` fails when anything under `model_routing` is parsed from a YAML
  anchor, alias, or merge key (`ROUTING_ANCHOR_UNSUPPORTED`) in a `schema_version: 1.2.0`
  config, and reports an advisory for older configs so no existing workspace turns red,
  because agents read the raw text, render/tune does not preserve them, and the Go runtime
  must not depend on them.
* The values above are illustrative; the actual catalog is operator data (OQ4). The
  baseline's six profiles map as: `claude-tier1-fast` is plain `tier1`; `claude-tier1-ingest`
  is `ingest`; `claude-tier2-standard` is plain `tier2`; `claude-tier2-repair` is `repair`;
  `claude-tier3-reviewer` is plain `tier3`; `gpt-tier3-architect` is `architect`. The
  baseline made `tier3` itself the GPT route; the decision keeps `tier3` as the frontier
  default and expresses the architect as a delta, so the tier-3 fallbacks (Stage default,
  escalation default) do not silently flip provider.
* Rejected: YAML anchors with a defining block (above reasons); full four-field copies per
  catalog entry (re-creates duplication and drift); a catalog independent of tiers (a
  second taxonomy, weakens P-013.2).

### D3: sites and bindings; role routes keep their existing spelling

A **site** is an invocation boundary that can carry a model binding. Sites are:
the three pipeline roles (existing `orchestrator`, `stage`, `ship` blocks and their nested
`escalation`), the review routes (existing `anchor_review`, `alt_review`, `alt_doc_review`),
and **installed non-pipeline agents**, addressed as `agent:<id>` where `<id>` is the agent
file name without `.agent.md`.

```yaml
model_routing:
  bindings:
    "agent:security-reviewer":     { route: reviewer }
    "agent:learnings-researcher":  { route: ingest }
    "agent:correctness-reviewer":  { route: tier1, reasoning_effort: high }
```

* A binding is `{ route: <catalog-name | tier1 | tier2 | tier3>, <optional per-field
  overrides> }`, `additionalProperties: false`. One shape only.
* The **site registry** is derived, not hand-typed: the shipped subagent templates give the
  default tier of each known agent (validated by a sync test against the templates), and
  verify adds installed workspace-authored agents. Pipeline agents cannot be bound through
  `bindings`; they use their role blocks (no dual spelling, so no new ambiguity).
* An unknown site id fails verification (`ROUTING_UNKNOWN_SITE`). That closes the
  silently-inert hazard for every name in the baseline that is not a real agent.
* Rejected: free-form binding keys (silent no-ops); binding by skill name (skills have no
  model attachment point, P-013.5); folding role blocks into `bindings` (churns every
  installed config and test for no gain).

### D4: resolution precedence (per field, total order)

For a site, each of `model_family`, `model_provider`, `reasoning_effort`, `context_tier`
resolves independently, first non-empty wins:

1. site binding per-field override;
2. the binding's `route` (catalog delta, then its `tier`; or the bare tier);
3. for role sites, the existing role block, then the role's default tier (Stage `tier3`,
   Ship `tier2`, Orchestrator `tier2`); for subagent sites with no binding, the agent's
   template default tier;
4. terminal default `default` for `context_tier` only.

`model_family` still unresolved after step 3 is a resolution **error**
(`ROUTING_UNRESOLVED: model_family`), never a silent default (P-013.5). An empty
`model_provider` or `reasoning_effort` is **valid** and means "use the model/runtime default":
the config template documents it ("leave empty for default"), `verify-workspace` already
accepts it (`verify_workspace.py`, "model_provider is intentionally NOT required to be
non-empty", pinned by `test_verify_workspace_allows_empty_model_provider_field`), and the
R1-A resolver reproduces that rule rather than tightening it, so legacy and default installs
are not regressed. Only a non-string value or an unresolved `{{...}}` placeholder in a
rendered `model_provider` remains invalid (existing verify behavior, unchanged). Escalation
routes keep the P-013.6 order (nested role
escalation, legacy flat, `tier3`) and per-field fallback. Installed frontmatter is **not**
part of the chain: it is a rendered default (E8B5B3C5/H8) and is checked against the
resolver's output. The resolver output carries an ordered `resolution_chain` so a future
derived-route layer (work-attribute routing, `9B582824`) can be inserted between steps 1
and 2 without changing any consumer.

### D5: the resolver is code, with vectors, and is the single source of truth

* New pure module `src/autoharness/model_routing.py`: `resolve_site(config, site, kind)`
  returns the four route fields, the tier class, the source chain, and any declared
  degradation. It takes parsed config data and performs no I/O.
* Language-neutral conformance vectors (JSON: config in, expected resolution out) under
  `tests/fixtures/model_routing/`, first reproducing today's behavior (tier fallback,
  nested/flat/tier3 escalation, `context_tier`, both-present ambiguity, same-route guard).
  A future Go port runs the same vectors (`F194A1D8`).
* `verify_workspace.py` and the install/tune variable derivation delegate to the module;
  the existing tests (`test_route_variable_precedence`, `test_context_tier_resolution`,
  `test_escalation_*`) pin the refactor as behavior-preserving.
* New read-only CLI `autoharness routing resolve --workspace <p> --site <id> [--kind
  route|escalation] --json`. The Orchestrator declares its invocation directive from this
  output when the CLI is available (`TOOL_OK`), and otherwise follows the existing prose
  with `TOOL_DEGRADED` (P-012). The prose is retained as the declared fallback, so no
  runtime without the CLI regresses.
* Rejected: leaving resolution as prose (the observed drift source); embedding the new
  logic only in `verify_workspace.py` (5.9k lines, not callable at runtime); a new schema
  field that stores pre-resolved routes (a second copy to drift).

### D6: phases, Orchestrator subagents, and capability-pack names are not sites

* Phases: not bindable in config. **Promotion rule:** a Stage or Ship phase may become a
  registered site only when (a) it executes as an isolated agent invocation with its own
  manifest-registered agent definition and a bounded context and return contract (the
  `9B582824` component A pattern), (b) that agent satisfies the depth and tier ceilings
  (P-013.2, P-016), and (c) measured evidence (the `9B582824` component B telemetry)
  shows the phase benefits from a different route. Until then the baseline's
  `stage.phases` and `ship.phases` are rejected as config keys (the schema already rejects
  them; `bindings` rejects unregistered sites).
* `dispatcher`, `checkpoint_manager`, `conflict_evaluator`, `backlogit_ops`,
  `engram_curator`, `graphtor_indexer`: not agents, so not sites. If one is later built as
  an agent it registers through the normal manifest and becomes bindable with no schema
  change.
* `security_auditor`: expressible today as bindings on `agent:security-reviewer` and
  `agent:security-lens-reviewer`.
* Rejected: accepting the names now "for forward compatibility" (silent inert keys, the
  exact defect class this design removes).

### D7: escalation keeps analysis-only semantics; add an ordered `chain` (R2)

* P-013.6's single-hop, analysis-only handoff and the authority-preservation invariant are
  unchanged. `max_cycles` is rejected as a routing key: it would let an escalated route
  re-execute, which is an authority change (OQ3).
* Add `escalation.chain: [ {route|fields}, ... ]` under each role's nested `escalation`
  as an **ordered dispatchability fallback**. The resolver selects the first level that is
  dispatchable and not a same-route no-op against the acting role's own route and against
  levels already skipped. When no level qualifies, `ESCALATION_DEGRADED` and the existing
  operator halt apply. This gives the baseline's "cross-family circuit breaker if
  Anthropic stalls" and the operator's multi-level wish (`1E6C8576` addendum) a bounded,
  verifiable form, and gives `3C19FA0F` a mechanism whose value stays operator data.
* `chain` and direct escalation fields in the same block, or `chain` alongside a non-empty
  legacy flat `escalation`, are AMBIGUOUS and fail closed (the H2 rule, extended).
* Rejected: `max_cycles` and any re-attempt semantics (authority); making the flat
  escalation multi-level (legacy shape, deprecation pending); unbounded chains (cap at 3
  levels).

### D8: cross-family review is a routing and declaration concern, not a merge gate (R3)

* Add a relative invariant: the review route's family should differ from the author's role
  family. The resolver computes it; review skills already declare degradation when a
  model-specific route cannot be dispatched (`TOOL_DEGRADED: model-specific-review-routing`).
  A new optional `model_routing.review_diversity: preferred | required` (default
  `preferred`, which is the current behavior) controls whether a same-family result is
  recorded as `REVIEW_DIVERSITY_DEGRADED` (preferred) or caps the plan-review decision at
  ADVISORY pending operator acknowledgement (required).
* P-014 and P-018 are **not** changed to depend on provider availability. The review's
  `dispatch_mode` and diversity result are recorded as evidence in the existing review
  artifacts and the Local Review Readiness block. A merge gate keyed to a second
  provider's availability would let an outage block merges.
* Rejected: hard-coded `anchor_review` flip (not relative); a P-014/P-018 blocking
  condition (availability coupling); silently same-family review when `required`
  (existing P-012 violation).

### D9: degraded modes (explicit, never silent)

| Condition | Behavior |
|---|---|
| Config missing, unparseable, schema-invalid, or no `schema_version` | HALT to operator (E8B5B3C5/H6); no last-known-good fallback. |
| Catalog name or binding route unresolved; unknown site; anchor/alias present | `verify-workspace` FAIL; runtime resolver exits non-zero; the invoking agent halts that invocation. |
| Runtime cannot honor a per-invocation override | `ROUTING_DEGRADED` naming the site and route; carry forward to inherited skills (existing). |
| Model family or provider unavailable at the runtime | `ROUTING_DEGRADED`; continue on the session model only after declaring it. |
| `context_tier` unsupported | `ROUTING_DEGRADED: context_tier`, non-halting (existing). |
| Escalation route unavailable or same-route | `ESCALATION_DEGRADED`; with `chain`, advance to the next level; exhausted means operator halt (R2). |
| Anchor review undispatchable | Existing `TOOL_DEGRADED: model-specific-review-routing` and same-model rubric pass; `required` diversity caps the decision at ADVISORY (R3). |

### D10: enforcement and drift matrix

| Layer | R1 change |
|---|---|
| Schema 1.2.0 | `routes` (tier required, field overrides, name pattern), `bindings` (site-id pattern, one object shape), `additionalProperties: false` on both; existing keys unchanged. |
| Resolver | One module and vectors (D5). |
| `verify-workspace` | New targeted checks: catalog integrity, binding route resolves, known site, `routes`/`bindings` declared in a pre-1.2.0 config (inert), alias-free `model_routing`, and installed subagent frontmatter versus the resolved route. The drift check fails closed for manifest-managed agents **only in workspaces that declare `bindings`** (the opt-in to config-authoritative subagent routing), is advisory for workspace-authored agents (037-DL split), and is non-blocking `info` otherwise, so a workspace with pre-existing drift (this one) does not turn red. Existing P-013.5/P-013.6 checks delegate to the resolver. |
| `tune-harness` | Detects subagent drift and proposes a refresh of route frontmatter (proposal only, never auto-applied); proposes catalog extraction when it finds repeated identical route blocks. |
| Install | Config template gains empty `routes`/`bindings` blocks; variable table documents them; subagent frontmatter is rendered from resolver output for bound sites. |
| Policy | P-013.5 amended (catalog, sites, bindings, resolver, alias prohibition); P-013.6 amended in R2; amendment-log rows per policy convention. |
| Tests | Red-first vectors and verify fixtures; `1.1.0` mirror pinned; tests prove the baseline-shaped block fails with a named error rather than silently passing. |

### D11: migration and backward compatibility

* Additive 1.2.0: every 1.1.0 config remains valid and resolves identically (proved by the
  vectors). `schema_version` stays `1.1.0` until the operator adopts `routes`/`bindings`,
  at which point tune proposes the bump (mirroring the F02FD596 precedent).
* No hard cutover: flat `escalation` and all legacy blocks keep working; the deprecation
  timeline is a separate operator decision (OQ6).
* Installed workspaces: tune proposes; nothing is auto-applied; workspace-authored agents
  are advisory-only.
* The dogfood `.autoharness/config.yaml` routing values are **not** edited by this work.
  Fixing the 13 stale subagent frontmatters is a tune-refresh chore the operator can run
  once R1 ships (recorded as a follow-up note, not scope).

### D12: release staging

| Release | Scope | Gate |
|---|---|---|
| **R1** (planned and harvested now, as two shipments) | R1-A: D5 resolver, vectors, delegation, CLI, Orchestrator directive. R1-B: D1 to D4, D10, D11 catalog, bindings, schema 1.2.0, verify and tune drift, install/policy/docs | R1-B blocked on R1-A; both after the queued `213-S` |
| **R2** (stash follow-up) | D7 escalation `chain`, per-level guard, P-013.6 amendment | R1 shipped; OQ3 default accepted |
| **R3** (stash follow-up) | D8 review diversity, invocation-time subagent and review directives in Stage, Ship, and review skills | R1 shipped; runtime override evidence |
| **R4** (stash follow-up, gated) | D6 phase-site promotion with `9B582824` A/C, derived-route slot | `9B582824` component A shipped and cost evidence |

## Rejected Alternatives

* **Adopt the baseline as written (A)** and **baseline with schema rewrite (B)**: see
  Options. The decisive reasons are that the keys have no enforcement point and that
  phases cannot change model inside one session.
* **YAML anchors with a defining block**: invisible to agent reading and grep, lost by
  template rendering and tune, YAML 1.1 merge semantics, a parity risk for Go.
* **`tier3` as the GPT route**: flips every tier-3 fallback and recreates the same-route
  no-op for Stage.
* **`max_cycles` / re-attempt escalation**: authority change; belongs to operator policy,
  not config.
* **Cross-family as a P-014/P-018 merge gate**: couples merge to provider availability.
* **Skill-level or phase-level model keys**: skills are leaf executors (P-013.5); phases
  are not invocation boundaries.
* **A second resolver written in prose or in `verify_workspace.py` only**: preserves the
  drift source.
* **Hard-removing the flat `escalation` block in this series**: breaks installed
  workspaces; deferred (OQ6).

## Unresolved Questions

Each item has a recommended default. The default is what this staging proceeds on; none
blocks planning or R1 shipping. The operator's answer (2026-10-12 UTC) and the per-question
status are recorded in the append-only "Operator Confirmation (2026-10-12)" section at the
end of this document; the table below keeps the original questions and defaults.

| ID | Question (needs operator authority) | Recommended default | What it blocks |
|---|---|---|---|
| OQ1 | Provider mix, cost, and cross-provider data egress: should Stage (or any role) route to a GPT architect? Routing Stage to a second provider sends repository and plan content to that provider. | **No**, keep the Claude Stage route. The mechanism makes adoption config-only. | Any dogfood config change; the choice behind `3C19FA0F` |
| OQ2 | Cross-family review: `preferred` or `required` | `preferred` (current behavior); never a merge gate | R3 default value only |
| OQ3 | Escalation: analysis-only, or bounded re-attempt (`max_cycles`) | Analysis-only (P-013.6 unchanged) | R2 shape; re-attempt would need an operator-authored policy amendment |
| OQ4 | Catalog names and values | Propose `ingest`, `repair`, `reviewer`, `architect` as tier deltas over current tiers; ship no catalog data in the dogfood config yet | Dogfood adoption of `routes`/`bindings`, not R1 code |
| OQ5 | Stage escalation target (`3C19FA0F`) and Orchestrator route alignment (`1F13DF5E`) | Left to the operator; not decided here | Those entries; R2 gives the former a mechanism |
| OQ6 | Flat `escalation` deprecation timeline | Not in this series | Nothing here |
| OQ7 | Go parity: author the resolver for a future port? | Yes (pure function, JSON vectors); `039-DL` does not hold R1 | Nothing here |
| OQ8 | Disposition of stash `1E6C8576`, whose design is consumed here | Operator archives it after R2 is staged, since its escalation-ladder addendum is covered by R2 and OQ3 | Stash hygiene only |
| OQ9 | May Ship move the dogfood `.autoharness/config.yaml` `schema_version` marker from `1.1.0` to `1.2.0` (marker only; no routing value) in R1-B unit B5? The config is operator-owned. | Yes (confirmed 2026-10-12; see "Operator Confirmation") | Nothing: confirmed. Ship cites the recorded confirmation at intake; the edit stays marker-only |

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Resolver refactor changes existing verify behavior | Vectors reproduce current behavior first (red/green); existing routing tests pin the delegation; refactor task separated from new-feature tasks. |
| Schema 1.2.0 repeats the in-place mutation bug class | New mirror, `1.1.0` byte-pin test, SCHEMA_CONTRACTS and migration entry, per the two compound learnings. |
| Shared-file conflicts with the queued `209-S` to `213-S` chain (Orchestrator/Stage/Ship templates, `workflow-policies.md.tmpl`, harness manifest) | Sequence after `213-S` with an explicit `blocks` edge; rebase at claim time (precedent in the 2026-10-08 Stage memory). |
| New Python surface while the operator is steering toward Go | Pure function plus language-neutral vectors; CLI is a thin wrapper; flagged for `039-DL` cross-read; no hold. |
| Site registry drifts from templates | Sync test between `SUBAGENT_SITES` and `templates/agents/**` frontmatter tier variables. |
| Operator expects phase routing and sees it deferred | D6 states the reason and the promotion rule; R4 recorded as a gated follow-up. |
| `routes`/`bindings` adoption increases rendered-config complexity | Empty blocks by default; tune proposes extraction only when duplication is detected. |
| Cross-provider routes expose code to a second vendor | OQ1 default is no change; all non-default routes carry explicit degradation; operator decision recorded. |
| Anchor ban rejects a config an operator already hand-wrote | Verify reports the exact location and a catalog rewrite; advisory until the operator bumps to 1.2.0 (the check is gated on the schema version). |

## Traceability

* Source stash: `BF66F08B` (archived by Stage after consumption); deliberation: `040-DL`.
* Harvested: feature `207-F` (shipment `214-S`, 5 tasks `207.001-T` to `207.005-T`) and
  feature `208-F` (shipment `215-S`, 13 tasks `208.001-T` to `208.013-T`; plan units B6 and
  B6a are `208.008-T` and `208.007-T`). `214-S` blocks on `213-S`; `215-S` blocks on `214-S`.
* Follow-up stash entries: `C2EA31FA` (R2 escalation chain), `C5801D7B` (R3 invocation
  directives and review diversity), `507B2139` (R4 phase promotion, gated), `56654C18`
  (tune refresh of the 13 stale subagent frontmatters, after `215-S`).
* Baseline: `docs/design-docs/model-routing-v2.md`.
* Plans (R1): `docs/plans/2026-10-11-model-routing-resolver-single-source-plan.md` (R1-A) and
  `docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md` (R1-B).
* Prior decisions reused: `docs/decisions/2026-08-07-model-routing-hierarchy-dynamic-reload-deliberation.md`,
  `docs/decisions/2026-09-27-close-evidence-frontmatter-context-tier-staging-deliberation.md`,
  `docs/compound/2026-08-01-invocation-time-model-routing-enforcement.md`,
  `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`,
  `docs/compound/2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md`.
* Policies: P-013, P-013.5, P-013.6, P-014, P-018, P-021, P-012, P-016.

## Operator Confirmation (2026-10-12)

Append-only note, recorded in UTC on 2026-10-12. Source: the operator's answer to the open
questions reported by Stage in the "Needs you" list for this staging, relayed through the
Orchestrator: "2. yes". Item 2 of that list was "accept the recommended defaults for OQ1 to
OQ9, including OQ9 (Ship may bump the dogfood `.autoharness/config.yaml` `schema_version`
marker from `1.1.0` to `1.2.0`; marker only, no routing value)".

Status per question. "Resolved by default" means the operator accepted the recommended
default in the table above. A question whose recommended default is itself "left to the
operator" or a pending operator action is not closed by a yes and stays open.

| ID | Status | Recorded outcome |
|---|---|---|
| OQ1 | Resolved by default | No provider-mix change; the Claude Stage route stays. No dogfood config change. |
| OQ2 | Resolved by default | Cross-family review is `preferred`; never a merge gate. |
| OQ3 | Resolved by default | Escalation stays analysis-only; P-013.6 unchanged; no `max_cycles`. The R2 gate "OQ3 default accepted" is satisfied. |
| OQ4 | Resolved by default | Proposed catalog names (`ingest`, `repair`, `reviewer`, `architect`) as tier deltas over current tiers; no catalog data in the dogfood config. Concrete dogfood catalog values remain a later operator data decision and gate nothing in R1. |
| OQ5 | **Open** | The recommended default is "left to the operator; not decided here", so a yes does not decide it. `3C19FA0F` (Stage escalation target) and `1F13DF5E` (Orchestrator route alignment) stay open operator decisions. |
| OQ6 | Resolved by default | The flat `escalation` deprecation timeline is not in this series. |
| OQ7 | Resolved by default | Go parity: the resolver is a pure function with JSON vectors; `039-DL` does not hold R1. |
| OQ8 | **Open (default accepted, action pending)** | The accepted disposition is that the operator archives stash `1E6C8576` after R2 is staged. R2 is not staged yet, so no disposition has been executed; `1E6C8576` is untouched. |
| OQ9 | Resolved: yes | Ship may bump the dogfood `.autoharness/config.yaml` `schema_version` marker from `1.1.0` to `1.2.0` in R1-B unit B5 (`208.006-T`). Marker only: no `model_routing` value may change. |

Ship intake note for `208.006-T` and `215-S`: the confirmation now exists, so OQ9 no longer
blocks either item. Ship cites this section at intake rather than re-asking. The edit stays
marker-only: `git diff --stat` must show exactly one changed line in
`.autoharness/config.yaml` (plus the manifest `config_hash` refresh), and Ship halts and asks
the operator only if that record is missing or the change would exceed the marker.
