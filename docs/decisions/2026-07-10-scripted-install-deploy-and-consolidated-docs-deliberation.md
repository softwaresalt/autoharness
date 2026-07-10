---
title: "Scripted Install/Deploy Automation + Consolidated Installation Guide"
description: "Deliberated design for a cross-platform (PowerShell + Bash) scripted bootstrap-and-deploy path that installs autoharness and enables all capability packs in a new development environment or workspace, a machine-readable capability-pack registry that makes 'all packs' enumerable, and a single authoritative installation guide that supersedes the scattered install/setup docs."
topic: "How should autoharness offer a deterministic, scripted install-and-deploy path (autoharness + all capability packs) alongside the existing AI-agent-driven install, where is the scripted/agent boundary, does a capability-pack registry exist, and how should the poor, scattered install docs be consolidated?"
depth: "hardened"
decision_status: "accepted"
doc_type: decision
source: docs/decisions/2026-07-10-scripted-install-deploy-and-consolidated-docs-deliberation.md
source_stash_ids:
  - "EF1EFEE1"
  - "711D390E"
  - "C359DE16"
linked_artifacts:
  - "src/autoharness/cli.py"
  - ".github/skills/install-harness/SKILL.md"
  - ".github/skills/workspace-discovery/SKILL.md"
  - ".github/agents/auto-mergeinstall.agent.md"
  - "templates/scripts/start.ps1.tmpl"
  - "templates/scripts/start.sh.tmpl"
  - "templates/scripts/.env.local.tmpl"
  - "templates/scripts/pre-push-quality-gates.ps1.tmpl"
  - "docs/getting-started.md"
  - "docs/environment-setup.md"
  - "docs/capability-packs.md"
  - "schemas/harness-config.schema.json"
tags:
  - "installation"
  - "scripted-install"
  - "capability-pack-registry"
  - "cross-platform"
  - "powershell"
  - "docs-consolidation"
  - "idempotency"
  - "workspace-containment"
  - "dogfood-parity"
---

# Scripted Install/Deploy Automation + Consolidated Installation Guide

## Problem

Three related stash entries describe one coherent capability with heavy overlap:

* **`EF1EFEE1`** (feature) — "Create PowerShell script to automate installation of
  autoharness and all capability packs into a new development environment."
* **`711D390E`** (feature) — "Add PowerShell scripts for scripted deployment of
  autoharness and all capability packs in the registry into a new workspace."
  This is a **near-duplicate** of `EF1EFEE1` (bootstrap the tool + deploy all packs);
  the only nuance is "environment" (EF1EFEE1) vs "workspace" (711D390E), which are the
  two phases of one flow.
* **`C359DE16`** (feature) — "Documentation for install and setup is poor; needs a
  consolidated installation path and accurate docs."

`EF1EFEE1` and `711D390E` are the **scripted install-and-deploy tool**; `C359DE16`
is the **consolidated installation guide** that documents it (and the manual path)
accurately. All three are consumed into **one feature**. None deferred.

## Discovery: the actual install architecture today

autoharness installs in three distinct movements today, each documented in a
different place, which is precisely the "scattered / poor docs" pain of `C359DE16`:

1. **Acquire the global tool** (`autoharness_home`) — one of three methods
   (`docs/getting-started.md` Step 1): `pip install autoharness`, `git clone`, or
   `copilot plugin` marketplace. Resolution order is
   `AUTOHARNESS_HOME` env → `autoharness home` CLI → agent-dir traversal →
   `~/.autoharness/` (getting-started lines 80-87).
2. **Register with the AI environment** (`docs/environment-setup.md`) — deterministic
   Python CLI commands already exist: `autoharness setup-vscode`,
   `setup-copilot-cli` (deprecated), `setup-claude`, `setup-codex`
   (`src/autoharness/cli.py:46-49, 1411-1430`), plus `copilot plugin install
   autoharness@autoharness`.
3. **Compose a harness into a target workspace** — **AI-agent-driven**: the
   `auto-mergeinstall` agent runs `workspace-discovery` (profile detection) +
   `install-harness` (template composition, variable resolution, Phase-4 adversarial
   verification). Capability-pack selection happens here via preset defaults and
   profile recommendations (`install-harness/SKILL.md` Step 1.3, lines 505-583).

Two supporting facts from discovery drive the design:

* **A deterministic verifier already exists**: `autoharness verify-workspace`
  (`cli.py:40, 121-132`) produces JSON + Markdown compatibility reports. The scripted
  path reuses it rather than reinventing verification.
* **No machine-readable capability-pack registry exists.** Pack knowledge is
  scattered across prose (`docs/capability-packs.md` lists nine packs at lines
  128-140), overlay instruction templates (`templates/instructions/*.instructions.md.tmpl`),
  and **closed enums** in three schemas (`harness-config.schema.json`,
  `harness-manifest.schema.json`, `workspace-profile.schema.json`) plus two prose
  selection tables in the skills. There is **no single enumerable file** that lists
  "all capability packs" with metadata. So `711D390E`'s phrase "all capability packs
  **in the registry**" refers to a registry that must first be **formalized**.

