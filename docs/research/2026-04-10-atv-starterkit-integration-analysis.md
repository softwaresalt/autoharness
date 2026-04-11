---
title: "ATV starterkit integration analysis"
description: "Read-only evaluation of atv-starterkit with candidate integrations for autoharness primitives, templates, capability packs, and installer/tuner behavior"
ms.date: 2026-04-10
ms.topic: research
keywords:
  - autoharness
  - atv-starterkit
  - integration analysis
  - capability packs
  - primitives
  - continuous learning
  - drift detection
  - browser verification
  - deployment verification
---

## Purpose

This document captures a read-only evaluation of `D:\Source\GitHub\atv-starterkit`
and identifies what should be integrated into autoharness, what should remain
external, and how the useful pieces should be woven into autoharness's existing
architecture.

The goal is not to import ATV wholesale. The goal is to extract **atomic,
practical, workspace-agnostic improvements** that strengthen autoharness's
existing two-agent model, 10 primitives, and capability-pack overlay system.

## Scope and method

This analysis covered:

1. ATV foundation and operating-model files:
   * `README.md`
   * `.github\copilot-instructions.md`
   * `.github\skills\ce-plan\SKILL.md`
   * `.github\skills\ce-work\SKILL.md`
   * `.github\skills\ce-review\SKILL.md`
   * `.github\skills\ce-compound\SKILL.md`
   * `.github\skills\deepen-plan\SKILL.md`
   * `.github\skills\test-browser\SKILL.md`
   * `.github\skills\learn\SKILL.md`
   * `.github\skills\observe\SKILL.md`
   * `.github\skills\evolve\SKILL.md`
   * `.github\skills\ce-compound-refresh\SKILL.md`
   * `.github\skills\agent-native-architecture\SKILL.md`
2. Representative ATV agents:
   * `.github\agents\learnings-researcher.agent.md`
   * `.github\agents\deployment-verification-agent.agent.md`
   * `.github\agents\agent-native-reviewer.agent.md`
3. ATV installer/runtime internals:
   * `pkg\detect\detect.go`
   * `pkg\scaffold\catalog.go`
   * `pkg\tui\presets.go`
   * `pkg\tui\wizard.go`
   * `pkg\installstate\types.go`
   * `pkg\installstate\manifest.go`
   * `pkg\installstate\recommendations.go`
   * `pkg\monitor\drift.go`
   * `pkg\monitor\executor.go`
   * `pkg\monitor\state.go`
   * `pkg\scaffold\templates\hooks\copilot-hooks.json`
   * `pkg\scaffold\templates\hooks\scripts\observe.js`
4. The corresponding autoharness surfaces:
   * `docs\primitives.md`
   * `docs\capability-packs.md`
   * `schemas\workspace-profile.schema.json`
   * `schemas\harness-manifest.schema.json`
   * `schemas\harness-config.schema.json`
   * `templates\foundation\AGENTS.md.tmpl`
   * `templates\agents\stage.agent.md.tmpl`
   * `templates\agents\ship.agent.md.tmpl`
   * `templates\agents\research\learnings-researcher.agent.md.tmpl`
   * `templates\skills\compound\SKILL.md.tmpl`
   * `templates\skills\compact-context\SKILL.md.tmpl`
   * `templates\skills\review\SKILL.md.tmpl`
   * `templates\skills\runtime-verification\SKILL.md.tmpl`
   * `templates\skills\operational-closure\SKILL.md.tmpl`

## Executive summary

ATV has a coherent operating model built from five strong ideas:

1. **Artifact-gated workflow phases**: brainstorm -> plan -> deepen -> work ->
   review -> test -> compound, with explicit gate conditions.
2. **Optional workflow depth**: a thin Compound Engineering path, plus richer
   gstack/browser layers when the environment supports them.
3. **Continuous learning**: observe tool use, extract instincts, evolve mature
   patterns into discoverable skills.
4. **Persona-heavy review**: specialized reviewers for correctness, security,
   architecture, performance, and agent-native parity.
5. **Operational validation after code success**: browser checks, deployment
   checklists, canary-style follow-through, and documentation refresh.

Autoharness already has the stronger base architecture:

* the **10 primitive model** (`docs\primitives.md`)
* the **capability-pack overlay contract** (`docs\capability-packs.md`)
* the **Stage/Ship two-agent workflow**
* **backlog-aware decomposition and execution**
* explicit **runtime verification** and **operational closure**

Because of that, the best ATV integrations are **not** replacements for
autoharness core orchestration. They are:

