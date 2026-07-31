---
type: session-memory
agent: Ship
date: 2026-07-01
session: backlog-to-shipped — record autoharness version on install (autonomous)
shipment: 054-S
tags: [install, versioning, drift-detection, ship, closure, autonomous]
---

# Ship Session — Record autoharness Version on Install (054-F)

## Summary

Shipped shipment **054-S** (feature **054-F**, task **054.001-T**): the harness
install now records the real autoharness version so harness-doctor can detect
version drift. Merged via PR
[#119](https://github.com/softwaresalt/autoharness/pull/119) as merge commit
`5ab29eb8fde830653dabefa7fe158d4aa76e5740`.

## Root cause + fix

The install-harness Step 3.3 manifest example hard-coded
`autoharness_version: "1.0.0"`, so installs never recorded the actual version —
defeating harness-doctor's Phase-2 drift check (the schema already required the
field and harness-doctor already read/compared it). Fixed:

- Manifest records `autoharness_version: "{{AUTOHARNESS_VERSION}}"`.
- `{{AUTOHARNESS_VERSION}}` resolution is install-mode-agnostic (CLI → package
  metadata → plugin manifest) and must be concrete.
- install-harness Step 4.1 now fails the install if the manifest keeps a literal
  placeholder.
- harness-doctor Phase 2 resolves the *current* version live via `autoharness
  version`; on failure it WARNs (no false PASS) instead of comparing install-time
  vs install-time.

## Review

Four cross-model adversarial passes (Claude Sonnet 4.6 + GPT-5.4). No P0. Each
round found progressively deeper issues (resolution source, baked-vs-live,
false-PASS, plugin topology, manifest placeholder gate) — all addressed within
the 3-cycle fix limit; the remaining mechanical enforcement is stashed as
follow-up **B2F96A58**. Tests: 126 passed.

## Closure

`backlogit shipment ship 054-S --sha 5ab29eb…` → shipped/archived (054-F +
054.001-T + 054-S). No release obligations.

## Autonomous session context

Cycle 2 of the autonomous overnight run (after 052-F). Remaining: 053-F (remove
model_routing — needs deliberation; conflicts with shipped P-013) and 051-F
(Phase 2 Telemetry & Evaluation Engine).

## Learning

A "one-line fix" masked a real feature: when a field is schema-required and a
consumer already compares it, the actual bug can be that the *producer* writes a
constant. Trace producer→field→consumer end-to-end before sizing. Cross-model
adversarial review was essential here — it surfaced install-topology and
false-PASS gaps a single reviewer missed.
