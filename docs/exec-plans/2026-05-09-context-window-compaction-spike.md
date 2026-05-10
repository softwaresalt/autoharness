# Context Window Compaction Strategy — Spike Findings

**Date**: 2026-05-09
**Shipment**: 022-S
**Status**: complete

---

## Source

`docs/design-docs/context-window-compaction-strategy.md` describes a three-layer
pipeline strategy for keeping context windows lean in long-running agent sessions.

## Layer-by-Layer Assessment

### Layer 1: Tool Result Offloading (Disk I/O)

**Description**: Write tool responses over a threshold (e.g., 2,000 tokens) to
disk. Keep a file path and 10-line preview in context. Agent re-reads from disk
when needed.

**Templateable?** Partially.

| Aspect | Templateable | Environment-dependent |
|---|---|---|
| Instruction to prefer `view_range` over full file reads | ✅ Yes — instruction template | — |
| Instruction to write large tool outputs to docs/scratch/ | ✅ Yes — instruction template | — |
| Automatic tool response truncation | — | ✅ Environment controls this (Copilot CLI, Codex, Claude Code each handle differently) |
| Transparent offloading (harness intercepts tool output) | — | ✅ Requires environment-level hook that autoharness cannot inject |

**What autoharness can do**: Create an instruction template that teaches agents
to proactively offload large results. The instruction would say: "When a tool
response exceeds ~2,000 tokens, write it to `{{DOCS_ROOT}}/scratch/{timestamp}-{summary}.md`
and keep only a file path + 10-line preview in your working context."

**What autoharness cannot do**: Intercept tool responses at the runtime level.
Each environment (Copilot CLI, Codex, Cursor, Claude Code) manages tool response
truncation independently. autoharness templates cannot hook into that pipeline.

**Primitive mapping**: Primitive 1 (State, Context, and Knowledge Retrieval).

### Layer 2: Tool Input Eviction

**Description**: Drop the raw inputs of old "write" commands after changes are
successfully committed. Keep only the knowledge that the file was edited.

**Templateable?** Minimally.

| Aspect | Templateable | Environment-dependent |
|---|---|---|
| Instruction to avoid re-reading files already committed | ✅ Yes — instruction template | — |
| Agent self-awareness of committed vs uncommitted context | ✅ Yes — instruction guidance | — |
| Automatic eviction of old edit diffs from message history | — | ✅ Environment controls message history; autoharness cannot modify past messages |
| Programmatic context window manipulation | — | ✅ No environment exposes an API for this |

**What autoharness can do**: Instruct agents to treat committed changes as
resolved — don't re-read diffs of files already committed and pushed.

**What autoharness cannot do**: Evict messages from the conversation history.
This is entirely environment-controlled. No current environment exposes an API
that allows an agent or instruction to delete or modify past messages.

**Primitive mapping**: Primitive 1 (State, Context, and Knowledge Retrieval).

### Layer 3: Head Summarization & Tail Preservation

**Description**: Triggered at ~85% context capacity. Summarize the "head"
(oldest messages) via a cheaper LLM, preserve the "tail" (recent 10-15%),
archive raw originals to disk.

**Templateable?** Yes — this is the existing `compact-context` skill.

| Aspect | Templateable | Environment-dependent |
|---|---|---|
| Summarize memory/plan/closure artifacts to durable files | ✅ Yes — **already exists** as `compact-context/SKILL.md.tmpl` | — |
| Threshold-based trigger (file count, size) | ✅ Yes — compact-context already has `max_files: 40`, `max_size_kb: 500` | — |
| Archive verbose originals | ✅ Yes — compact-context archives to `docs/archive/` | — |
| Capacity-percentage trigger (85% of context window) | — | ✅ Requires environment to report context usage; no API exists for this |
| Head/tail message summarization (in-conversation) | — | ✅ Requires environment to allow message replacement; autoharness writes to files, not conversation history |

