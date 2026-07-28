---
title: Multi-model adversarial review routing enhancements
date: 2026-07-27
source_stash: E929B1C9, CB6A0EC6
stage_session: c3e63d78-eaeb-4360-8630-5ec114914a6c
review_mode: single-agent-declared-degradation
---

# Multi-model Adversarial Review Routing Enhancements Plan

## Stage Mode and Tooling

* `TOOL_DEGRADED: backlogit MCP operations — CLI fallback: C:\Tools\backlogit.exe`.
* `INDEX_SYNC_OK (CLI fallback)` before backlog reads.
* `ENGRAM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`, and `INTERCOM_DEGRADED` were declared from the operator-provided environment constraints; code and documentation context came from direct `rg`, `glob`, and `view` reads.
* `TOOL_DEGRADED: reviewer-subagent-dispatch — single-agent persona pass`; plan review was performed inline because no plan-review sub-agent dispatch surface is reachable here.

## Problem Frame

Two selected feature-shaped stash entries describe one coherent release unit:

1. **E929B1C9** asks autoharness to make OpenAI GPT-5.6 Sol a first-class anchor/reviewer model in multi-model adversarial review flows while preserving environment agnosticism and consensus-based finding assembly.
2. **CB6A0EC6** asks autoharness to back-port three evolved plan-review gate enhancements from the backlogit workspace into `templates/skills/plan-review/SKILL.md.tmpl`: dispatch capability/degradation, the relationship to P-012, and a persona rubric adapter that makes dispatch and inline modes use the same plan-review lens. It also asks Ship to check companion impacts on plan-harden, harvest, workflow-policies P-012, review persona agent templates, install-harness variable resolution, and line-ending/name normalization.

The current autoharness surfaces already include multi-model review concepts, but they do not yet model GPT-5.6 Sol as an anchor. Relevant current surfaces discovered during planning:

* `.github/skills/verify-harness/SKILL.md` dispatches Template Fidelity, Overlay Coherence, and Cross-Reference reviewers and asks each to use a different model.
* `templates/agents/adversarial-review.agent.md.tmpl` and `templates/instructions/adversarial-review.instructions.md.tmpl` route reviewers by Tier 1/2/3 and optional `{{ALT_REVIEW_PROVIDER}}` / `{{ALT_REVIEW_FAMILY}}`; no anchor review slot exists.
* `templates/skills/review/SKILL.md.tmpl` and `templates/skills/plan-review/SKILL.md.tmpl` say cross-model diversity is preferred, but model assignment is generic.
* `templates/skills/plan-review/SKILL.md.tmpl` lacks the backlogit copy's capability-aware dispatch/degradation section and persona adapter table.
* `templates/policies/workflow-policies.md.tmpl` P-012 is currently backlog-tool-centric and does not explicitly cover non-registry workflow capabilities such as reviewer sub-agent dispatch.
* `schemas/harness-config.schema.json` models tier and orchestrator routing, but does not currently expose the `alt_review` fields described by `.github/skills/install-harness/SKILL.md`, nor any first-class anchor review route.

The implementation must remain template-first, environment-agnostic, and variable-parameterized. Ship should not bake Copilot CLI, VS Code, backlogit, or a single provider runtime into generated artifacts. GPT-5.6 Sol should be the default anchor where supported, but the generated harness must still declare degradation or fallback when the runtime cannot route to that model.

## Relevant Learnings

* `docs/compound/2026-05-06-p012-tool-availability-gate-and-dispatch.md`: probe before relying, declare degraded mode, and never silently fallback when a configured tool/capability is unavailable.
* `docs/compound/p013-orchestrator-model-routing.md`: model routing is config-resolved through `model_family` / `model_provider` / `reasoning_effort`; do not reintroduce retired standalone `model_tier` frontmatter.
* `docs/compound/093-S-review-loop-convergence.md`: review flows need bounded convergence and explicit residual handling; anchor-review additions must preserve existing circuit breakers and consensus semantics.
* `docs/compound/2026-07-02-headless-eval-runner-deterministic-reviewer.md`: autoharness should keep deterministic verification hermetic and not require live model calls in CI; model-routed adversarial review remains a runtime skill behavior, not a deterministic test dependency.