1. **new or stronger leaf skills**
2. **new optional capability packs**
3. **tighter installer/tuner mechanics**
4. **more concrete guidance inside existing primitives**

## What ATV contributes that autoharness does not already have

### 1. Explicit knowledge-maintenance workflows

Autoharness already has:

* `templates\skills\compound\SKILL.md.tmpl`
* `templates\agents\research\learnings-researcher.agent.md.tmpl`
* `templates\skills\compact-context\SKILL.md.tmpl`

ATV adds two things autoharness does not currently model as first-class
workflows:

* **learning extraction from observed behavior** via `learn`, `observe`,
  and `evolve`
* **maintenance of existing learnings** via
  `.github\skills\ce-compound-refresh\SKILL.md`

This is the highest-value ATV knowledge contribution.

### 2. Stronger deployment verification patterns

Autoharness already has runtime verification and closure, but ATV's
`deployment-verification-agent.agent.md` is much more concrete about:

* invariants
* pre-deploy checks
* post-deploy checks
* rollback procedure
* validation window
* owner and monitoring details

This maps directly into Primitive 10.

### 3. Better browser-verification recipes

Autoharness already has a `browser-verification` capability pack and a
`runtime-verification` skill that mentions browser mode. ATV's
`test-browser\SKILL.md` contributes sharper operational recipes:

* headed vs headless choice
* port detection
* dev-server verification
* route selection from changed files
* human verification pauses for OAuth, payments, email, SMS

### 4. A real continuous-learning loop

ATV's observation hook file and `observe.js` script demonstrate a practical
learning loop:

* capture lifecycle events to `.atv\observations.jsonl`
* infer recurring patterns
* store them as instincts
* promote mature instincts into generated `learned-*` skills

Autoharness has strong durable knowledge patterns, but this specific
observe -> learn -> evolve loop is not present today.

### 5. Installer/tuner ergonomics

ATV's installer internals are not more sophisticated than autoharness's
architecture, but they do contribute useful implementation patterns:

* **additive stack packs** in `pkg\detect\detect.go` and `pkg\tui\wizard.go`
* **preset composition** in `pkg\tui\presets.go`
* **manifest + checksum persistence** in `pkg\installstate\manifest.go`
* **deterministic drift classification** in `pkg\monitor\drift.go`
* **repo-state-derived recommendations** in `pkg\installstate\recommendations.go`

Autoharness already has manifest schemas and capability packs, so the
opportunity is to strengthen install/tune behavior, not adopt ATV's UI.

## What autoharness already does better than ATV

### 1. Primitive-based architecture

ATV has a strong workflow bundle, but autoharness has the better abstraction:
the 10 irreducible primitives plus formal capability packs. That is a stronger
foundation for a global harness generator than ATV's productized bundle of
slash commands.

### 2. Backlog-aware two-agent orchestration

ATV's CE flow is plan-centric and repository-artifact-centric. Autoharness's
Stage/Ship model is stronger because it explicitly separates:

* stash intake and decomposition (`stage`)
* execution and closure (`ship`)
* durable knowledge vs active work
* backlog sequencing vs docs and memory

That is a better fit for autoharness's cross-workspace mission.

### 3. Environment agnosticism

ATV is deeply optimized for GitHub Copilot and related workflow hooks.
Autoharness explicitly supports GitHub Copilot CLI, Copilot Chat, Cursor,
Codex, Claude Code, and similar environments. Any ATV integration must preserve
that neutrality.

## Integration candidates

## Candidate 1: Add a `compound-refresh` skill

### ATV evidence

* `atv-starterkit\.github\skills\ce-compound-refresh\SKILL.md`

### Why it is worth integrating

Autoharness already knows how to **create** learnings and how to **compact**
knowledge artifacts, but it does not have a first-class workflow for
**reviewing, updating, consolidating, replacing, or deleting stale learnings**.

That is a real gap. Over time, compound libraries drift. ATV has already
codified a maintenance workflow for that problem.

### Proposed autoharness integration

Create:

* `templates\skills\compound-refresh\SKILL.md.tmpl`

Wire it into:

* `ship.agent.md.tmpl` post-merge closure
* the tuner as a recommendation when compound artifacts drift from code reality

Suggested behavior:

* scope to `{{DOCS_COMPOUND}}`
* classify docs as keep / update / consolidate / replace / delete
* prefer evidence-backed maintenance over cosmetic churn
* optionally mark uncertain docs as stale instead of changing them blindly

### Primitive fit

* **Primitive 1** — state, context, knowledge retrieval
* **Primitive 7** — observability and evaluation
* **Primitive 9** — repository knowledge and legibility

### Recommendation

