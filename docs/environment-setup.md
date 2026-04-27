---
title: Environment Setup
description: Register autoharness with your AI coding environment — VS Code, Copilot CLI, Claude Code, Codex, or Cursor
---

> **Navigation**: [README](../README.md) · [Getting Started](getting-started.md) · [Environment Setup](environment-setup.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md) · [Tuning Guide](tuning-guide.md) · [Backlog Integration](backlog-integration.md) · [Credits](credits.md)

## Overview

autoharness is environment-agnostic. Register it once in whichever environment(s) you use. This page covers per-environment setup; see [Getting Started](getting-started.md) for global installation and harness composition.

## VS Code with GitHub Copilot

The Auto-MergeInstall agent writes the agent and prompt discovery settings to your **VS Code user settings** (`%APPDATA%\Code\User\settings.json` on Windows; `~/Library/Application Support/Code/User/settings.json` on macOS; `~/.config/Code/User/settings.json` on Linux). These are user-scoped settings so the Auto-MergeInstall agent is available from every workspace, not just the one it was installed into.

After the first-time setup described below, entries like these will be present in your user settings without any manual editing:

```jsonc
// VS Code user settings — written automatically by autoharness install
// The exact path is the output of: autoharness home
{
  "chat.agentFilesLocations":  { "C:\\Users\\you\\AppData\\Roaming\\uv\\tools\\autoharness\\Lib\\site-packages\\autoharness\\data\\.github\\agents":  true },
  "chat.agentSkillsLocations": { "C:\\Users\\you\\AppData\\Roaming\\uv\\tools\\autoharness\\Lib\\site-packages\\autoharness\\data\\.github\\skills":  true },
  "chat.promptFilesLocations": { "C:\\Users\\you\\AppData\\Roaming\\uv\\tools\\autoharness\\Lib\\site-packages\\autoharness\\data\\.github\\prompts": true }
}
```

The installer resolves the path by running `autoharness home` — tilde shorthand (`~`) is not expanded in VS Code JSON settings on Windows and is never used. Existing settings are preserved; only the autoharness-specific entries are added.

Once those settings are in place, the **Auto-MergeInstall** agent appears in the **agents dropdown** at the top of the Chat view. Select it there before typing your prompt. The `/install-harness` slash command (from the autoharness prompt file) is also available in chat.

> **First-time setup:** Run this command once after installing autoharness (cwd does not matter):
>
> ```bash
> autoharness setup-vscode
> ```
>
> This writes the three `chat.*` entries into your VS Code user settings using the fully-resolved path from `autoharness home`. Then reload the VS Code window (`Ctrl+Shift+P` → **Reload Window**) and the **Auto-MergeInstall** agent will appear in the agents dropdown. Re-run `autoharness setup-vscode` only if the resolved `autoharness home` path changes after a reinstall or environment move.

## GitHub Copilot CLI — Plugin Install (Recommended)

The fastest way to get autoharness agents into Copilot CLI is the **plugin system**:

```bash
copilot plugin marketplace add softwaresalt/autoharness
copilot plugin install autoharness@autoharness
```

This installs the Auto-MergeInstall and Auto-Tune agents plus all skills in a single command — no Python required. Updates are equally simple:

```bash
copilot plugin update autoharness
```

The plugin is discovered from the repository-root `plugin.json` manifest.

## GitHub Copilot CLI — VS Code Background Sessions

VS Code integrates with the Copilot CLI as **background agent sessions** that run autonomously while you continue other work. VS Code installs and configures the Copilot CLI agent runtime automatically.

For the **Auto-MergeInstall** and **Auto-Tune** agents to appear in Copilot CLI sessions, install the plugin (see above) or run this legacy command once after installing the Python package:

```bash
autoharness setup-copilot-cli
```

> **Deprecation notice:** `setup-copilot-cli` is superseded by registering the autoharness marketplace and installing `autoharness@autoharness`. The plugin provides the same agents and skills with built-in versioning and no Python dependency. The CLI command will be removed in a future release.
> Direct `owner/repo` plugin installs currently work, but Copilot CLI warns that they are deprecated in favor of marketplace-based installs.

This copies the agent `.md` files and skill `SKILL.md` files from the autoharness installation into your Copilot CLI global config directory (`~/.copilot/agents/` and `~/.copilot/skills/`). This is the standard registration path for external workspaces; autoharness does not install these global agents into the target workspace. Re-run it after upgrading autoharness to pick up updated files.

