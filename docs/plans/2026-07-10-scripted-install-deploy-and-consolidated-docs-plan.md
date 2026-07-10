---
title: "Scripted Install/Deploy Automation + Consolidated Installation Guide — Implementation Plan"
description: "Impl-plan, plan-hardening (P-006), and plan-review verdict for the capability-pack registry (schema + data), the cross-platform deploy-harness script templates, the autoharness dogfood deploy instances, the install-harness/discovery wiring, and the consolidated installation guide."
doc_type: plan
source: docs/plans/2026-07-10-scripted-install-deploy-and-consolidated-docs-plan.md
decision_doc: docs/decisions/2026-07-10-scripted-install-deploy-and-consolidated-docs-deliberation.md
source_stash_ids:
  - "EF1EFEE1"
  - "711D390E"
  - "C359DE16"
requires_plan_hardening: "yes"
plan_review_verdict: "approved"
tags:
  - "installation"
  - "scripted-install"
  - "capability-pack-registry"
  - "cross-platform"
  - "docs-consolidation"
  - "dogfood-parity"
---

# Scripted Install/Deploy Automation + Consolidated Installation Guide — Implementation Plan

See `docs/decisions/2026-07-10-scripted-install-deploy-and-consolidated-docs-deliberation.md`
for the design rationale. This plan decomposes the feature into six width-isolated,
≤2h, ≤~3-file tasks and enumerates risks (P-006).

## Task decomposition & dependency graph

```text
T1 (capability-pack registry schema)          ── foundational, no deps
  └── T2 (capability-pack registry data)       depends on T1
        └── T3 (cross-platform deploy-harness script templates)   depends on T2
              ├── T4 (autoharness dogfood deploy-harness instances)  depends on T3
              ├── T5 (install-harness + workspace-discovery wiring)   depends on T3
              └── T6 (consolidated installation guide + doc supersede) depends on T3
```

T1 and T2 formalize the enumerable registry (the prerequisite that makes "all packs"
concrete). T3 is the script family that consumes it. T4/T5/T6 are independent
consumers of the script design (dogfood instance, install wiring, docs) and can be
built in parallel after T3.

### T1 — Capability-pack registry schema

* **Scope**: Create `schemas/capability-pack-registry.schema.json` (JSON Schema
  draft-07, matching the style of the sibling schemas). Define a `packs[]` array;
  each entry: `id` (string, enum-aligned with the nine current pack names),
  `title`, `purpose`, `primitive_impact` (array of integers 1-10),
  `eligibility_signals` (array of strings), `overlay_instruction` (string — template
  path, may be empty for agent-only packs like `adversarial-review`),
  `mcp_requirements` (array of strings, may be empty), `default_in_preset` (array
  constrained to `starter`/`standard`/`full`). Include `schema_version` +
  `$id`/`$schema` header consistent with `schemas/harness-config.schema.json`.
* **Files (≤1)**: `schemas/capability-pack-registry.schema.json`.
* **Verify**: valid JSON; `python -c "import json; json.load(open(...))"` parses;
  schema is self-consistent (draft-07 metaschema) and `id` enum matches the pack
  names used in `harness-config.schema.json`.

### T2 — Capability-pack registry data

* **Scope**: Create `templates/packs/capability-pack-registry.yaml` enumerating the
  nine current packs (`agent-intercom`, `agent-engram`, `backlogit`,
  `browser-verification`, `continuous-learning`, `strict-safety`,
  `release-observability`, `adversarial-review`, `graphtor-docs`) with metadata
  sourced from `docs/capability-packs.md:128-140` (purpose + primitive impact),
  the per-pack overlay sections (eligibility signals), and
  `install-harness/SKILL.md` Step 1.3 (overlay instruction paths + preset defaults).
  Plain `.yaml` (no `{{VARIABLE}}`), per the `backlogit.registry.yaml` precedent.
* **Files (≤1)**: `templates/packs/capability-pack-registry.yaml`.
* **Verify**: parses as YAML; validates against the T1 schema (`autoharness`
  jsonschema is already a locked dep — validate with a one-off
  `jsonschema.validate`); pack `id` set exactly equals the nine names in
  `docs/capability-packs.md:128-140`; each `overlay_instruction` path exists under
  `templates/instructions/` (or is empty for `adversarial-review`).

### T3 — Cross-platform deploy-harness script templates