**Integrate directly.** This is the strongest direct skill candidate from ATV.

---

## Candidate 2: Strengthen runtime verification and operational closure with ATV's deployment checklist pattern

### ATV evidence

* `atv-starterkit\.github\agents\deployment-verification-agent.agent.md`
* `atv-starterkit\.github\skills\test-browser\SKILL.md`
* README sections on QA, ship, canary, and release follow-through

### Why it is worth integrating

Autoharness already has:

* `templates\skills\runtime-verification\SKILL.md.tmpl`
* `templates\skills\operational-closure\SKILL.md.tmpl`

Those templates have the right structure but are intentionally generic.
ATV contributes more operationally concrete checklist content:

* invariants to preserve
* pre-deploy audits
* post-deploy checks
* rollback conditions
* monitoring plan
* validation window and owner

### Proposed autoharness integration

Do **not** import ATV's agent as-is. Instead:

1. Extend `runtime-verification` to include:
   * environment-precheck flow
   * browser-mode route selection heuristics
   * human verification stop points for flows that require a user
2. Extend `operational-closure` to require:
   * healthy signals
   * failure signals
   * rollback trigger
   * validation window
   * owner
3. Optionally add a specialized review/deployment persona for workspaces with:
   * migrations
   * data backfills
   * production data transformations

### Primitive fit

* **Primitive 4** — orchestration and handoffs
* **Primitive 7** — evaluation
* **Primitive 10** — operational closure and feedback

### Recommendation

**Integrate directly into existing skills.** No new primitive required.

---

## Candidate 3: Expand the `browser-verification` capability pack

### ATV evidence

* `atv-starterkit\.github\skills\test-browser\SKILL.md`
* README browser QA and benchmark sections

### Why it is worth integrating

Autoharness already treats browser verification as an optional overlay in
`docs\capability-packs.md`, but its pack definition is still broad. ATV
provides a better operational recipe for what the pack should actually change.

### Proposed autoharness integration

Strengthen the existing `browser-verification` pack with:

* **eligibility signals**
  * `runtime_surfaces.web_ui == true`
  * detected browser tooling or test runners
* **behavior deltas**
  * headed/headless decision
  * route selection from changed files or affected surfaces
  * server availability checks before browser work
  * human verification checkpoints for external flows
* **overlay targets**
  * `runtime-verification`
  * `operational-closure`
  * any pack-specific instructions file

### Primitive fit

* **Primitive 4**
* **Primitive 7**
* **Primitive 10**

### Recommendation

**Strengthen the existing pack** rather than creating a new one.

---

## Candidate 4: Add a continuous-learning capability pack

### ATV evidence

* `atv-starterkit\.github\copilot-instructions.md`
* `atv-starterkit\.github\skills\observe\SKILL.md`
* `atv-starterkit\.github\skills\learn\SKILL.md`
* `atv-starterkit\.github\skills\evolve\SKILL.md`
* `atv-starterkit\pkg\scaffold\templates\hooks\copilot-hooks.json`
* `atv-starterkit\pkg\scaffold\templates\hooks\scripts\observe.js`

### Why it is worth integrating

This is ATV's most distinct architectural idea that autoharness does not
already implement:

* observe real agent behavior
* infer reusable patterns
* accumulate confidence
* graduate mature conventions into discoverable skills

This is different from autoharness's current compound model. Compound captures
**explicit solved problems**. ATV's learning loop captures **observed recurring
practice**.

### Proposed autoharness integration

Create a new optional capability pack such as:

* `continuous-learning`
* or `adaptive-conventions`

The pack would include:

* `observe` skill
* `learn` skill
* `evolve` skill
* storage under a configurable repo-local directory
* generated `learned-*` skills or instructions

Important constraint:

* keep **hook capture** environment-specific and optional
* preserve autoharness's environment-agnostic base model

Suggested overlay targets:

* foundation docs
* one or more new skills
* possibly a pack-specific instructions file
* manifest overlay records

### Primitive fit

* **Primitive 1** — state and knowledge
* **Primitive 6** — dynamic reminders via evolved conventions
* **Primitive 7** — observability and evaluation
* **Primitive 9** — repository knowledge

### Recommendation

**Add as a new optional capability pack**, not a primitive and not a default.

---

## Candidate 5: Add a conditional agent-native parity reviewer

### ATV evidence

* `atv-starterkit\.github\skills\agent-native-architecture\SKILL.md`
* `atv-starterkit\.github\agents\agent-native-reviewer.agent.md`

### Why it is worth integrating

ATV has a clear and useful review lens for agent-native software:

