---
title: "Engram .claude/instructions.md stdio-transport correction"
doc_type: decided-plan
status: reviewed
created: 2026-07-29
source_stash_id: "8FD768E9"
prior_work: "036.005-T"
supersedes:
  - docs/archive/plans/2026-07-29-engram-claude-instructions-transport-fix-plan.md
---

# Decided Plan: Engram .claude/instructions.md stdio-transport correction

**Outcome:** Reviewed and marked `READY` as a single-file documentation fix.
The source plan contains inline review approval but no PR or merge evidence, so
this decided-plan preserves the reviewed state rather than claiming shipment.
This replaces the verbose original, archived for traceability at
`docs/archive/plans/2026-07-29-engram-claude-instructions-transport-fix-plan.md`.

## Decision

Replace the stale HTTP endpoint note in `.claude/instructions.md` with a
transport-neutral statement that matches `.mcp.json`: engram is registered as a
stdio MCP server (`command: engram`, `args: ["shim"]`), it should be accessed
through the registered MCP tools, and there is no HTTP endpoint or port to use.
The replacement must also point readers at
`.github/instructions/agent-engram.instructions.md` as the canonical protocol
reference.

## Implementation (single file)

- Update `.claude/instructions.md` only.
- Remove `http://127.0.0.1:7437/mcp` and any other HTTP/port directive for
  engram.
- Keep the replacement transport-neutral and grounded in `.mcp.json` rather than
  inventing a new endpoint.

## Key constraints preserved

- Ground truth was verified before planning: the live agent-facing occurrence was
  `.claude/instructions.md`, while `.mcp.json` already declared stdio transport.
- `.vscode/settings.json` had no engram HTTP reference, and no template generated
  `.claude/instructions.md`, so no wider template or config sweep was needed.
- `.github/instructions/agent-engram.instructions.md` and its template were
  already transport-neutral and intentionally remained untouched.
- Blast radius stays minimal: no schema, CLI, or base-harness behavior changes.

## Rejected alternatives

- **Broader tool-table cleanup in the same file** — rejected because stale
  `create_task` / `update_task` / `query_changes` entries are a separate
  tool-surface-accuracy concern, not part of the transport defect.
- **Edit `.mcp.json` or the agent-engram instructions** — rejected because those
  surfaces were already correct.
- **Run a wider multi-file transport sweep** — rejected because pre-planning
  verification found only one live agent-facing transport claim in scope.

## Review findings that changed the plan

No additional review findings changed the scope after ground-truth verification.
The inline review pass simply confirmed correctness, width isolation,
transport-neutral wording, and the canonical cross-reference, then returned
`READY` with P0 = 0 and P1 = 0.