---
title: Capability Packs
description: Formal overlay pattern for optional cross-cutting harness capabilities in autoharness
---

## Overview

Capability packs are the formal mechanism `autoharness` uses for optional, cross-cutting behavior that deepens the installed harness without changing the underlying primitive model.

They are **overlays, not primitives**.

That distinction matters:

* A primitive is irreducible and universal across effective harnesses
* A capability pack is optional and workspace-dependent
* A primitive defines architecture
* A capability pack defines a coordinated overlay across existing artifacts

If a feature can be turned on or off per workspace and still leave the 10-primitive system coherent, it belongs in the capability-pack layer rather than the primitive layer.

## Why overlays exist

Some optional capabilities are too cross-cutting to model as a single generated file.

Examples:

* browser-backed validation needs changes to verification guidance, possibly review expectations, and installer recommendations
* continuous learning needs changes to observation capture, maintenance workflows, and learned-artifact promotion paths
* stricter safety postures need changes to foundation docs, risky execution skills, and tuning guidance
* `agent-intercom` needs heartbeat, operator visibility, approval routing, and standby behavior threaded through the whole lifecycle

If these were modeled as one-off add-ons, the harness would become inconsistent: one file would mention the capability, but the surrounding workflow would behave as if it did not exist.

## Formal overlay contract

Every capability pack in `autoharness` should define the same contract.

### 1. Eligibility signals

Discovery must know what to look for before recommending the pack.

Examples:

* runtime surface markers
* MCP configuration files
* existing instructions or docs already referencing a workflow
* infrastructure or deployment markers

### 2. Recommendation logic

The workspace profile should be able to answer **why** the pack is being recommended.

Typical outcomes:

* recommended automatically
* recommended conditionally
* not recommended

### 3. Overlay targets

A pack must declare which artifact classes it affects.

Typical target classes:

| Target Class | Examples |
|---|---|
| Foundation docs | `AGENTS.md`, `copilot-instructions.md`, constitution |
| Instructions | `*.instructions.md` overlays or pack-specific instruction files |
| Agents | Pipeline agents and support agents |
| Skills | Long-running, risky, or gating workflows |
| Prompts | Heartbeat or orchestration prompts |
| Policies | Workflow or approval policies |

### 4. Behavior deltas

A pack must describe what changes in the harness when it is enabled.

Good behavior deltas are explicit and verifiable:

* new approval path
* stronger safety-mode requirements
* added browser-verification expectations
* extra release-readiness and monitoring detail

### 5. Verification checks

Installation is not complete merely because the pack name appears in the manifest.

Verification must prove that the declared overlay targets were actually updated consistently.

### 6. Tuning drift rules

The tuner must detect:

* a recommended pack that was never enabled
* an enabled pack whose woven targets are only partially present
* stale overlay guidance that remains after the pack was removed
* new workspace signals that should change the overlay target set

## Installation lifecycle

Capability-pack overlays are applied in this order:

1. Discover workspace signals
2. Recommend packs in the workspace profile
3. Select preset and primitive set
4. Select packs
5. Apply pack overlays across all declared targets
6. Verify overlay coherence
7. Record enabled packs and overlay targets in the manifest

This means overlays are **post-selection, pre-verification** composition steps.

## Tuning lifecycle

During tuning, overlays are checked for coherence rather than only presence.

The tuner should compare:

* workspace signals now vs. at install time
* manifest-declared overlay targets vs. actual installed artifacts
* expected behavior deltas vs. present wording and workflow steps

Partially woven overlays should be treated as a real harness-quality problem.

## Current packs in autoharness