The nine current packs (`docs/capability-packs.md:128-140`): `agent-intercom`,
`agent-engram`, `backlogit`, `browser-verification`, `continuous-learning`,
`strict-safety`, `release-observability`, `adversarial-review`, `graphtor-docs`.

## Decision

Deliver a **scripted install/deploy path** as a cross-platform tool pair plus the
enabling registry and a consolidated guide, composed of four artifact families:

1. **Machine-readable capability-pack registry** — a new schema
   (`schemas/capability-pack-registry.schema.json`) and an enumerable data file
   (`templates/packs/capability-pack-registry.yaml`) listing every pack with
   metadata (id, title, eligibility signals, overlay instruction template, MCP
   requirements, default-in-preset). This makes "all packs" enumerable for the
   script and the docs and gives the framework one authoritative pack catalog.
2. **Cross-platform scripted deploy tool** — `deploy-harness.ps1.tmpl` +
   `deploy-harness.sh.tmpl` under `templates/scripts/`, that deterministically runs
   preflight → bootstrap → register → scaffold → verify → handoff (see D2), reading
   the pack registry to enable all packs. Idempotent, backup-before-overwrite,
   workspace-contained.
3. **autoharness dogfood instances** — rendered `scripts/deploy-harness.ps1` +
   `scripts/deploy-harness.sh` demonstrating the script against a real profile,
   mirroring the existing `start.ps1` / `start.sh` and pre-commit-hook dogfood parity.
4. **Consolidated installation guide** — a single authoritative `docs/installation.md`
   that is THE install path (scripted + manual), superseding/redirecting the scattered
   install content in `README.md`, `docs/getting-started.md`, and
   `docs/environment-setup.md`, with accurate, tested steps.

### D1 — Scope consolidation: one feature, three stashes consumed

`EF1EFEE1` + `711D390E` = the scripted tool (families 1-3). `C359DE16` = the
consolidated guide (family 4). One covering feature. The near-duplicate pair is
merged into a single script with two phases (bootstrap the tool into a new
environment; deploy/prepare a workspace with all packs), not two scripts.

### D2 — The scripted/agent boundary (the central decision)

