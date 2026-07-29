---
title: Engram .claude/instructions.md stdio-transport correction
doc_type: plan
status: reviewed
created: 2026-07-29
source_stash_id: 8FD768E9
prior_work: 036.005-T
---

# Plan: Correct stale engram HTTP-endpoint note in `.claude/instructions.md`

## Problem

`.claude/instructions.md:4` states `Engram is running as an MCP server at
http://127.0.0.1:7437/mcp`. This is stale and wrong: `.mcp.json` registers engram
as a **stdio** MCP server (`type: stdio`, `command: engram`, `args: ["shim"]`).
The HTTP endpoint / port directive misleads agents into assuming a network
transport that does not exist. Prior task `036.005-T` (archived) flagged this exact
`http://127.0.0.1:7437/mcp` string as stale and corrected the parallel block in
`.github/copilot-instructions.md`, but the editor-local `.claude/instructions.md`
mirror was never updated.

## Ground-truth verification (done before planning)

- `grep 127.0.0.1:7437` / `grep 7437`: the only live occurrence in the owned tree
  is `.claude/instructions.md:4`. Other hits are the stash entry itself and the
  archived `036.005-T.md` reference — neither is agent-facing config.
- `.mcp.json`: engram is `type: stdio`, `command: engram`, `args: ["shim"]`.
- Editor-local mirrors: only `.claude/instructions.md` and `.vscode/settings.json`
  exist (no `.cursor`). `.vscode/settings.json` has no engram HTTP/port reference.
- No `.tmpl` template generates `.claude/instructions.md` (grep for
  `Engram is running` / `Claude Code Integration` / `7437` across `**/*.tmpl`
  returned nothing). The file is hand-authored, not template-generated.
- `.github/instructions/agent-engram.instructions.md` and its
  `templates/instructions/agent-engram.instructions.md.tmpl` are already
  transport-neutral (daemon / MCP-surface language, no port / http / endpoint) —
  no change needed there. This confirms the stash's "keep transport-neutral"
  expectation is already satisfied for those files.

## Scope (width-isolated, single concern)

Single editor-local documentation file: `.claude/instructions.md`. No schema, no
CLI, no template, no base-harness change. Blast radius is minimal → P-006 plan
hardening NOT required.

## Fix

Replace the stale HTTP-endpoint sentence on line 4 with a transport-neutral note
that reflects the stdio registration in `.mcp.json` and removes any port/HTTP
access directive. Cross-reference the canonical protocol instruction. Suggested
replacement (implementer may refine wording, must preserve intent):

> Engram is registered as a stdio MCP server in `.mcp.json` (command
> `engram shim`); access it through the registered Engram MCP tools. There is no
> HTTP endpoint or port. Full protocol:
> `.github/instructions/agent-engram.instructions.md`.

## Out of scope (residual risk — NOT this shipment)

The same block still lists `create_task` / `update_task` / `query_changes` in its
tool table — drift already corrected for `copilot-instructions.md` by `036.005-T`
but not mirrored here. This is a separate concern (tool-surface accuracy, not
transport) and is intentionally excluded to keep this fix width-isolated to the
stash's transport defect. Flag for a follow-up stash entry.

## Acceptance criteria

1. `.claude/instructions.md` no longer contains `http://127.0.0.1:7437/mcp` or any
   HTTP/port access directive for engram.
2. The replacement text reflects the stdio transport per `.mcp.json` and is
   transport-neutral (no invented port).
3. Cross-reference to `.github/instructions/agent-engram.instructions.md` present.
4. No other files modified; `grep 7437` across the owned tree returns no live
   agent-facing config hit (stash/archive historical references excluded).

## Plan review (multi-persona, inline — small doc fix)

- **Correctness reviewer**: replacement matches `.mcp.json` reality; no residual
  port. PASS.
- **Scope / width-isolation reviewer**: single file, single concern; tool-table
  drift correctly deferred. PASS.
- **Evidence-integrity reviewer**: ground truth verified by grep before planning;
  no stale assumptions carried from the (partially stale) stash text. PASS.
- **Cross-reference reviewer**: referenced instruction file and `.mcp.json` exist.
  PASS.

Outcome: **READY** — P0=0, P1=0.