| Pack | Primary Purpose | Typical Primitive Impact |
|---|---|---|
| `agent-intercom` | Remote operator visibility, approval routing, and standby handoffs | 4, 5, 6, 7, 10 |
| `agent-engram` | Engram-first indexed search, code graph lookup, and workspace context retrieval | 1, 4, 6, 9 |
| `backlogit` | backlogit-native query, queue, memory, checkpoints, comments, and traceability | 1, 2, 4, 7, 8, 9 |
| `browser-verification` | Browser-backed runtime confidence for web-facing work | 4, 7, 10 |
| `continuous-learning` | Observation capture, instinct formation, and promotion into explicit learned artifacts | 1, 6, 7, 9, 10 |
| `strict-safety` | Stronger default safety posture for risky work | 5, 6, 8 |
| `release-observability` | Richer monitoring and closure expectations | 7, 10 |
| `adversarial-review` | Multi-model parallel review with consensus-weighted findings and remediation queue | 7, 10 |

## Example: agent-engram as a formal overlay

`agent-engram` is a pack for workspaces that use the Engram MCP daemon as a local code graph,
semantic search, and workspace-memory layer.

### Eligibility signals

* `.engram/config.toml`, `.engram/registry.yaml`, or `.engram/code-graph/` exists
* `.vscode/mcp.json` or `.vscode/settings.json` references `agent-engram`, `engram`, or engram tool names
* existing docs already describe Engram-first search, workspace binding, or `.engram/` persistence

### Overlay targets

* Foundation docs
* `agent-engram.instructions.md`
* Research / planning / harnessing / build / repair workflows
* Search-strategy sections in shared guidance

### Behavior deltas

* prefer `unified_search`, `query_memory`, `list_symbols`, `map_code`, `impact_analysis`, and `query_graph` before grep / glob / raw file scans
* verify the engram daemon and workspace binding state before relying on indexed results
* use `sync_workspace` when results appear stale after out-of-band edits
* fall back to file-based search only when indexed lookup is unavailable or insufficient
* if semantic search is unavailable, fall back to `list_symbols` + `map_code` + `impact_analysis` rather than brute-force file reading

### Verification checks

* `agent-engram.instructions.md` is installed
* affected agents and skills reference engram-first lookup and lifecycle checks consistently
* manifest records the overlay target set

This pack does not replace general search guidance. It deepens it when a workspace has Engram available.

## Example: agent-intercom as a formal overlay

`agent-intercom` is the clearest example of why the overlay pattern exists.

### Eligibility signals

* `.intercom/settings.json`
* `.vscode/mcp.json` or settings referencing intercom tools
* existing docs already describing remote approval or operator steering

### Overlay targets

* Foundation docs
* `agent-intercom.instructions.md`
* Pipeline agents
* Long-running and gating skills
* Heartbeat prompt

### Behavior deltas

* heartbeat / ping at session start and during long-running work
* milestone broadcasts during planning, build, review, verification, and closure
* destructive approval routed through the intercom workflow
* transmit / standby flows used for operator clarification and wait states
* degraded-mode warning when intercom is unavailable

### Verification checks

* intercom instruction file installed
* affected agents and skills reference the intercom workflow consistently
* manifest records the overlay target set

This is not a one-file add-on. It is a woven operational behavior layer.

## Example: backlogit as a formal overlay

`backlogit` is an example of a pack that sits on top of the generic backlog-tool abstraction and enables deeper, tool-native behavior when the workspace specifically uses backlogit.

### Eligibility signals

* `backlog_tool.tool_name == backlogit`
* backlogit MCP or CLI registration is present
* backlogit feature flags expose query, queue, memory, checkpoint, dependency, or traceability capabilities

### Overlay targets

* Foundation docs
* `backlogit.instructions.md`
* Backlog integration instructions
* Orchestration / planning agents
* Memory-related agents and workflows

### Behavior deltas

* prefer `backlogit_query_sql` for token-efficient backlog lookup
* prefer `backlogit_get_queue` and dependency operations for ready-work selection
* mirror session state via backlogit memory and checkpoint tools
* use backlogit comments and commit tracking for traceability
* rehydrate the index when direct Markdown edits or stale query results require it

### Verification checks

* backlogit registry exposes the advanced operations referenced by the pack
* `backlogit.instructions.md` is installed
* affected agents mention queue / memory / traceability behaviors consistently