## Requirements Trace

| Requirement | Planned implementation action |
|---|---|
| E929B1C9 — GPT-5.6 Sol first-class anchor/reviewer model | Add a first-class, config-resolved anchor review model route and wire it into verify-harness/adversarial-review dispatch tables without replacing consensus assembly. |
| E929B1C9 — environment agnostic | Use `{{ANCHOR_REVIEW_PROVIDER}}`, `{{ANCHOR_REVIEW_FAMILY}}`, and optional reasoning-effort placeholders with defaults; document declared degradation if unavailable. |
| E929B1C9 — plan-review/review persona model routing | Update plan-review/review coordination guidance so one eligible cross-model persona can be the anchor reviewer when model override dispatch is available; fallback remains declared inline/same-model review. |
| CB6A0EC6 — back-port dispatch capability/degradation | Add the capability-aware dispatch section to `templates/skills/plan-review/SKILL.md.tmpl` using `{{DOCS_PLANS}}`, `{{DOCS_COMPOUND}}`, `{{PRIMARY_LANGUAGE}}`, and installed template paths. |
| CB6A0EC6 — relate reviewer dispatch to P-012 | Generalize P-012 in `templates/policies/workflow-policies.md.tmpl` to cover required workflow capabilities in addition to backlog-registry tools. |
| CB6A0EC6 — persona rubric adapter | Add an environment-agnostic adapter table mapping persona display names to installed identity files and plan-focused lenses, including `{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md` for the generated technology reviewer. |
| CB6A0EC6 — companion impacts | Split follow-up work across plan-harden/harvest templates, review persona references, policy, and install-harness variable documentation so no task mixes template work with schema/CLI/policy work. |
| CB6A0EC6 — LF/CRLF/naming normalization | Ship must compare the backlogit copy only as evidence, normalize wording and line endings to repository conventions, and avoid backlogit-specific literals such as `docs/exec-plans` or Go-only persona names. |

## Implementation Units

### Unit A — P-012 capability clause for reviewer dispatch

* **Domain**: workflow-policy template only.
* **Files**: `templates/policies/workflow-policies.md.tmpl`; related verification references if existing policy assertions require exact wording.
* **Change**: generalize P-012 from backlog-registry tools only to configured tools **and required workflow capabilities**. Preserve registry/CLI fallback behavior for backlogit, then add a capability-degradation clause for things like reviewer sub-agent dispatch where no registry `cli_command` exists.
* **Acceptance**: policy still rejects silent filesystem fallback for backlog tools; it also requires `TOOL_OK`, `TOOL_DEGRADED`, or `TOOL_UNAVAILABLE` records for required workflow capabilities before a skill depends on them.
* **Verification**: targeted policy/template validation only; no broad refactor.

### Unit B — Anchor review model configuration contract

* **Domain**: schema/config/default contract.
* **Files**: `schemas/harness-config.schema.json`, `schemas/harness-config/1.0.0.schema.json`, `templates/harness-config.yaml.tmpl`, and any existing config-resolution tests or verification assertions that cover `model_routing`.
* **Change**: introduce a first-class anchor review route, e.g. `model_routing.anchor_review` (exact key to be selected by Ship) with provider/family/reasoning fields. Default to OpenAI GPT-5.6 Sol while allowing operator override. Preserve legacy tier routing and avoid retired `model_tier` fields.
* **Acceptance**: schema allows the new object without permitting arbitrary additional properties; generated config stays valid YAML when optional strings are empty; defaults are documented as environment-agnostic model identifiers, not hard runtime calls.
* **Verification**: schema/template tests that already cover harness-config round-trips; add targeted validation if no coverage exists.

### Unit C — Verify-harness and adversarial-review anchor slot