* parity between UI actions and agent actions
* parity between user-visible context and agent-visible context
* preference for atomic tools over embedded workflow logic
* shared workspace over separate agent sandboxes

This is not universal enough to become a primitive, but it is a useful review
persona for workspaces building agent-facing products or MCP-backed apps.

### Proposed autoharness integration

Add a conditional review persona or specialized agent that activates when
workspace discovery detects:

* `frameworks.mcp_sdk`
* `frameworks.mcp_transport`
* explicit agent-tooling surfaces
* application features where user actions must be mirrored for agents

It should slot into:

* `review\SKILL.md.tmpl`
* possibly `plan-review\SKILL.md.tmpl` for agent-native product planning

### Primitive fit

* **Primitive 7** — review/evaluation
* **Primitive 9** — repo legibility for agent-native systems

### Recommendation

**Integrate conditionally** for agent-native and MCP-heavy workspaces.

---

## Candidate 6: Add a lightweight plan-hardening step

### ATV evidence

* `atv-starterkit\.github\skills\deepen-plan\SKILL.md`
* `atv-starterkit\.github\skills\lfg\SKILL.md`

### Why it is worth integrating

ATV explicitly distinguishes:

* creating a plan
* hardening a plan with deeper research
* reviewing the hardened plan

Autoharness already has `impl-plan` and `plan-review`, but no named middle step
for selectively deepening risky plans before the review gate.

### Proposed autoharness integration

Do **not** import ATV's plugin-discovery or broad skill-fanout behavior.
Instead, introduce a narrow autoharness-native hardening step for cases like:

* public API changes
* security-sensitive work
* migrations or data transformations
* external integrations
* high-runtime-risk features

The hardening step should:

* pull in `learnings-researcher`
* reinforce relevant instructions
* enrich verification, operational, and rollback sections before plan review

Possible implementation:

* add an optional `plan-harden` skill
* or extend `impl-plan` with an explicit high-risk enrichment branch

### Primitive fit

* **Primitive 4** — orchestration and handoffs
* **Primitive 6** — dynamic reminders
* **Primitive 10** — closure readiness in planning

### Recommendation

**Integrate as a narrow, risk-triggered plan-hardening step**, not as a full
ATV-style meta-orchestrator.

---

## Candidate 7: Reuse ATV's installer composition logic in autoharness install/tune

### ATV evidence

* `pkg\detect\detect.go`
* `pkg\tui\presets.go`
* `pkg\tui\wizard.go`
* `pkg\scaffold\catalog.go`

### Why it is worth integrating

ATV's Go TUI is not portable into autoharness, but its composition logic is
clean and proven:

* detect multiple stack signals
* normalize them into additive packs
* choose a primary stack
* apply layers/components based on preset

Autoharness already has:

* `schemas\workspace-profile.schema.json`
* `schemas\harness-config.schema.json`
* install presets
* capability packs

The opportunity is to make install/tune more precise, not to copy the UI.

### Proposed autoharness integration

Reuse the logic pattern for:

* additive `stack_packs` in discovery/config
* explicit install layers or artifact classes
* clearer preset-to-overlay mapping
* better explanations for why a pack or preset is recommended

This belongs in:

* workspace discovery logic
* install-harness
* tune-harness
* config schema evolution

### Primitive fit

This is not a primitive change. It is an **installer/tuner composition
improvement**.

### Recommendation

**Adopt the logic, reject the TUI implementation.**

---

## Candidate 8: Add deterministic drift scanning to Tune using autoharness's existing manifest model

### ATV evidence

* `pkg\installstate\manifest.go`
* `pkg\monitor\drift.go`
* `pkg\monitor\state.go`

### Why it is worth integrating

ATV demonstrates a clean checksum-based drift pass:

* store hashes at install time
* re-hash current files later
* classify drift
* feed the result into recommendations

Autoharness already has the necessary data model:

* `schemas\harness-manifest.schema.json` stores per-artifact `checksum`

So the value is **not** a manifest redesign. The value is adding a **tune-time
drift scanner** and a clearer classification/recommendation flow.

### Proposed autoharness integration

Add a tune-time drift scanner that:

* compares installed artifact hashes to manifest checksums
* classifies at least:
  * missing
  * user-modified
* supports ignore patterns such as `.autoharness\drift-ignore`
* feeds summary output into tuning recommendations

This should update or complement:

* `workspace-profile.drift_report`
* tune-harness recommendations
* pack-specific drift checks

### Primitive fit

* **Primitive 7** — observability/evaluation
* tuner/maintenance lifecycle

### Recommendation

**Integrate into Tune.** This is a concrete and practical improvement.

---

