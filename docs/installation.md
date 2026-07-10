---
title: Installation
description: The authoritative install path for autoharness — scripted one-command deploy and manual pip/clone/plugin
doc_type: guide
source: docs/installation.md
supersedes:
    - docs/getting-started.md#step-1-install-autoharness-globally
---

> **Navigation**: [README](../README.md) · [Getting Started](getting-started.md) · [Installation](installation.md) · [Environment Setup](environment-setup.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md) · [Tuning Guide](tuning-guide.md) · [Backlog Integration](backlog-integration.md) · [Credits](credits.md)

## Overview

autoharness is installed **once to a global location** and invoked against target
workspaces. The target workspace receives only the generated harness artifacts —
never autoharness engine files, templates, or schemas.

```text
┌──────────────────────────┐       ┌──────────────────────────┐
│  autoharness (global)    │       │  target workspace        │
│  ~/.autoharness/         │       │  ~/projects/my-app/      │
│                          │──────▶│  AGENTS.md               │
│  templates/ schemas/     │ reads │  .github/agents/ ...     │
│  .github/agents/ skills/ │ tmpl, │  .backlog/  .autoharness/│
└──────────────────────────┘ output└──────────────────────────┘
```

There are two supported install paths:

* **Scripted (recommended)** — the `deploy-harness` script collapses the
  install → register → configure → hand-off sequence into one idempotent command.
* **Manual** — run the individual `pip`, `git clone`, or Copilot-plugin steps
  yourself.

Both paths end at the same place: an agent installer (`/install-harness`) that
composes the tailored harness. The scripts never resolve `{{VARIABLE}}` templates
themselves — template composition and adversarial verification are always the
AI agent's job.

## Scripted Install (Recommended)

autoharness ships cross-platform deploy scripts and generates them into a target
workspace on the `full` preset:

* `scripts/deploy-harness.ps1` (PowerShell, Windows/macOS/Linux)
* `scripts/deploy-harness.sh` (POSIX sh, macOS/Linux)

To bootstrap from scratch, obtain the script from the autoharness repository
(`scripts/deploy-harness.ps1` / `scripts/deploy-harness.sh`) or from a workspace
where a `full`-preset harness was already installed, place it at your workspace
root, then run it from the workspace directory.

### What the script does (six phases)

The script runs a deterministic, single-pass sequence (no internal retry loop):

| Phase | Action | Safety |
|---|---|---|
| **preflight** | Verify prerequisites (`python`, `git`; optional `gh` and the target CLI). Fail closed on missing hard prerequisites. | Read-only |
| **bootstrap** | Locate or acquire `autoharness_home` (the **global** install). | Out-of-cwd; gated behind explicit `-Bootstrap`/`--bootstrap` |
| **register** | Register the AI environment (`setup-vscode`, `copilot plugin install`, `setup-claude`, `setup-codex`). | Per-environment config |
| **scaffold** | Write `.autoharness/config.yaml` with the preset and every pack enumerated from the capability-pack registry. | cwd-only; backup-before-overwrite; never clobbers `.env.local` |
| **compose** | **Handoff only** — prints the `/install-harness` command. No template resolution happens here. | cwd-only |
| **verify** | Optional `autoharness verify-workspace`. | cwd-only |

The **scaffold** and **verify** phases write only inside the current workspace.
The **bootstrap** phase installs a global tool outside the workspace **by design**
and is therefore gated behind an explicit `-Bootstrap`/`--bootstrap` opt-in.

### Flags

The PowerShell and shell scripts mirror the same flags and semantics:

| PowerShell | Shell | Default | Purpose |
|---|---|---|---|
| `-Preset` | `--preset` | `full` | Install shape: `starter`, `standard`, `full` |
| `-Packs` | `--packs` | `all` | `all` (resolved from the registry) or a comma-separated subset |
| `-Register` | `--register` | `copilot-cli` | AI environment: `vscode`, `copilot-cli`, `claude`, `codex`, `none` |
| `-InstallMethod` | `--install-method` | `pip` | Global install method: `pip`, `clone`, `plugin` |
| `-Home` | `--home` | *(auto)* | Explicit `autoharness_home` override |
| `-Bootstrap` | `--bootstrap` | off | Opt in to the out-of-cwd **global** install |
| `-DryRun` | `--dry-run` | off | Print the plan without mutating anything |
| `-Force` | `--force` | off | Overwrite an existing `.autoharness/config.yaml` (a timestamped backup is written first) |