* **Scope**: Create `templates/scripts/deploy-harness.ps1.tmpl` and
  `templates/scripts/deploy-harness.sh.tmpl`. Each implements the six phases from
  decision D2 (preflight → bootstrap → register → scaffold → compose-handoff →
  verify) with flags: `-Preset`/`--preset` (default `full`),
  `-Packs`/`--packs` (default `all`, resolved from the registry),
  `-Register`/`--register` (`vscode`|`copilot-cli`|`claude`|`codex`|`none`),
  `-InstallMethod`/`--install-method` (`pip`|`clone`|`plugin`),
  `-Home`/`--home`, `-Bootstrap`/`--bootstrap` (explicit opt-in for the
  out-of-cwd global install — D6), `-DryRun`/`--dry-run`, `-Force`/`--force`.
  Reads `templates/packs/capability-pack-registry.yaml` to enumerate "all packs".
  Idempotent, backup-before-overwrite for `.autoharness/config.yaml`, never clobbers
  `.env.local`, workspace-contained scaffold/verify, single deterministic pass per
  phase (no retry loop). Loader/env-var-precedence parity with `start.ps1`/`start.sh`.
  Handoff phase prints the exact `/install-harness preset=<preset>` command and does
  NOT resolve templates. `{{VARIABLE}}` swap points only for genuine per-workspace
  values (e.g. `{{WORKSPACE_ROOT}}`, `{{PROJECT_NAME}}`, `{{AUTOHARNESS_HOME_DEFAULT}}`,
  `{{DEFAULT_PRESET}}`, `{{PACK_REGISTRY_PATH}}`).
* **Files (≤2)**: `templates/scripts/deploy-harness.ps1.tmpl`,
  `templates/scripts/deploy-harness.sh.tmpl`.
* **Verify**: PowerShell parses (`pwsh -NoProfile -Command "..."` AST parse of the
  resolved script); `bash -n` on the resolved sh script; `-DryRun` performs no
  mutations; all `{{VAR}}` are covered by the T5 variable table; exit-code semantics
  documented in a header comment.

### T4 — autoharness dogfood deploy-harness instances

* **Scope**: Create rendered `scripts/deploy-harness.ps1` and `scripts/deploy-harness.sh`
  in the autoharness repo, mirroring the T3 template design resolved against the
  autoharness repo's own profile (PowerShell/pip method, Copilot-CLI registration,
  full-preset with all nine packs). Consistent with the existing
  `start.ps1`/`start.sh` and pre-commit-hook dogfood parity. Set execute permission
  on the `.sh` (`chmod +x`).
* **Files (≤2)**: `scripts/deploy-harness.ps1`, `scripts/deploy-harness.sh`.
* **Verify**: both parse (pwsh AST parse / `bash -n`); `-DryRun` prints the phase
  plan without mutating; the rendered instance contains **no** unresolved `{{VAR}}`;
  design matches the T3 template (parity diff).

### T5 — install-harness + workspace-discovery wiring

* **Scope**: Wire the new artifacts into the install flow. Add the deploy-harness
  scripts to `install-harness/SKILL.md` Step 2.9 (Startup Scripts) and the Step 3.2
  directory mapping so a `full`-preset install can optionally emit
  `{workspace}/scripts/deploy-harness.{ps1,sh}`. Add every new `{{VARIABLE}}` from T3
  to the install-harness variable resolution table (the single variable registry).
  Add a workspace-discovery note so the profile can record the operator's AI
  environment(s) for the `register` phase default. Reference the pack registry
  (`templates/packs/capability-pack-registry.yaml`) as the pack enumeration source.
* **Files (≤3)**: `.github/skills/install-harness/SKILL.md`,
  `.github/skills/workspace-discovery/SKILL.md`,
  `templates/scripts/.env.local.tmpl` (only if a new env var is needed; otherwise the
  third slot is unused).
* **Verify**: every T3 `{{VAR}}` appears in the variable table; no `{{...}}` remains
  after resolution against ≥3 profiles (Python/pip, TypeScript/npm, Rust/cargo);
  markdownlint clean.

### T6 — Consolidated installation guide + doc supersede

* **Scope**: Create `docs/installation.md` as the single authoritative install path
  (scripted one-command path + manual pip/clone/plugin path), with accurate
  copy-pasteable steps. Trim `README.md`'s install section to a pointer; move the
  install mechanics out of `docs/getting-started.md` Step 1-2 (leave the post-install
  narrative + a link); cross-link `docs/environment-setup.md` (do not duplicate).
  Add `Installation` to the navigation bars across the affected `docs/*.md`. Use
  frontmatter `supersedes` where content genuinely moves.
* **Files (≤3 doc files; navigation-bar edits across docs count as the doc set)**:
  `docs/installation.md` (new), `README.md`, `docs/getting-started.md` (+ light
  nav-bar touch on `docs/environment-setup.md`/`docs/capability-packs.md` as part of
  the same doc concern).
* **Verify**: markdownlint clean (MD001/MD025/MD041); all cross-references resolve
  (no dead links); every command in the guide matches the real CLI/script behavior
  (no aspirational steps — the script exists via T3/T4); nav bars consistent.

## Plan Hardening (P-006)

This plan has **elevated blast radius** (a new schema, a new registry that other
tooling will depend on, cross-platform scripts that install a **global** tool and
mutate config, and a docs reorganization that supersedes multiple existing pages),
so hardening is required. Enumerated risks and mitigations:

