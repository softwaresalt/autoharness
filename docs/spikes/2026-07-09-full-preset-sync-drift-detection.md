---
title: Full-Preset Harness Sync — Drift Detection Findings
doc_type: spike
date: 2026-07-09
stash_id: 4EEB1131
kind: chore
status: complete
owner: Stage
---

# Full-Preset Harness Sync — Drift Detection (READ-ONLY Spike)

Investigation for stash `4EEB1131`: auto-tune this workspace to the newest full
autoharness preset. Compared the installed `.github` mirror (a **condensed,
hand-authored self-install** — autoharness dogfoods its own harness) against the
source templates, following the verify-harness / tune-harness drift methodology.
Detection was read-only (view/grep/glob + backlogit read). Enabled capability
packs per `.autoharness/workspace-profile.yaml`: **agent-intercom, backlogit,
agent-engram, graphtor-docs**.

Findings distinguish **intentional condensation** (not drift) from **genuine
behavioral drift / missing pack weaves** (remediation-worthy).

## Weave status summary

### feature-flow-dark (P-017 dark factory mode)

| Surface | Status | Notes |
|---|---|---|
| `_orchestrator.agent.md` | ✅ woven | trigger, `DARK_MODE_ACTIVE`, bounded scope, telemetry, stop conditions preserved |
| `.ship.agent.md` | ⚠️ partial | local-review-first, dark approval, admin-fallback present, **but missing merge-commit-only / P-009 gate** the template requires in the dark path |
| `.stage.agent.md` | ✅ n/a | Stage template defines **no** dark-mode role → absence is correct, not drift |
| `github-pr-automation.instructions.md` | ✅ woven | §1.9 gate, dark merge authorization + admin fallback complete |
| `agent-intercom.instructions.md` | ✅ woven | dark visibility protocol + events complete |
| `feature-flow-dark.prompt.md` | ✅ current | matches template shim |
| `AGENTS.md` | ✅ refs present | P-017 in quality gates + workflow |

**Verdict:** feature-flow-dark is *mostly* woven. The one genuine dark-mode gap
is Ship's missing merge-commit-only (P-009) gate in the dark merge path.

### Capability packs

| Pack | Status | Genuine gaps |
|---|---|---|
| agent-engram | ✅ fully woven | instruction in-sync, agent startup checks present, copilot-instructions engram block present |
| agent-intercom | ⚠️ partial | instruction in-sync, **but `ping-loop.prompt.md` missing** (overlay `verification_checks` explicitly requires it) and copilot-instructions intercom block dropped |
| backlogit | ⚠️ partial | registry present, agents wired, **but copilot-instructions backlogit overlay block dropped** |
| graphtor-docs | ⚠️ partial | agent startup checks present, **but instruction dropped the canonical `.mcp.json` registration precedence + editor-local fallback rule** the template now specifies |

## Genuine drift findings (remediation-worthy)

- **D1 — Manifest staleness.** `.autoharness/harness-manifest.yaml` records
  `autoharness_version: 1.3.4` and omits installed artifacts from `artifacts[]`:
  instructions `circuit-breaker`, `coding-discipline`, `github-pr-automation`,
  `output-timestamps`; prompts `feature-flow-dark`, `feature-flow-parallel`,
  `feature-flow`. No checksums recorded for them.
- **D2 — Ship agent material drift.** Missing Role Boundary (NON-NEGOTIABLE)
  table + P-010 self-check (P-010 quality gate requires *both* Stage and Ship to
  declare one; Stage has it, Ship does not); missing merge-commit-only / P-009
  dark-mode gate; missing Post-Merge Branch Protocol (post-merge closure branch +
  PR); reduced circuit-breaker / escalation set.
- **D3 — Orchestrator material drift.** Missing Staging Artifact Merge Gate
  before Ship handoff; missing Elective Agents / install-tune routing (Step E1 +
  active-Ship block); reduced trigger/intent surface. (Behaviors shipped via
  026-F, 019-F not reflected in the condensed installed orchestrator.)
- **D4 — Stage agent material drift.** Missing Step Sequence Contract / mandatory
  checklist; missing Contextual Grouping Analysis + Learnings Retrieval; plan
  hardening reduced to a one-liner (no P-006 Gate Bypass Guard fail-safe);
  shipment handoff safety reduced (no `harvest_ids` scope guard, manifest
  verification, or stash-archive step).
- **D5 — copilot-instructions.md partial pack weave.** Only the Engram overlay
  block is present; agent-intercom, backlogit, and graphtor-docs overlay blocks
  the template carries were dropped, despite all four packs being enabled.
- **D6 — AGENTS.md enabled-pack pointer dropped.** Foundation map no longer
  points to enabled packs. NOTE: harness-architecture mandates AGENTS.md remain a
  short *map, not a manual* — remediation must add a brief pointer, **not** full
  overlay sections.
- **D7 — Missing agent-intercom `ping-loop.prompt.md`.** Template exists; the
  intercom overlay `verification_checks` require "ping-loop prompt references
  intercom heartbeat"; copilot-instructions template also expects it. Not
  installed → genuine missing intercom weave.
- **D8 — graphtor-docs.instructions.md partial drift.** Installed dropped the
  canonical workspace-root `.mcp.json` registration precedence + editor-local
  fallback rule that the current template specifies.
- **D9 — Broken constitution cross-reference.** `harness-architecture.instructions.md`
  lists `constitution.instructions.md` as a key Primitive-5 artifact, but no
  `.github/instructions/constitution.instructions.md` is installed. Violates the
  "all cross-references must resolve" quality gate.
- **D10 — Missing cross-referenced base instructions.**
  - `pull-request.instructions.md` + `ci-security.instructions.md` — installed
    `github-pr-automation.instructions.md` explicitly extends and falls back to
    both; neither is installed (broken cross-refs).
  - `role-enforcement.instructions.md` — harness-architecture says it is
    conditionally installed when both Stage and Ship exist (they do); underpins
    the P-010 self-check.
  - `concurrency.instructions.md` — installed `circuit-breaker.instructions.md`
    depends on a "concurrency protocol" for stall handling that no installed file
    defines.

## Explicitly NOT drift (intentional condensation / omission)

- `.github/skills/` holds only the 4 engine skills (install/tune/verify/discovery).
  The harness pipeline skills (deliberate, impl-plan, harvest, review, …) live
  only as templates — the dogfood agents inline that methodology. Not drift.
- Non-enabled packs (strict-safety, continuous-learning, browser-verification,
  technology-*) absent from `.github/instructions/` — intentional.
- `stage-grouping-analysis.prompt.md` uninstalled — no overlay verification check
  requires it; template-only feature, non-blocking (noted, not remediated).
- Base instructions `commit-message`, `markdown`, `writing-style`,
  `context-efficiency`, `git-merge` absent — no strong installed dependency
  signal; overlapping policy already covered in AGENTS.md. Not flagged.
- `P-013` defined-but-only-in-registry — a rename policy, not broken. Noted only.

## Not deferred

No remediation here removes a shipped policy without a named replacement, so no
items are deferred/gated. All findings are additive or corrective.