**What autoharness can do**: The compact-context skill already handles the
file-level analog of Layer 3 — it summarizes memory, plans, and closure artifacts
into durable files and archives originals. The gap is that it operates on **files**,
not on the **conversation history** itself.

**What autoharness cannot do**: Summarize and replace messages within the active
conversation. That requires environment support (e.g., Copilot CLI's `/compact`
command or Codex's built-in context management).

**Primitive mapping**: Primitive 1 (State, Context, and Knowledge Retrieval).

## Gap Analysis

### What already exists

| Artifact | Coverage |
|---|---|
| `compact-context/SKILL.md.tmpl` | Layer 3 file-level compaction (memory, plans, closure artifacts) |
| Stage/Ship agent checkpoint triggers | Invoke compact-context at checkpoint threshold (>10) and batch completion |
| `docs/archive/` convention | Verbose originals are preserved, not deleted |

### Gaps identified

| Gap | Layer | Fix | Effort |
|---|---|---|---|
| No instruction template teaching agents to offload large tool results | 1 | New `context-efficiency.instructions.md.tmpl` | Small (1 task) |
| No instruction template teaching agents to treat committed diffs as resolved | 2 | Include in `context-efficiency.instructions.md.tmpl` | Small (same task) |
| compact-context doesn't trigger on context token usage | 3 | Cannot fix — environment must report token usage | N/A |
| No intercom broadcast when compaction runs | 3 | Add to compact-context skill template | Small (1 task) |
| No compaction-trigger instruction that reminds agents to invoke compact-context proactively | 3 | Include in `context-efficiency.instructions.md.tmpl` | Small (same task) |

## Implementation Plan

### Shipment scope: 1 feature, 3 tasks

**Feature**: Context Window Efficiency — instruction template + compact-context enhancements

**Task 1**: Create `templates/instructions/context-efficiency.instructions.md.tmpl`

A new instruction template (Primitive 1) that teaches agents context hygiene:

- **Tool Result Offloading** (Layer 1): When a tool response exceeds ~2,000
  tokens, write it to `{{DOCS_ROOT}}/scratch/` and keep only a path + preview.
  Prefer `view_range` over full file reads. Prefer targeted grep over broad
  searches.
- **Committed Change Eviction** (Layer 2): After committing and pushing, treat
  the diff as resolved. Do not re-read committed file content unless the task
  requires it. Reference the commit SHA, not the full diff.
- **Proactive Compaction Trigger** (Layer 3): When the session has produced
  >10 checkpoint files or >40 memory files, invoke the compact-context skill
  before proceeding. Do not wait for the environment to manage this — the
  agent must invoke compaction explicitly.

Variables: `{{DOCS_ROOT}}` (existing).

**Task 2**: Add intercom broadcasts to `compact-context/SKILL.md.tmpl`

When the `agent-intercom` capability pack is installed:
- Broadcast `[COMPACT] Starting compaction: target={target}` at Phase 1 start
- Broadcast `[COMPACT] Compacted {count} files, recovered {size}` at Phase 4 end

**Task 3**: Register `context-efficiency` in install-harness overlays

Add the instruction to the `instructions` install layer so it's installed for
all presets (starter, standard, full). No capability pack required — this is
universal infrastructure.

### What is NOT in scope (environment-dependent)

- Automatic tool response truncation (environment-controlled)
- Message history eviction (no API exists)
- Token-usage-based compaction trigger (environment must report usage)
- In-conversation head/tail summarization (requires message replacement API)

These are documented as "environment responsibilities" — autoharness cannot
control them but can document which environments support them.

## Recommendation

Ship this as a small follow-up shipment (~3 tasks). The instruction template
provides immediate value by teaching agents context hygiene practices that work
across all environments. The compact-context intercom enhancement is a minor
wiring task. Both are well within the 2-hour rule per task.

The environment-dependent features (Layers 1-2 automatic offloading, Layer 3
in-conversation summarization) should be documented in the instruction template
as "when available, the environment handles this; otherwise, follow these manual
practices."
