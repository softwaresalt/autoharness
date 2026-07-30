<!-- engram:start -->
## Engram Agent Memory — Claude Code Integration

Engram is registered as a stdio MCP server in `.mcp.json` (command `engram shim`); access it through the registered Engram MCP tools. There is no HTTP endpoint or port. Full protocol: `.github/instructions/agent-engram.instructions.md`.

### Available Tools

| Tool | Purpose |
|------|---------|
| `get_daemon_status` | Confirm the Engram daemon / MCP surface is reachable (lifecycle check) |
| `get_workspace_status` | Verify workspace binding and index freshness (required binding verification) |
| `set_workspace` | Bind this workspace at session start (when explicit binding is required) |
| `query_memory` | Retrieve stored context, notes, and content records |
| `unified_search` | Broad semantic search across code, docs, and history |
| `list_symbols` | List symbols in a file or matching a concept |
| `map_code` | Explore callers, callees, and local graph context |
| `impact_analysis` | Assess blast radius before modifying a symbol |
| `query_graph` | Run advanced read-only graph queries |
| `sync_workspace` | Incremental index refresh when the workspace is stale |
| `index_workspace` | Full index rebuild when needed |
| `flush_state` | Flush pending index state when the workspace uses it |

### Recommended Workflow

1. **Session start**: confirm the daemon / MCP surface is reachable with
   `get_daemon_status`, verify binding and index freshness with
   `get_workspace_status`, and call `set_workspace` only if explicit binding is
   required.
2. **Context loading**: call `query_memory` / `unified_search` to retrieve relevant
   prior context.
3. **Code exploration**: use `list_symbols`, `map_code`, and `impact_analysis` when
   navigating unfamiliar modules or assessing blast radius.
4. **Freshness**: run `sync_workspace` (or `index_workspace` for a full rebuild)
   when the index is stale, and use `flush_state` when the workspace requires a
   pending-state flush.
<!-- engram:end -->