### Examples

Preview the full plan without changing anything:

```powershell
./scripts/deploy-harness.ps1 -DryRun
```

```bash
./scripts/deploy-harness.sh --dry-run
```

First-time bootstrap (install the global tool, register Copilot CLI, scaffold a
`full` harness config, then hand off to the agent installer):

```powershell
./scripts/deploy-harness.ps1 -Bootstrap -Preset full -Register copilot-cli -InstallMethod pip
```

```bash
./scripts/deploy-harness.sh --bootstrap --preset full --register copilot-cli --install-method pip
```

The script is idempotent: an existing `autoharness_home` is detected and reused,
an existing `.autoharness/config.yaml` is backed up before overwrite (and only
replaced with `-Force`/`--force`), and an existing `.env.local` is never touched.

After the script finishes, run the `/install-harness` command it prints to let
the agent installer compose and verify the harness.

Exit codes: `0` success, `1` preflight, `2` bootstrap, `3` register, `4` scaffold,
`5` verify.

## Manual Install

### With pip (recommended)

```bash
python -m pip install autoharness
```

This installs `autoharness` as a global CLI tool. Agents resolve the install path
by running `autoharness home`.

If you previously installed from the Git URL or `uv tool`, switch once:

```bash
python -m pip uninstall autoharness   # if installed from a pip Git URL
uv tool uninstall autoharness         # if installed with uv tool
python -m pip install autoharness
```

Use the Git URL only when you need an unreleased snapshot from the repository tip
instead of the stable PyPI release. Update with
`python -m pip install --upgrade autoharness`.

### With git clone (alternative)

```bash
git clone https://github.com/softwaresalt/autoharness.git ~/.autoharness
```

Update with `cd ~/.autoharness && git pull`. Or use a custom location and set the
environment variable:

```bash
git clone https://github.com/softwaresalt/autoharness.git ~/tools/autoharness
export AUTOHARNESS_HOME=~/tools/autoharness            # bash/zsh
$env:AUTOHARNESS_HOME = "$HOME\tools\autoharness"      # PowerShell
```

### With the Copilot CLI plugin

For Copilot CLI users who do not need the Python CLI:

```bash
copilot plugin marketplace add softwaresalt/autoharness
copilot plugin install autoharness@autoharness
```

The plugin path gives Copilot CLI users built-in versioning and update management
with no Python dependency. The Python CLI is still needed for `setup-vscode`,
`verify-workspace`, and registering with Claude Code or Codex.

## Verify the Installation

```bash
autoharness home      # prints the installation path
autoharness version   # prints the version
```

### How agents find autoharness

The `autoharness_home` path is resolved in this order:

1. `AUTOHARNESS_HOME` environment variable
2. Output of `autoharness home` (if on PATH)
3. Directory traversal from the agent definition file
4. `~/.autoharness/` default

## After Installing

1. **Configure your workspace (optional)** — create `.autoharness/config.yaml`
   to persist preset, packs, and preferences. See
   [Getting Started → Configure Your Workspace](getting-started.md#step-2-configure-your-workspace-optional).
2. **Register your AI environment** — VS Code, Copilot CLI, Claude Code, Codex,
   or Cursor. See [Environment Setup](environment-setup.md). The scripted path's
   `register` phase performs this automatically.
3. **Compose a harness** — run the agent installer against your workspace:

   ```text
   /install-harness preset=standard
   ```

   See [Getting Started → Install a Harness](getting-started.md#step-3-install-a-harness-into-a-target-workspace)
   for the full walkthrough, selective installation, and dry-run options.

## Next Steps

* **[Getting Started](getting-started.md)** — Full walkthrough, workspace configuration, and post-install verification
* **[Environment Setup](environment-setup.md)** — Per-environment registration
* **[Capability Packs](capability-packs.md)** — Overlay pattern and pack catalog
* **[Tuning Guide](tuning-guide.md)** — Maintain and adapt your harness as the codebase evolves