* **Domain**: adversarial verification/review routing documents and templates.
* **Files**: `.github/skills/verify-harness/SKILL.md`, `templates/agents/adversarial-review.agent.md.tmpl`, `templates/instructions/adversarial-review.instructions.md.tmpl`, and docs that enumerate adversarial review models such as `.github/copilot-review-instructions.md` if applicable.
* **Change**: add an explicit anchor reviewer (default GPT-5.6 Sol) to the default reviewer pool alongside the existing tier/diversity reviewers, using the correct mechanism per artifact type. The global, source-controlled `.github/skills/verify-harness/SKILL.md` is NOT rendered from a template, so it MUST load the anchor route from the target workspace config (`model_routing.anchor_review` in `<workspace_path>/.autoharness/config.yaml`) at dispatch time and MUST NOT embed literal `{{ANCHOR_REVIEW_*}}` placeholders, which would never resolve in a source-controlled skill. The rendered templates `templates/agents/adversarial-review.agent.md.tmpl` and `templates/instructions/adversarial-review.instructions.md.tmpl` use `{{ANCHOR_REVIEW_PROVIDER}}` / `{{ANCHOR_REVIEW_FAMILY}}` placeholders resolved at install time. Do not remove consensus, majority, unique, confidence weighting, or post-remediation re-review semantics.
* **Acceptance**: reports identify the anchor reviewer separately from Tier 1/2/3; the global `verify-harness` skill contains no unresolved `{{ANCHOR_REVIEW_*}}` placeholders and resolves the anchor route from the target workspace config at runtime; if the config route is absent or anchor routing is unavailable, the skill records a declared fallback and continues only when reviewer-count and consensus minimums are still satisfied.
* **Verification**: read-only skill/template checks or existing documentation tests that assert reviewer tables and model-routing variables resolve.
* **Manifest**: `.github/skills/verify-harness/SKILL.md` is checksum-tracked in `.autoharness/harness-manifest.yaml`. After editing it, recompute its raw-bytes sha256 and update the matching checksum entry, then confirm `verify_workspace` reports no drift for this artifact. Skipping the refresh leaves the installed harness reporting false drift.

### Unit D — Plan-review and code-review anchor persona routing

* **Domain**: review coordination skill templates.
* **Files**: `templates/skills/plan-review/SKILL.md.tmpl`, `templates/skills/review/SKILL.md.tmpl`.
* **Change**: define how cross-model personas select the anchor route when a model override can be declared. For plan review, prefer the anchor for one cross-model persona that is already triggered by the plan; for code review, allow the anchor reviewer to satisfy the diversity requirement for high-risk template/policy/review-surface diffs.
* **Acceptance**: multi-model remains preferred but not mandatory; if the environment cannot dispatch model-specific personas, the skill declares degradation and applies the same rubric inline rather than silently skipping review.
* **Verification**: template text inspection and any existing skill documentation checks.

### Unit E — Plan-review declared-degradation and persona rubric adapter back-port

* **Domain**: plan-review skill template only.
* **Files**: `templates/skills/plan-review/SKILL.md.tmpl`.
* **Change**: back-port the three requested sections from the backlogit workspace copy while parameterizing paths and persona names: Dispatch Capability and Declared Degradation, Relationship to P-012, and Persona rubric adapter. Use `{{DOCS_PLANS}}`, `{{DOCS_COMPOUND}}`, `{{PRIMARY_LANGUAGE}}`, and `{{PRIMARY_LANGUAGE_LOWER}}`; do not use `docs/exec-plans`, Go-only filenames, or backlogit literals.
* **Acceptance**: the generated skill records literal `dispatch_mode:` and `decision:` fields in appended reviews; both multi-agent dispatch and single-agent declared-degradation modes must cover every selected persona and normalize outputs to P0-P3 findings.
* **Verification**: compare against the backlogit copy for semantic coverage, then normalize to autoharness template conventions and line endings.

### Unit F — Plan-harden and harvest companion gate updates