## Candidate 9: Formalize a risk-classified action contract inside `strict-safety`

### ATV evidence

* `pkg\monitor\executor.go`
* `pkg\monitor\state.go`

### Why it is worth integrating

ATV's Go executor itself is too ATV-specific to port. Its command allowlist is
tailored to ATV commands and local runtime assumptions.

What is useful is the **contract shape**:

* `ProposedAction`
* `ActionRisk`
* `ActionResult`

This is a good way to make safety posture more legible and machine-readable.

### Proposed autoharness integration

Do not create a runtime executor in autoharness. Instead:

* use the action/risk/result vocabulary in `strict-safety`
* require risky workflows to classify intended actions
* route destructive or high-blast-radius actions through pack-specific approval
  or operator confirmation flows

This sharpens Primitive 5 without making autoharness dependent on a specific
command broker.

### Primitive fit

* **Primitive 5** — safety and guardrails
* **Primitive 8** — workflow policy

### Recommendation

**Adopt the contract language, not the ATV executor.**

## Primitive-by-primitive impact summary

| Primitive | ATV contribution worth integrating |
|---|---|
| **1. State, Context, Knowledge** | `compound-refresh`; continuous-learning pack; richer knowledge maintenance workflows |
| **4. Orchestration, Handoffs** | optional plan-hardening step; more explicit workflow gating patterns |
| **5. Safety, Guardrails** | risk-classified action contract vocabulary |
| **7. Observability, Evaluation** | agent-native parity reviewer; drift scanning; continuous-learning loop |
| **9. Repository Knowledge** | maintenance of learnings; evolved conventions as durable repo knowledge |
| **10. Operational Closure** | richer deployment verification, rollback, monitoring, and validation-window artifacts |

## Recommendations to reject or defer

## Reject 1: importing ATV's full CE/gstack workflow as autoharness core

### Why

Autoharness's Stage/Ship + backlog + primitives model is more universal and
better aligned with its role as a global harness generator.

ATV's plan-first slash-command stack is a useful reference library, but not the
right orchestration core for autoharness.

### Alternative

Borrow leaf patterns and optional overlays only.

---

## Reject 2: adopting ATV's file-based todo system as a default model

### Why

ATV's `file-todos` and `triage` workflows conflict with autoharness's deliberate
separation between:

* backlog/work item state
* durable docs and memory

Autoharness already has a better abstraction via the backlog tool registry and
backlog capability packs.

### Alternative

Keep file-based task tracking, if at all, as an adapter example or a fallback
for simple/manual workspaces, not as the default harness model.

---

## Reject 3: porting ATV's TUI

### Why

The TUI is product UI, not harness architecture. Autoharness should keep the
composition logic and schema patterns, but implement them through discovery,
configuration, prompts, and tuning workflows.

### Alternative

Reuse ATV's layering and stack-pack logic in install/tune internals.

---

## Defer 1: mandatory Copilot hook capture

### Why

ATV's hook files are useful in GitHub Copilot environments, but autoharness is
explicitly environment-agnostic.

### Alternative

Include hook capture only inside the optional continuous-learning pack, with
per-environment adapters.

## Proposed integration sequence

### Wave 1: highest-confidence, lowest-coupling improvements

1. Add `compound-refresh`
2. strengthen `operational-closure`
3. strengthen `runtime-verification`
4. add checksum-based drift scanning to Tune

### Wave 2: optional overlays with clear ROI

1. add continuous-learning capability pack
2. strengthen `browser-verification`
3. add conditional agent-native reviewer

### Wave 3: install/tune ergonomics

1. add additive stack-pack logic
2. improve preset/layer composition
3. improve deterministic recommendations from discovery/tune

### Wave 4: selective workflow deepening

1. add plan-hardening for risky work
2. expand review/closure interplay for high-risk changes

## Recommended final position

ATV should be treated as a **source of tactical patterns**, not as a candidate
replacement architecture.

The most practical autoharness integrations are:

1. **`compound-refresh`**
2. **stronger deployment-verification and closure artifacts**
3. **a continuous-learning optional pack**
4. **a better `browser-verification` overlay**
5. **Tune-time deterministic drift scanning**
6. **a conditional agent-native review persona**

The key guardrail is to keep all of those changes aligned with the autoharness
model:

* primitives remain the architectural foundation
* capability packs remain optional overlays
* Stage/Ship remains the orchestration model
* backlog abstraction remains the work-state system
* environment-specific capture mechanisms remain optional

That path lets autoharness absorb ATV's strongest ideas without becoming
Copilot-specific, productized-slash-command-first, or less general than it is
today.
