---
title: "Capability-Pack Runtime Installer (47971057) — Bounded Detection Increment vs. Deferred Provisioning"
date: "2026-08-07"
description: "Deliberation for 47971057. Frames the capability-pack runtime installer, chooses a safe/decidable bounded increment (interactive pre-merge-install TUI checklist + per-pack scan/detect/version + recommended-action report, detection/planning only), and defers actual runtime provisioning plus all supply-chain/source/OS-matrix design to operator with recorded open questions."
topic: "What part of the capability-pack runtime installer is safely decidable now, and what must be deferred to operator design decisions?"
depth: "decision"
decision_status: "decided-bounded"
doc_type: decision
source: docs/decisions/2026-08-07-capability-pack-runtime-installer-deliberation.md
stash_ids: ["47971057"]
model_route:
  model_family: claude-opus-4.8
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "scripts/deploy-harness.ps1"
  - "scripts/deploy-harness.sh"
  - "templates/scripts/deploy-harness.ps1.tmpl"
  - "templates/scripts/deploy-harness.sh.tmpl"
tags: ["capability-packs", "runtime-installer", "47971057", "provisioning", "bounded-increment"]
---

# Capability-Pack Runtime Installer (47971057)

## Problem frame (stash 47971057)

Autoharness must actually install/upgrade external capability-pack runtimes
(backlogit, agent-engram/engram, graphtor-docs) before merge-install, via an
interactive TUI checklist that, per selected pack, scans for a pre-existing install,
detects existence + version, and offers fresh-install / upgrade / retain-skip /
unsupported. Provisioning must precede the merge-install composition. The stash
carries an **explicit OPEN DESIGN QUESTIONS block marked "do NOT silently decide."**

## Verified current state (read-only)

`scripts/deploy-harness.ps1` / `.sh` (and their `.tmpl` templates) run an **advisory**
preflight that only checks *presence* of `backlogit`, `engram`, `graphtor-docs` via
`Get-Command` (plus a graphtor workspace-local `.graphtor/bin/` path). It does NOT
detect version, download, install, upgrade, pin, checksum/signature-verify, or
provision embedding models — matching the stash's stated CURRENT GAP.

## Decidability partition

| Portion | Decidable & safe now? | Rationale |
|---|---|---|
| Interactive pre-merge-install checklist (check/uncheck packs) | **Yes** | UX over the existing pack set; no new external decisions. |
| Per-pack scan + detect presence **and version** (`<tool> --version`; graphtor local path) | **Yes** | Cross-platform probe; extends existing advisory detection. |
| Recommended action **category** (retain-present / needs-install(deferred) / undetectable→unsupported) as a REPORT | **Yes** | Classification only; no execution, no upgrade-target needed. |
| Explicit install-ORDER UX/docs (provision runtimes BEFORE merge-install composition) | **Yes** | Documentation/sequencing statement. |
| Actual install/upgrade EXECUTION | **No — DEFER** | Needs authoritative sources, version/channel, elevation, PATH refresh. |
| Supply-chain: pinning, checksums, signatures | **No — DEFER** | Security policy requires operator decision. |
| OS/platform support matrix | **No — DEFER** | Operator scope decision. |
| Embedding-model provisioning (graphtor) | **No — DEFER** | Source/licensing/size decisions. |
| Offline/proxy/customer-network, rollback/partial-failure, non-interactive/CI parity, idempotence, upgrade-compat, licensing/consent, self-bootstrap ordering | **No — DEFER** | The stash's explicit do-not-decide list. |

## Options

* **Option A — Implement full provisioning now.** *Rejected*: silently decides the
  operator's marked open questions (sources, supply-chain, OS matrix, elevation);
  violates the stash directive and the fail-closed posture.
* **Option B — Defer everything (deliberation only).** *Rejected*: gives up real,
  safe, decidable value (better detection + checklist + ordering docs) that the
  operator directive ("stage as far as evidence supports") wants captured.
* **Option C — Bounded detection/checklist/report increment now; defer provisioning
  execution + all supply-chain/source/OS design (CHOSEN).** Extend the advisory
  preflight into an interactive TUI checklist that scans, detects presence+version,
  and REPORTS a per-pack recommended action-category, with an explicit
  provision-before-compose ordering statement — **no runtime install/upgrade is
  executed.** All execution + the open design questions are deferred to operator.

## Fail-closed guardrails on the chosen increment

* The increment performs **no downloads, installs, upgrades, or model provisioning**
  and mutates no runtime — it is detection + interactive selection + reporting.
* "needs-install" is reported as a **deferred** recommendation, never auto-executed.
* Non-interactive/CI invocation prints the same report (no TUI dependence), so the
  increment does not regress headless deploys.

## Decision

Adopt **Option C**. Harvest the bounded detection/checklist/report increment (feature
114-F) into shipment 122-S. **Defer** actual runtime provisioning and every open design
question to operator; 47971057 remains an ACTIVE living tracker for the deferred
provisioning portion (annotated append-only). Blast radius of the increment is
low–moderate (deploy-script/template + docs, detection-only) — P-006 hardening **not
required** for the detection-only increment, but the provisioning phase (when
un-deferred) WILL require hardening.

## Recorded open questions (operator — not decided here)

Authoritative package/download sources; version/channel policy; pinning + checksums +
signature/supply-chain verification; user-local vs system install + elevation; PATH
refresh; offline/proxy/customer-network; graphtor embedding-model provisioning;
rollback/partial-failure semantics; non-interactive/headless/CI provisioning parity;
idempotence; upgrade compatibility; licensing/consent; whether autoharness itself is
bootstrapped before the runtime-provisioning phase while still ensuring pack runtimes
precede merge-install composition.