* **Domain**: skill-template companion contracts.
* **Files**: `templates/skills/plan-harden/SKILL.md.tmpl`, `templates/skills/harvest/SKILL.md.tmpl`.
* **Change**: ensure plan-harden can carry elevated review-gate/capability risks forward, and ensure harvest recognizes the plan-review gate's machine-readable markers (`dispatch_mode:` and `decision:`). Harvest should refuse missing/FAIL decisions and require explicit authorization for ADVISORY if that convention is added.
* **Acceptance**: harvest cannot decompose a plan whose review gate silently skipped dispatch or emitted no decision marker. Plan-harden guidance remains narrow and does not become a second planner.
* **Verification**: targeted template inspection and any existing harvest/plan-review contract tests.

### Unit G — Review persona identity mapping and agent-template references

* **Domain**: review persona agent templates and install path mapping.
* **Files**: `templates/agents/review/*.agent.md.tmpl`, `templates/agents/research/learnings-researcher.agent.md.tmpl` if present, and install-harness review-persona mapping text where identity filenames are declared.
* **Change**: audit the adapter table identity paths used by plan-review. Use installed artifact names, e.g. `.github/agents/review/constitution-reviewer.agent.md`, `.github/agents/review/{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md`, `.github/agents/review/scope-boundary-auditor.agent.md`, and `.github/agents/research/learnings-researcher.agent.md` where installed. Update references only where they are stale or would generate nonexistent paths.
* **Acceptance**: display-name-to-file mapping is valid for Python, TypeScript, and Rust profiles; technology-specific reviewer naming uses existing variables and no Go-only assumptions.
* **Verification**: cross-reference checks for generated reviewer file names.

### Unit H — Install-harness variable table and packaging/documentation update

* **Domain**: install-harness skill documentation and variable resolution table.
* **Files**: `.github/skills/install-harness/SKILL.md`, and any docs that enumerate generated review variables or capability-pack model routing.
* **Change**: document the new anchor review variables and defaults alongside existing `{{ALT_REVIEW_PROVIDER}}` / `{{ALT_REVIEW_FAMILY}}`. If Ship chooses to formalize missing `alt_review` / `alt_doc_review` schema support while adding the anchor route, document that explicitly in the same variable table.
* **Acceptance**: every new `{{ANCHOR_REVIEW_*}}` placeholder introduced in templates is listed with source, example, default, and degradation behavior; no unresolved variable can appear in installed output.
* **Verification**: variable completeness scan and install-harness docs consistency checks.
* **Manifest**: `.github/skills/install-harness/SKILL.md` is checksum-tracked in `.autoharness/harness-manifest.yaml`. After editing it, recompute its raw-bytes sha256 and update the matching checksum entry, then confirm `verify_workspace` reports no drift for this artifact. Skipping the refresh leaves the installed harness reporting false drift.

## Dependency Graph

```text
Unit A (P-012 capability clause) ─┬─> Unit E (plan-review degradation/adapter) ─┬─> Unit F (harvest/plan-harden gates)
Unit G (persona identity mapping) ┘                                             └─> Unit H (install-harness docs)
Unit B (anchor config contract) ─────> Unit C (verify/adversarial anchor slot) ───┘
Unit B (anchor config contract) ─────> Unit D (plan/code review anchor routing) ──┘
```

Units A, B, and G can start independently. Units C and D depend on Unit B so they can reference stable variable names. Unit E depends on the policy clause and identity mapping. Unit F depends on Unit E's machine-readable gate markers. Unit H should run last so the variable table and installation documentation reflect the final names selected by the implementation tasks.

## Decisions and Rationale