| # | Risk | Likelihood | Blast radius | Mitigation (owned by task) |
|---|------|-----------|--------------|----------------------------|
| R1 | **Overwrite / data loss** — script clobbers an existing `.autoharness/config.yaml` or `.env.local`, destroying operator settings/secrets | Med | Lost config/secrets | T3/T4: backup-before-overwrite for `config.yaml` (timestamped copy); never write `.env.local` if present (mirror install-harness Step 2.9); `-DryRun` shows the plan; `-Force` required to overwrite. Verified by a dry-run + re-run idempotency check. |
| R2 | **Workspace-containment violation** — the scaffold/verify phase writes outside cwd, or the global bootstrap writes out-of-cwd silently | Med | Constitution III-V breach | T3: scaffold/verify write only inside cwd; the out-of-cwd global install is gated behind an explicit `-Bootstrap`/`--bootstrap` opt-in or interactive confirmation (D6); document the boundary in the header comment. |
| R3 | **Registry drift** — the new `capability-pack-registry.yaml` diverges from the schema enums / `docs/capability-packs.md` pack table over time | Med | "All packs" silently wrong | T2: pack `id` set asserted equal to `docs/capability-packs.md:128-140` and the `harness-config.schema.json` enum at author time; a registry-vs-enums drift check is recorded as an explicit tuning follow-up (not built here — see decision D3 bounded scope). |
| R4 | **Cross-platform breakage** — `.ps1` works, `.sh` fails (or vice versa); flag parsing diverges between the two | Med | Broken install on one OS | T3/T4: parse-check both (pwsh AST parse + `bash -n`); keep flag names/semantics mirrored (D4); dogfood both instances; single deterministic pass so neither can spin. |
| R5 | **autoharness_home resolution edge cases** — script mis-detects an existing install, double-installs, or picks the wrong home (env vs CLI vs default) | Med | Duplicate/stale install | T3: bootstrap uses the documented resolution order (`AUTOHARNESS_HOME` → `autoharness home` → default) and confirms via `autoharness version`; idempotent detect-then-skip; `-Home` overrides explicitly. |
| R6 | **Docs go stale vs scripts** — the consolidated guide documents steps the script doesn't actually perform (aspirational docs) | Med | Inaccurate "accurate docs" | T6 depends on T3/T4 so it documents the **shipped** behavior; verification requires every command in the guide to match real CLI/script behavior; no step documented that isn't implemented. |
| R7 | **Scripted/agent boundary blur** — the script tries to resolve templates or "install the harness" itself, duplicating (and drifting from) the agent installer | Med | Divergent install logic | T3: the compose phase is **handoff-only** (prints the agent command); the script never resolves `{{VARIABLE}}` templates (D2). Verified by grepping the script for template-resolution logic (must be absent). |
| R8 | **Partial-install / failure recovery** — a mid-run failure (missing MCP prereq, network) leaves a corrupt half-state | Low | Blocked re-install | T3: each phase independently re-runnable and status-reporting; preflight fails closed before any mutation; re-run resumes cleanly (D6). |
| R9 | **Schema/registry adoption over-reach** — refactoring all existing enum/prose consumers to read the registry balloons scope | Med | Shipment blowout | T1/T2: registry is **additive**; existing enums stay the validation authority; consumer refactor is explicitly out of scope (D3). Only the deploy script + guide consume the registry now. |
| R10 | **Doc supersede breakage** — moving install content breaks inbound links / nav bars across `docs/*` | Low | Broken navigation | T6: update all nav bars in one pass; cross-reference sweep must pass (no dead links); use `supersedes` frontmatter for provenance. |

**Hardening conclusion**: risks are bounded and each is owned by a specific task with
a concrete verification. R1/R2 (data-loss + containment) are the highest-severity and
are mitigated by backup + dry-run + explicit opt-in for the only intentional
out-of-cwd write. No risk requires operator input to *plan*; the two operator-visible
concerns (the global-install cross-boundary write and the "renaming/refactoring enum
consumers is a follow-up" boundary) are explicitly documented rather than silently
handled.

## Plan Review

* **Granularity (2-hour rule)**: all six tasks ≤~3 files, single concern each. PASS.
* **Width isolation**: schema (T1) / registry data (T2) / script templates (T3) /
  dogfood instances (T4) / install wiring (T5) / docs (T6) are cleanly separated —
  no task mixes schema work with script work with docs work. PASS.
* **Dependency integrity (P-003)**: T2→T1; T3→T2; T4→T3; T5→T3; T6→T3. Acyclic,
  single covering feature parent. PASS.
* **Dogfood parity**: T4 explicitly mirrors the T3 template design (start.ps1/.sh
  precedent). PASS.
* **Boundary discipline**: script is handoff-only for composition; agent retains
  discovery + composition + adversarial verification (D2/R7). PASS.
* **Registry scope discipline**: registry is additive; consumer refactor deferred
  (D3/R9), keeping the shipment sane. PASS.
* **Cross-platform**: `.ps1` + `.sh` pair per 069-F precedent (D4/R4). PASS.
* **Docs accuracy**: T6 depends on the shipped script so steps are real, not
  aspirational (R6). PASS.
* **Verdict**: **APPROVED** for harvest.
