---
source: docs/plans/2026-07-10-scripted-install-deploy-and-consolidated-docs-decided-plan.md
title: "Scripted Install/Deploy Automation + Consolidated Installation Guide"
doc_type: decided-plan
status: reviewed
created: 2026-07-10
source_stash_ids:
  - "EF1EFEE1"
  - "711D390E"
  - "C359DE16"
supersedes:
  - docs/archive/plans/2026-07-10-scripted-install-deploy-and-consolidated-docs-plan.md
---

# Decided Plan: Scripted Install/Deploy Automation + Consolidated Installation Guide

**Outcome:** Reviewed and approved for harvest with P-006 hardening. The source
plan defines the registry, script, install-wiring, and documentation work in six
tasks but includes no PR or merge evidence, so this decided-plan records the
reviewed state rather than shipped status. This decided-plan replaces the verbose
original, archived for traceability at
`docs/archive/plans/2026-07-10-scripted-install-deploy-and-consolidated-docs-plan.md`.

## Problem (settled)

Make "all capability packs" concrete, add cross-platform deploy-harness
automation, wire it into install/discovery, and consolidate installation
documentation without letting the script take over discovery/composition or risk
silently overwriting operator state.

## Decisions

1. **Introduce an additive capability-pack registry.** A new schema plus
   `templates/packs/capability-pack-registry.yaml` become the explicit
   enumeration source for the nine current packs, while the existing
   harness-config enums remain the validation authority.
2. **Make deploy-harness phase-based, idempotent, and handoff-only.** The
   PowerShell and shell templates implement preflight, bootstrap, register,
   scaffold, compose-handoff, and verify; they may bootstrap and scaffold, but
   they do not resolve templates or replace the agent installer.
3. **Require explicit authority for the global bootstrap boundary.** The only
   intentional out-of-cwd write is the global install/bootstrap path, and it
   must be gated behind `-Bootstrap` / `--bootstrap` rather than happening
   silently.
4. **Ship dogfood instances that mirror the template design.** The autoharness
   repo gets rendered `scripts/deploy-harness.ps1` and `.sh` instances resolved
   for its own profile so dogfood usage stays aligned with the templates.
5. **Consolidate installation docs only after the scripts exist.**
   `docs/installation.md` becomes the single authoritative installation guide,
   with README/getting-started/environment-setup adjusted to point to it rather
   than duplicate mechanics.

## Implementation (6 tasks)

- **T1 — Capability-pack registry schema:** add
  `schemas/capability-pack-registry.schema.json` with the pack metadata contract
  (`id`, title, purpose, primitive impact, eligibility signals, overlay
  instruction, MCP requirements, preset defaults).
- **T2 — Capability-pack registry data:** add
  `templates/packs/capability-pack-registry.yaml` enumerating the nine current
  packs and validating against T1.
- **T3 — Cross-platform deploy-harness script templates:** add
  `templates/scripts/deploy-harness.ps1.tmpl` and `.sh.tmpl` with mirrored
  flags, dry-run support, backup-before-overwrite for
  `.autoharness/config.yaml`, `.env.local` preservation, and a compose phase
  that prints the exact `/install-harness preset=<preset>` handoff command.
- **T4 — autoharness dogfood deploy-harness instances:** add resolved
  `scripts/deploy-harness.ps1` and `.sh` instances for the repo's own profile
  and verify parseability, dry-run behavior, and zero unresolved variables.
- **T5 — install-harness + workspace-discovery wiring:** add the deploy scripts
  to install-harness output mapping and startup-scripts guidance, record every
  new variable in the install-harness table, and let workspace discovery record
  the operator AI environment for register-phase defaults.
- **T6 — Consolidated installation guide:** add `docs/installation.md`, trim the
  duplicated install mechanics out of `README.md` and `docs/getting-started.md`,
  cross-link `docs/environment-setup.md`, and update navigation bars across the
  affected docs.

## Key constraints preserved

- Registry data is plain YAML with no `{{VARIABLE}}`; drift is bounded by schema
  validation and an explicit equality check against the known pack ID set.
- The script never clobbers `.env.local`, and overwriting
  `.autoharness/config.yaml` requires backup and explicit force semantics.
- Workspace scaffold/verify stays inside the workspace; only the deliberate
  bootstrap/install path crosses the workspace boundary, and only with explicit
  opt-in.
- PowerShell and shell variants must expose mirrored flags and parse cleanly on
  both platforms.
- Script phases are re-runnable and deterministic; no retry loop or hidden
  recovery flow.
- Documentation may describe only shipped behavior: T6 depends on T3/T4 so the
  guide cannot get ahead of the actual script and CLI behavior.
- The registry rollout is additive: deploy-harness and the guide consume it now;
  broad consumer refactors are deferred.

## Rejected alternatives

- **Let deploy-harness resolve templates itself** — rejected because discovery,
  composition, and verification remain agent responsibilities; the script is a
  handoff surface, not a second installer.
- **Silently perform the global bootstrap/install path** — rejected because the
  only out-of-cwd mutation must be explicit and operator-legible.
- **Refactor every existing pack consumer to read the new registry now** —
  rejected as scope blowout; the registry is introduced additively first.
- **Ship a one-platform script** — rejected; the design must mirror
  `start.ps1` / `start.sh` and stay cross-platform.
- **Write consolidated installation docs before the script behavior exists** —
  rejected because the guide must match real commands, not aspirational steps.

## Post-review refinements folded in

The approval pass kept the six-task graph intact but locked in three boundaries:
the registry stays additive rather than triggering a broad consumer refactor,
the compose phase stays handoff-only so agent installation logic does not drift
into scripts, and the consolidated guide lands only after the script behavior is
real enough to document exactly.