1. **Use a first-class anchor route, not `ALT_REVIEW_*` overload.** `ALT_REVIEW_*` currently means one optional alternate provider slot, often Gemini. GPT-5.6 Sol should be an anchor reviewer, so overloading alternate-provider semantics would make the route ambiguous and harder to verify.
2. **Keep consensus assembly unchanged.** The request is model routing, not a change to confidence math. Consensus, majority, unique findings, P0/P1 blocking, and post-remediation re-review must remain intact.
3. **Declare capability degradation locally and in P-012.** Reviewer dispatch is not a backlog registry operation, but it is still a required workflow capability. The plan-review template should own the local fallback semantics while P-012 provides the general policy principle.
4. **Normalize the backlogit plan-review copy, do not paste it verbatim.** The backlogit copy contains Go-specific names and `docs/exec-plans`; autoharness must emit variable-parameterized templates that work for multiple languages and documentation layouts.
5. **Do not require a live GPT-5.6 Sol call in deterministic verification.** CI and template tests should assert routing text/schema/variables, not call external model providers.

## Risks and Caveats

* **Schema/config blast radius:** adding a new model route may require updates in generated config examples, schemas, and variable resolution docs. Mitigation: isolate Unit B and run targeted schema/variable completeness checks.
* **Template variable drift:** any new `{{ANCHOR_REVIEW_*}}` placeholder must be added to install-harness resolution documentation and defaults. Mitigation: Unit H closes after all template changes.
* **Dispatch semantics divergence:** inline plan-review could drift from dispatched persona review. Mitigation: the persona rubric adapter makes the Focus column authoritative in both modes.
* **Provider availability ambiguity:** not all environments can route to GPT-5.6 Sol. Mitigation: generated artifacts must record declared degradation and still satisfy minimum reviewer-count/coverage gates.
* **Backlogit copy assumptions:** the source copy is outside this repository and uses Go-specific names and `docs/exec-plans`. Mitigation: Ship should use it as semantic evidence only and normalize line endings, paths, and placeholders.

## Plan Hardening Signals (REQUIRED)

| Signal | Present? | Justification |
|---|---|---|
| Public API, schema, or contract change | yes | Unit B changes harness configuration schema/contract; Units E/F alter plan-review and harvest gate contracts. |
| Security, auth, permission, or compliance-sensitive behavior | no | No auth or secrets handling is planned. Provider names must not include credentials. |
| Migration, backfill, destructive data/config action, or irreversible step | no | Existing installed workspaces may need tuning guidance, but no destructive migration is planned. |
| External integration, operator checkpoint, or external dependency | yes | GPT-5.6 Sol is an external model route and must degrade when unavailable. |
| High runtime, rollout, or rollback risk | yes | Review-gate templates and workflow-policy changes can affect every generated harness's planning/review pipeline. |

Conclusion: **Requires plan hardening: yes.**

## Plan Hardening

Hardening was required and applied because the work changes generated review-gate behavior, workflow policy, and model-routing contracts across multiple template families.

### Protected Invariants

* Review gates must never be silently skipped. Every plan-review result must record `dispatch_mode:` and `decision:` or fail closed before harvest.
* GPT-5.6 Sol routing must be first-class but not provider-lock the harness; it must be represented through variables/defaults and declared degradation.
* Consensus-based finding assembly in verify-harness/adversarial-review must remain semantically unchanged.
* Template changes must stay environment-agnostic and variable-parameterized.
* No deterministic validation should require a live external model call.

### Risk Controls for Ship

| ProposedAction | ActionRisk | Required control |
|---|---|---|
| Add anchor review model variables and schema/config fields | Generated config drift or unresolved placeholders | Update schema mirrors, harness-config template, install-harness variable table, and variable completeness checks in one dependency-ordered sequence. |
| Change plan-review dispatch/degradation contract | Harvest could accept partial or silently skipped review | Add machine-readable markers and companion harvest checks before considering the gate satisfiable. |
| Generalize P-012 to capabilities | Policy overreach could confuse backlog-tool fallback with non-tool capabilities | Preserve the existing backlog registry/CLI language and add a separate capability clause with examples. |
| Use backlogit plan-review copy as source evidence | Go/path/literal assumptions could leak into templates | Normalize to `{{PRIMARY_LANGUAGE}}`, `{{PRIMARY_LANGUAGE_LOWER}}`, `{{DOCS_PLANS}}`, and installed review persona paths. |

