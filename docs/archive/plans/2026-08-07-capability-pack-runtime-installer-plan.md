---
title: "Implementation Plan — Capability-Pack Runtime Detection & Checklist Increment (47971057, bounded)"
date: "2026-08-07"
description: "Bounded, provisioning-free increment for 47971057: interactive pre-merge-install TUI checklist + per-pack scan/detect/version + recommended-action report + explicit provision-before-compose ordering. No runtime install/upgrade executed."
doc_type: plan
source: docs/archive/plans/2026-08-07-capability-pack-runtime-installer-plan.md
stash_ids: ["47971057"]
model_route:
  model_family: claude-opus-4.8
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/decisions/2026-08-07-capability-pack-runtime-installer-deliberation.md"
  - "scripts/deploy-harness.ps1"
  - "scripts/deploy-harness.sh"
tags: ["47971057", "capability-packs", "plan", "bounded"]
---

# Implementation Plan — Capability-Pack Runtime Detection & Checklist (bounded)

## Objective

Extend the advisory deploy preflight into an interactive pre-merge-install checklist
that scans, detects presence + version, and reports a per-pack recommended
action-category for backlogit / agent-engram / graphtor-docs, and make the
provision-before-compose ordering explicit — **without executing any runtime
install/upgrade or model provisioning** (deferred to operator per the deliberation).

## Affected surfaces (verified)

* `scripts/deploy-harness.ps1`, `scripts/deploy-harness.sh`
* `templates/scripts/deploy-harness.ps1.tmpl`, `templates/scripts/deploy-harness.sh.tmpl`
* deploy/pack UX docs (installer ordering)

## Work decomposition (2-hour rule, width-isolated)

* **T1 (scan/detect)**: extend preflight to detect per-pack presence AND version
  (`<tool> --version` probe; graphtor `.graphtor/bin/` local path) and emit a
  structured per-pack status (present+version / absent / undetectable). Parity across
  `.ps1` + `.sh` + their `.tmpl` templates. No install logic.
* **T2 (interactive checklist + report)**: interactive check/uncheck TUI over the pack
  set that presents T1 detection and a recommended action-category (retain-present /
  needs-install[DEFERRED] / unsupported-undetectable) as a **report only**. Provides a
  non-interactive/CI fallback that prints the same report (no TUI dependence). No
  provisioning execution.
* **T3 (ordering UX + deferral docs)**: document that selected pack runtimes are
  provisioned BEFORE merge-install composition; record that actual provisioning
  execution + all supply-chain/source/version-channel/OS-matrix/model-provisioning
  decisions are DEFERRED-pending-operator, linking the open-questions list.

## Dependencies

* T2 → T1 (checklist consumes detection). T3 → T2 (docs reflect the checklist/report).
  Acyclic.

## Fail-closed guardrails (from deliberation)

* No downloads/installs/upgrades/model provisioning; detection + selection + report only.
* "needs-install" is a deferred recommendation, never auto-executed.
* Headless/CI parity preserved (report without TUI).

## Verification / DoD

* Preflight reports per-pack presence+version+action-category for all three packs.
* Interactive checklist works; CI/non-interactive prints identical report.
* Ordering (provision-before-compose) documented; deferral + open questions recorded.
* No `{{VARIABLE}}` unresolved in templates; cross-references resolve; markdownlint P-008.

## Requires plan hardening

**No** (for this bounded increment). Detection/selection/report only — no runtime
mutation, no supply-chain execution, no schema, single script/template family + docs.
Note: the DEFERRED provisioning-execution phase WILL require P-006 hardening when it
is later un-deferred; that is out of scope here.