To run the Auto-MergeInstall agent as a background session:

1. Open the Chat view (`Ctrl+Alt+I`)
2. Select **Copilot CLI** from the **Session Target** dropdown (or run **Chat: New Copilot CLI** from the Command Palette)
3. Optionally select **Auto-MergeInstall** from the **Agents** dropdown in the session (requires `github.copilot.chat.cli.customAgents.enabled` — experimental)
4. Type your install request in the session:

```text
Install a standard harness into this workspace
```

## GitHub Copilot CLI — Terminal

VS Code registers a **GitHub Copilot CLI** terminal profile. To open a session:

- Select the **+** dropdown in the Terminal panel and choose **GitHub Copilot CLI**, or
- Run **Terminal: Create New Terminal (With Profile)** from the Command Palette and select **GitHub Copilot CLI**, or
- Type `copilot` in any VS Code integrated terminal

VS Code handles authentication automatically. Once the session is open, type `/install-harness` to run the install prompt, or describe the task naturally.

For standalone Copilot CLI sessions outside VS Code, run `autoharness setup-copilot-cli` first so agents and skills are registered globally, then use the generated `start.ps1` (or `start.sh`) at the workspace root to set workspace-local state before launching. The startup scripts do not copy or refresh agent files.

> **First install (before `start.ps1` exists):** The startup scripts are generated *by* the installer, so they do not exist yet. Use the VS Code terminal approach above — VS Code handles auth. The `start.ps1` / `start.sh` scripts are for subsequent sessions outside VS Code.

## Claude Code

Run once after installing autoharness:

```bash
autoharness setup-claude
```

This copies agent `.md` files into `~/.claude/agents/` and skill `SKILL.md` files into `~/.claude/skills/`. Claude Code discovers agents and skills from those directories at startup. The `CLAUDE_CONFIG_DIR` environment variable overrides the default `~/.claude/` path. Restart Claude Code after running, and again after upgrading autoharness.

## Codex

Run once after installing autoharness:

```bash
autoharness setup-codex
```

This copies skill `SKILL.md` files into `~/.codex/skills/`. Codex uses a unified skills model — the `install-harness` and `tune-harness` skills serve as the agent entry points. The `CODEX_HOME` environment variable overrides the default `~/.codex/` path. Restart Codex after running, and again after upgrading autoharness.

## Cursor

Add autoharness as an agent source in Cursor settings.

## Startup Scripts

The Auto-MergeInstall agent generates `start.ps1` (PowerShell) and `start.sh` (bash) at your workspace root. These scripts set workspace-local directories for AI agent state before launching your AI CLI tool:

```powershell
# start.ps1 — generated by autoharness
$env:COPILOT_HOME = ".\.copilot"   # workspace-local Copilot database and memories
$env:GITHUB_TOKEN = (gh auth token)
& "copilot"                        # or the full path configured in .autoharness/config.yaml
```

```bash
# start.sh — generated by autoharness
export COPILOT_HOME="./.copilot"
export GITHUB_TOKEN="$(gh auth token)"
"copilot"
```

By redirecting `COPILOT_HOME` (and optionally `ENGRAM_DATA_DIR` for agent-engram) to a workspace-local directory, the agent's memories, checkpoints, and database are stored inside the project and become visible to git. This keeps agent state isolated per project rather than shared across all workspaces.

The startup scripts are runtime launchers only. They do not install `Auto-MergeInstall` or `Auto-Tune` into the workspace. For Copilot CLI, refresh those global agent and skill files with `autoharness setup-copilot-cli` after each autoharness upgrade. For VS Code, the user-settings registration normally survives upgrades and only needs to be rerun if the resolved install path changes.

Sections for Claude Code and OpenAI Codex are included in each script as commented-out blocks; activate the one you need.

To configure the Copilot CLI path (when it is not on PATH), set it in `.autoharness/config.yaml` before running install or tune:

```yaml
ai_tools:
  copilot_cli:
    exe_path: "C:\\Tools\\ghcpcli\\copilot.exe"   # Windows example
    # exe_path: "/usr/local/bin/copilot"           # macOS/Linux example
```

## Next Steps

- **[Getting Started](getting-started.md)** — Install autoharness and compose a harness
- **[Tuning Guide](tuning-guide.md)** — Maintain and adapt your harness over time