### Verification and Closure Expectations

* Runtime surface: none in the product runtime; this is a template/policy/schema packaging change.
* Required verification before PR: targeted schema validation, variable completeness scan, markdown/template structural checks, and cross-reference integrity for generated persona paths and skill references.
* Operational closure: PR description should list anchor route defaults, declared-degradation behavior, and any follow-up if existing `alt_review` schema support is discovered to be broader than this shipment can safely address.

## Runtime Verification and Closure

| Unit | Runtime surface? | Verification expectation | Closure expectation |
|---|---|---|---|
| A | no | Policy text/cross-reference checks; P-012 still mentions registry fallback and new capability degradation. | Note policy amendment in PR summary. |
| B | no live runtime | Schema/config round-trip or existing harness-config tests; no model call. | Document default anchor route and override behavior. |
| C | agent skill runtime only | Template/skill inspection proves anchor slot and consensus semantics coexist. | Mention no deterministic live provider dependency. |
| D | agent skill runtime only | Plan-review/review skill text includes declared model-routing fallback. | Include review-mode implications in PR summary. |
| E | agent skill runtime only | Template text includes dispatch mode, P-012 relationship, and persona adapter with variableized paths. | Record inline/dispatch parity as release note. |
| F | no product runtime | Harvest/plan-harden templates recognize the new gate markers and fail closed. | Note downstream Stage/Ship behavior. |
| G | no | Cross-reference generated persona identity paths. | Note any intentional filename mapping decisions. |
| H | no | Variable completeness and docs consistency checks. | Close with installed-output unresolved-variable evidence. |

## Plan Review

`dispatch_mode: single-agent-declared-degradation`

`TOOL_DEGRADED: reviewer-subagent-dispatch — single-agent persona pass`

`decision: PASS`

### Gate Rationale

The plan includes the required hardening conclusion and a `## Plan Hardening` section. The inline persona pass covered every selected plan-review persona. No P0 or P1 findings remain, and no P2 finding requires operator authorization before harvest. The implementation units are separated by domain so policy/schema/skill-template/agent-template/install-doc work are not mixed in one task.

### Persona Coverage

| Persona | Mode | Finding summary |
|---|---|---|
| Constitution Reviewer | inline | PASS — Stage boundary is respected; implementation is delegated to Ship; environment-agnostic template constraints are explicit. |
| Python Reviewer | inline | PASS — no Python implementation is planned except possible downstream schema/config tests; tasks require targeted verification without adding speculative dependencies. |
| Scope Boundary Auditor | inline | PASS — units are width-isolated and each has a verifiable exit state; schema/policy/skill-template work is split. |
| Learnings Researcher | inline | PASS — P-012, P-013, review-loop, and deterministic-review learnings are reflected in decisions and controls. |
| Architecture Strategist | inline | PASS — first-class anchor route avoids overloading alternate-provider semantics and preserves consensus assembly. |
| Agent-Native Parity Reviewer | inline | PASS — dispatch-capability degradation is modeled for both sub-agent and inline environments. |
| Security Lens Reviewer | not triggered | Not selected: no auth/authz, sensitive data store, secret-management, or trust-boundary API behavior is planned. |

### Findings

* **P0:** none.
* **P1:** none.
* **P2:** none.
* **P3:** Ship should explicitly decide whether adjacent backlogit enhancements not named in the stash, such as a `## Constitution Check` verdict row, belong in this shipment or should remain a separate follow-up. Do not import them silently as part of the three-section back-port.

### Plan Hardening Requirement Check

Hardening was required due to schema/config, workflow-policy, and review-gate blast radius. The requirement is satisfied by the hardening section above.

### Harvest Readiness

The plan is ready for harvest into one covering feature and dependency-ordered tasks. Harvest must preserve parent-first ordering and keep the two consumed stash IDs attached to the covering feature description.