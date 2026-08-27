---
source: docs/plans/2026-08-07-capability-pack-runtime-installer-decided-plan.md
title: "Capability-Pack Runtime Detection & Checklist Increment"
doc_type: decided-plan
status: planned
created: 2026-08-07
supersedes:
  - docs/archive/plans/2026-08-07-capability-pack-runtime-installer-plan.md
---

# Decided Plan: Capability-Pack Runtime Detection & Checklist Increment

**Outcome:** Planned as the bounded follow-up harvested from stash `47971057`. The source plan records no PR or merge evidence, so status remains `planned`. The decided increment stops at detection, selection, and reporting: it adds per-pack presence/version scanning, an interactive pre-merge-install checklist, and explicit provision-before-compose ordering, while leaving all runtime installation, upgrade, and model provisioning decisions deferred to the operator.

## Decisions

- Extend the advisory deploy preflight into an **interactive pre-merge-install checklist** that covers backlogit, agent-engram, and graphtor-docs.
- Detect both **presence and version** for each pack runtime, including local graphtor binary probing, and report a per-pack recommended action category instead of trying to mutate the environment.
- Keep the increment provisioning-free: `needs-install` is a recommendation in the report, not an automatic install path.
- Make the lifecycle ordering explicit: selected pack runtimes are provisioned **before** merge-install composition, but that provisioning workflow is not part of this bounded increment.
- Preserve non-interactive parity: CI/headless runs print the same checklist outcome as a report even when no TUI can run.

## Implementation (3 tasks)

- **T1 — Scan/detect:** extend deploy preflight to probe per-pack presence and version in both PowerShell and shell entry points plus their templates.
- **T2 — Interactive checklist + report:** add the TUI checklist, present the scan results with recommended action categories, and keep an equivalent non-interactive report mode.
- **T3 — Ordering and deferral docs:** document provision-before-compose ordering and record the still-deferred supply-chain, version-channel, OS-matrix, and model-provisioning questions.

## Key constraints preserved

- No downloads, installs, upgrades, or model provisioning are executed here.
- PowerShell and shell scripts, plus their templates, stay behaviorally aligned.
- The report remains usable in both interactive and non-interactive contexts; the checklist is a presentation layer, not a required runtime dependency.
- Template output must stay clean: no unresolved `{{...}}` placeholders and no cross-reference drift in the accompanying docs.

## Rejected alternatives

- **Executing runtime installs or upgrades inside this increment** — rejected because the operator has not yet resolved the provisioning decisions and hardening requirements for that phase.
- **Making the flow TUI-only** — rejected to preserve CI/headless parity.
- **Coupling detection to supply-chain/source/version-channel decisions now** — rejected so the increment can remain bounded, provisioning-free, and reviewable.