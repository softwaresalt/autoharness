---
title: autoharness
description: Globally-installed agent harness framework that generates AI coding assistant primitives into any target workspace
---

# autoharness

A globally-installed agent harness framework that composes AI coding assistant primitives into any repository workspace. Discover your workspace's technology stack, then generate a customized set of agents, instructions, skills, prompts, policies, and constitutional foundations — all tailored to your codebase.

Install once globally. Invoke against any workspace. The target receives only finished harness artifacts, never engine files.

## The Problem

Modern AI coding assistants (GitHub Copilot, Claude Code, Cursor, Codex) work dramatically better with structured guidance: agent definitions, skill workflows, coding instructions, review personas, and workflow policies. Building these from scratch for every repo is tedious. Maintaining them as the codebase evolves is worse.

## How It Works

```text
 Discover              Install               Tune
 ───────── ──────▶ ─────────── ──────▶ ─────────
 Scan workspace        Compose tailored       Adapt harness as
 profile: languages,   harness from the       the codebase,
 frameworks, build     10 universal           docs, and team
 tools, CI/CD          primitive templates    conventions evolve
```

```text
┌──────────────────────────┐       ┌──────────────────────────┐
│  autoharness (global)    │       │  target workspace        │
│                          │       │                          │
│  templates/              │──────▶│  AGENTS.md               │
│  schemas/                │ reads │  .github/agents/         │
│  agents/                 │ tmpl, │  .github/skills/         │
│  skills/                 │ writes│  .github/instructions/   │
│  docs/                   │ output│  .github/policies/       │
│                          │       │  .backlog/               │
│                          │       │  .autoharness/           │
└──────────────────────────┘       └──────────────────────────┘
```

## The 10 Primitives

Every effective agent harness implements these irreducible primitives ([deep reference](docs/primitives.md)):

| # | Primitive | Purpose |
|---|-----------|---------|
| 1 | **State, Context & Knowledge Retrieval** | Durable memory, checkpoints, retrieval, compaction |
| 2 | **Task Granularity & Horizon Scoping** | Decompose work to prevent error compounding |
| 3 | **Model Routing & Escalation** | Match model capability to task complexity |
| 4 | **Orchestration, Delegation & Lifecycle Handoffs** | Sequence agents through a feature/chore lifecycle |
| 5 | **Tool Execution, Safety Modes & Guardrails** | Safe environment mutation with policy enforcement |
| 6 | **Injection Points & Dynamic Reminders** | Surface constraints exactly when needed |
| 7 | **Observability & Evaluation** | Track agent efficacy, output quality, and entropy |
| 8 | **Workflow Policy** | Cross-agent sequencing and gate enforcement |
| 9 | **Repository Knowledge & Agent Legibility** | Structure the repo as a navigable knowledge base |
| 10 | **Operational Closure & Feedback** | Verify runtime behavior and close the delivery loop |

## Presets & Capability Packs

Start light and grow. Presets control the installation shape; capability packs overlay deeper behavior on top.

| Preset | Scope | Best For |
|---|---|---|
| **starter** | Core planning, execution, guardrails, repo knowledge | First adoption, smaller repos |
| **standard** | Full 10-primitive harness | Most application and service repositories |
| **full** | Full harness plus recommended capability packs | Teams wanting deeper verification |

| Pack | Purpose |
|---|---|
| **agent-intercom** | Operator visibility, heartbeat, approval routing |
| **agent-engram** | Indexed search, code graph lookup, workspace binding |
| **backlogit** | backlogit-native query, queue, dependencies, memory/checkpoints, and traceability |
| **browser-verification** | Browser-aware runtime verification for web UIs |
| **continuous-learning** | Observation capture, instinct formation, learned artifacts |
| **strict-safety** | Explicit ProposedAction / ActionRisk / ActionResult tracking |
| **release-observability** | Richer operational closure and monitoring |
| **adversarial-review** | Multi-model consensus review and escalation |

See [Capability Packs](docs/capability-packs.md) for the full overlay contract and pack details.

## Quick Start

```bash
# Option A: Copilot CLI plugin (recommended — no Python needed)
copilot plugin marketplace add softwaresalt/autoharness
copilot plugin install autoharness@autoharness

# Option B: Python CLI (for setup-vscode and verify-workspace)
uv tool install git+https://github.com/softwaresalt/autoharness.git
autoharness setup-vscode        # VS Code with GitHub Copilot

# Register with other AI environments (requires Python CLI)
autoharness setup-claude        # Claude Code
autoharness setup-codex         # Codex

# Install a harness (from the target workspace)
/install-harness preset=standard

# Run deterministic verification against an installed workspace
autoharness verify-workspace --workspace .
```

If the target workspace is Git-backed, treat install and tune output as
feature-branch work. autoharness may still generate local uncommitted changes
while you are on the default branch, but the intended review path is feature
branch plus pull request, not a direct commit or push to the default branch.

The marketplace-based plugin install path gives Copilot CLI users built-in versioning and update management with no Python dependency. The Python CLI is still needed for `setup-vscode` (writing VS Code user settings), `verify-workspace` (CI-friendly JSON Schema validation), and registering with Claude Code or Codex.

The `setup-claude` and `setup-codex` commands copy agent or skill files into each tool's standard global config directory, so rerun them after upgrading autoharness to refresh those files. `setup-vscode` writes user-settings pointers to `autoharness home`; rerun it only if that resolved install path changes.

See [Getting Started](docs/getting-started.md) for the full walkthrough, including workspace configuration, install layers, selective installation, and post-install verification.

## Documentation

| Document | Description |
|---|---|
| [Getting Started](docs/getting-started.md) | Install autoharness, configure your workspace, compose a harness |
| [Environment Setup](docs/environment-setup.md) | Per-environment registration (VS Code, Copilot CLI, Claude Code, Codex, Cursor) |
| [Primitives](docs/primitives.md) | Deep reference for the 10 irreducible harness primitives |
| [Capability Packs](docs/capability-packs.md) | Overlay pattern, pack catalog, and composition rules |
| [Tuning Guide](docs/tuning-guide.md) | Maintain and adapt your harness as the codebase evolves, including checksum drift and schema-contract upgrades |
| [Backlog Integration](docs/backlog-integration.md) | Backlog tool detection, registry abstraction, and manual registration |
| [Credits](docs/credits.md) | Sources of inspiration, research, and tools that shaped autoharness |

## Acknowledgements

autoharness builds on [METR Time Horizons research](docs/credits.md), [OpenAI harness engineering](docs/credits.md), [Anthropic Constitutional AI](docs/credits.md), [atv-starterkit](https://github.com/microsoft/atv-starterkit), [backlogit](https://github.com/softwaresalt/backlogit), and established software engineering practice. See [Credits](docs/credits.md) for the full breakdown.

## License

MIT