This pack does not replace generic backlog integration. It deepens it when backlogit is the selected backlog tool.

## Example: browser-verification as a formal overlay

`browser-verification` is a pack for workspaces with real web-facing runtime
surfaces and browser-capable verification tooling.

### Eligibility signals

* `runtime_surfaces.web_ui == true`
* browser tooling detected such as Playwright, Cypress, Puppeteer, Selenium, or equivalent
* runtime verification or closure work regularly depends on route-level browser confidence

### Recommendation logic

* **Automatically recommended** when the workspace has a web UI plus browser automation tooling
* **Conditionally recommended** when the workspace has a web UI but browser verification is only partly documented
* **Not recommended** for back-end-only or non-browser products

### Overlay targets

| Artifact | Change |
|---|---|
| `browser-verification.instructions.md` | New instruction file installed with server-readiness, route-selection, headed/headless, and human-checkpoint rules |
| `AGENTS.md` / `copilot-instructions.md` | Add browser-verification overlay guidance |
| `runtime-verification/SKILL.md` | Reference the browser-verification operating model explicitly |
| `operational-closure/SKILL.md` | Carry browser findings and blocked checkpoints into closure artifacts |

### Behavior deltas

* browser verification starts only after confirming server availability and target environment
* route selection is driven by changed surfaces and adjacent critical paths
* headed vs headless mode is chosen intentionally and recorded
* external or operator-assisted flows become explicit checkpoints instead of silent test gaps

### Verification checks

* `browser-verification.instructions.md` is installed
* foundation docs mention the overlay
* runtime verification and closure skills reference the browser workflow consistently

### Tuning drift rules

* browser tooling and web UI exist but the pack is missing - recommend enabling it
* pack enabled but instruction file or woven workflow references are missing - re-weave the overlay
* pack disabled but browser-specific overlay language remains - offer cleanup

## Example: continuous-learning as a formal overlay

`continuous-learning` is a pack for workspaces that want to capture recurring
agent and operator practice as explicit repository knowledge rather than relying
on invisible prompt drift.

### Eligibility signals

* operators want recurring workflow improvements to become durable harness guidance
* repeated review findings, runtime signals, or post-merge lessons keep appearing
* the workspace is willing to store normalized learning state under `.autoharness/`

### Recommendation logic

* **Conditionally recommended** for teams that want explicit learning loops inside the harness
* **Available on request** for other workspaces that prefer to start with a lighter operating model

### Overlay targets

| Artifact | Change |
|---|---|
| `continuous-learning.instructions.md` | New instruction file installed with observation hygiene and promotion rules |
| `AGENTS.md` / `copilot-instructions.md` | Add observation lifecycle and learned-artifact guidance |
| `observe/SKILL.md` | New skill to capture recurring observations |
| `learn/SKILL.md` | New skill to cluster observations into instincts |
| `evolve/SKILL.md` | New skill to promote mature instincts into `learned-*` artifacts |

### Behavior deltas

* recurring workflow signals are captured as normalized observations
* observations are clustered into evidence-backed instincts
* only sufficiently corroborated instincts are promoted into explicit instructions or skills
* environment-specific hook capture stays optional rather than becoming an environment lock-in

### Verification checks

* `continuous-learning.instructions.md` plus `observe`, `learn`, and `evolve` are installed
* foundation docs reference the observation lifecycle consistently
* promotion thresholds and learned-artifact pathways are explicit

### Tuning drift rules

* pack enabled but one or more lifecycle skills are missing - re-install them
* pack disabled but learned-artifact promotion rules remain woven into the harness - offer cleanup
* workspace wants explicit recurring-practice capture but the pack is absent - recommend enabling it

## Conditional reviewer note

The `agent-native-parity-reviewer` is intentionally **not** a capability pack. It
is a conditional review persona that discovery recommends when the workspace
exposes MCP-heavy or parity-sensitive agent-facing product surfaces. Treat it as
review-layer adaptation, not as a separate primitive or overlay pack.

