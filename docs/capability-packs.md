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
| `browser-verification` | Browser-backed runtime confidence for web-facing work | 4, 7, 10 |
| `strict-safety` | Stronger default safety posture for risky work | 5, 6, 8 |
| `release-observability` | Richer monitoring and closure expectations | 7, 10 |

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

## Design rules

When creating future packs, follow these rules:

1. Do not create a new primitive unless the capability is universal and irreducible
2. Do not model a cross-cutting pack as a single disconnected instruction file
3. Keep packs optional and composable
4. Prefer explicit overlay targets over fuzzy “this influences some files” language
5. Verify the overlay as a system, not file by file in isolation
6. Ensure tuning can detect partially applied overlays later