The scripted path **must not** replace the AI-agent-driven harness composition.
Profile discovery, `{{VARIABLE}}` resolution across dozens of templates, overlay
weaving, and Phase-4 adversarial verification are **reasoning tasks** — they are the
product. A deterministic script cannot do them well, and pretending otherwise would
violate Core Rule 4 ("Discovery before generation") and Core Rule 5 ("Verify after
installation" via multi-model adversarial review).

What a script **can** deterministically automate is the scattered manual bootstrap
sequence that surrounds the agent step. The boundary is drawn crisply as six phases:

| Phase | Script (deterministic) | Agent (reasoning) |
|---|---|---|
| **preflight** | Verify prerequisites: Python/pip, `git`, `gh`, the target AI CLI (`copilot`/`claude`/`codex`), and pack MCP prereqs (backlogit, engram, graphtor bin). Emit a readiness report; fail closed on missing hard prereqs. | — |
| **bootstrap** | Acquire/locate `autoharness_home` (pip install, `git clone`, or plugin), then confirm via `autoharness home` / `autoharness version`. | — |
| **register** | Run the existing `autoharness setup-*` command(s) / `copilot plugin install` for the detected environment(s). | — |
| **scaffold** | Read the pack registry; write `.autoharness/config.yaml` with `preset: full` + `capability_packs: [<all>]` (or an operator-chosen subset). Backup any existing config first. | — |
| **compose** | **Hand off** — print/echo the exact next command (`/install-harness preset=full` via the `auto-mergeinstall` agent). The script does NOT resolve templates. | Discover profile → compose templates → resolve variables → write artifacts. |
| **verify** | Optionally run `autoharness verify-workspace` for a deterministic post-install compatibility report. | Phase-4 adversarial multi-model verification. |

**Boundary statement**: *script = deterministic bootstrap + environment registration +
pack enumeration + config scaffolding + prerequisite/verify + handoff. Agent = workspace
discovery + template composition + adversarial verification.* The script's job is to
collapse the scattered "install tool → register environment → configure packs → run
installer" dance into one idempotent, documented command, and to make "all packs"
concrete by seeding a full-preset config from the registry.

### D3 — Capability-pack registry must be formalized (prerequisite, bounded)

Because no enumerable registry exists (Discovery), "all capability packs in the
registry" is not resolvable today. We formalize a **single machine-readable catalog**:

* **Schema**: `schemas/capability-pack-registry.schema.json` — defines a `packs[]`
  array; each entry has `id` (enum-aligned with the existing pack names),
  `title`, `purpose`, `primitive_impact` (array of ints), `eligibility_signals`
  (array), `overlay_instruction` (template path), `mcp_requirements` (array; may be
  empty), and `default_in_preset` (array of `starter`/`standard`/`full`).
* **Data**: `templates/packs/capability-pack-registry.yaml` — enumerates the nine
  current packs sourced from `docs/capability-packs.md:128-140` and
  `install-harness/SKILL.md` Step 1.3. It is a **fixed enumeration with no
  `{{VARIABLE}}` customization points**, so it is a plain `.yaml`, not a `.tmpl` —
  following the precedent of the non-parameterized
  `templates/backlog/registries/backlogit.registry.yaml`.

**Bounded scope**: this feature *authors* the registry and makes the **deploy script
and the consolidated guide** consume it. It does **not** refactor the existing schema
enums or the two skill prose tables to read from the registry — that broader
"single-source-of-truth consolidation" is a valuable but separate follow-up and would
balloon this shipment. The registry is additive; the existing enums remain the
validation authority. A drift check (registry vs schema enums vs docs pack table) is
noted as a tuning follow-up, not built here.

### D4 — Cross-platform: ship PowerShell AND Bash (069-F precedent)

The operator asked for PowerShell, but Core Rule 3 (environment-agnostic) and the
just-shipped **069-F precedent** (which shipped `pre-push-quality-gates.ps1.tmpl` +
`.sh.tmpl` as a pair, and `start.ps1`/`start.sh` already exist as dogfood pairs)
settle this: deliver **both** `deploy-harness.ps1.tmpl` and `deploy-harness.sh.tmpl`.
PowerShell-only would be an environment-specific regression. The scripts keep loader
parity with `start.ps1`/`start.sh` conventions (env-var precedence, `.env.local`
loading style, non-fatal warnings for optional tools).

### D5 — Docs consolidation: one authoritative guide, supersede the scattered pieces

Create **`docs/installation.md`** as the single authoritative installation path,
covering: (a) the one-command scripted path (recommended), and (b) the manual path
(pip/clone/plugin → `setup-*` → agent install) for operators who want control. The
guide has **accurate, tested** steps (each command copy-pasteable and verified).

Supersede/redirect the scattered content:

* `docs/getting-started.md` Step 1-2 (global install + config) → its install
  mechanics move into `docs/installation.md`; getting-started keeps the
  post-install "install a harness / verify" narrative and links to the new guide.
* `docs/environment-setup.md` → remains the per-environment registration reference,
  cross-linked from the consolidated guide (not duplicated).
* `README.md` install section → trimmed to a pointer at `docs/installation.md`.
* Navigation bars across `docs/*.md` → add `Installation` and keep links consistent.

Use frontmatter `supersedes` where content genuinely moves, and cross-links where it
is referenced. The consolidated guide documents the scripted path **only after** the
script exists (dependency), so its steps are real, not aspirational.

### D6 — Idempotency, safety, and workspace containment (mandatory)

The deploy script MUST:

* **Be idempotent** — re-runnable without harm; detect an already-present
  `autoharness_home` / existing registration and skip or refresh rather than
  duplicate. Uses `autoharness home` / `autoharness version` to detect prior installs.
* **Back up before overwrite** — before writing `.autoharness/config.yaml`, if one
  exists, copy it to a timestamped backup (Core Rule 6: preserve existing work). Never
  clobber an existing `.env.local` (mirrors `install-harness` Step 2.9 secrets rule).
* **Respect workspace containment** — the **scaffold/verify** phases write only inside
  the target workspace cwd (Constitution Principles III-V). The **bootstrap** phase
  installs the global tool *outside* cwd **by design** (that is what installing a
  global tool means); this cross-boundary write is made **explicit and opt-in**
  (a `-Bootstrap` / `--bootstrap` flag or an interactive confirmation) so it is never
  a silent out-of-cwd mutation. `-DryRun` prints the plan without mutating anything.
* **Support partial-install recovery** — each phase is independently re-runnable and
  reports its own status; a failure in one phase (e.g., MCP prereq missing) does not
  corrupt earlier phases, and re-running resumes cleanly. Single deterministic pass
  per phase (no internal retry loop — circuit-breaker compatible, per 069-F/D5 hook
  precedent).

## Architecture framing: install-flow tooling, not a capability pack

The scripted deploy path is **install-flow orchestration tooling**, not a capability
pack. It does not redefine the primitive model or add an optional overlay woven
through six artifact classes; it is a deterministic convenience wrapper over the
existing install movements. It touches Primitive 4 (orchestration/handoff — it
sequences bootstrap→register→scaffold→handoff and hands off to the agent installer)
and Primitive 5 (guardrails — idempotency, backup, containment). It is therefore
modeled as first-class install tooling + docs, not forced through the overlay
contract.

## What this fixes

* **EF1EFEE1 / 711D390E**: one idempotent, cross-platform command bootstraps
  autoharness and seeds a full-preset config that enables **every** pack in the newly
  formalized registry, then hands off to the agent installer — replacing a scattered
  manual multi-step sequence.
* **C359DE16**: one authoritative, accurate `docs/installation.md` replaces the
  scattered, partially-inaccurate install content and gives operators a single
  consolidated path.

## Consolidation outcome

All three stashes consumed into one feature. None deferred. Decomposed into six
width-isolated tasks (see the plan doc). Estimated ~12h total (6 × ~2h).