### Stable versus incubating guidance

For backlogit, `autoharness` should distinguish between **stable external
contract** and **incubating internal workflow**.

Stable backlogit contract that can be woven now:

* query-driven lookup
* queue-aware work selection
* dependency operations
* memory and checkpoints
* comments and commit traceability
* metadata discovery and command-map export

Incubating backlogit workflow that should remain in backlogit until proven:

* `groomer` and `shipper` agent choreography
* shipment artifacts and shipment-scoped branch assumptions
* stash JSONL and related storage transitions
* unfinalized file naming or lifecycle rules tied to the emerging two-agent model

Use [Backlogit Operating Model](backlogit-operating-model.md) for the current
boundary, [Backlogit Compatibility Matrix](backlogit-compatibility-matrix.md)
for surface-by-surface status, and
[Backlogit Graduation Checklist](backlogit-graduation-checklist.md) before
promoting incubating workflow changes into templates.

## Design rules

When creating future packs, follow these rules:

1. Do not create a new primitive unless the capability is universal and irreducible
2. Do not model a cross-cutting pack as a single disconnected instruction file
3. Keep packs optional and composable
4. Prefer explicit overlay targets over fuzzy “this influences some files” language
5. Verify the overlay as a system, not file by file in isolation
6. Ensure tuning can detect partially applied overlays later
## Example: adversarial-review as a formal overlay

`adversarial-review` provides multi-model parallel review by dispatching independent reviewer
agents across different model tiers, then assembling findings into a confidence-weighted consensus
report. Agreement across models indicates high-confidence findings; unique findings from a single
model are preserved as low-confidence observations. The output is a structured remediation queue
with findings ordered by `confidence x severity`.

### Eligibility signals

* Workspace profile indicates security-sensitive domains (authentication, payments, data processing, PII handling)
* CI configuration includes compliance gates, security scanning, or audit requirements
* `strict-safety` capability pack is already selected (co-installation recommended)
* Operator explicitly requests higher review confidence or multi-model validation
* Workspace has significant codebase volume (>1000 source files) where single-model blind spots are more likely

### Recommendation logic

* **Automatically recommended** when `strict-safety` is also active
* **Conditionally recommended** when workspace profile includes security or compliance signals
* **Available on request** for all other workspaces that want higher review confidence

### Overlay targets

| Artifact | Change |
|---|---|
| `adversarial-review.agent.md` | New agent installed - implements the parallel dispatch + consensus-assembly protocol |
| `review/SKILL.md` | Add escalation note: recommend adversarial-review when 3+ P0/P1 findings appear |
| `ship.agent.md` | Step 4.4 review gate invokes adversarial-review agent when pack is active |

### Behavior deltas

* Review gate in ship agent uses N parallel reviewer agents (default 3) across Tier 1/2/3 models
* PR pre-merge review produces consensus + majority + unique finding sections with confidence labels
* HIGH-confidence consensus findings block gates identically to standard review P0/P1 findings
* MEDIUM-confidence findings require explicit acknowledgment (fix or defer with rationale)
* LOW-confidence findings are preserved as advisory observations
* Remediation queue entries include confidence tier and action class
* Structured bug/issue queue entries are ready for direct backlog creation

### Verification checks

* `adversarial-review.agent.md` is installed in `.github/agents/`
* `ship.agent.md` contains the `adversarial-review` conditional at the review gate step
* `review/SKILL.md` contains the escalation note
* Manifest records the overlay target set with `adversarial_review_enabled: true`

### Tuning drift rules

* Pack enabled but `adversarial-review.agent.md` is missing from `.github/agents/` - re-install agent
* Pack enabled but `ship.agent.md` does not contain the conditional blocks - re-weave
* Pack disabled but agent file and conditional blocks remain - offer cleanup
* Workspace has gained security or compliance signals since install - recommend enabling the pack
