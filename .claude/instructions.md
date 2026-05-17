<!-- engram:start -->
## Engram Agent Memory — Claude Code Integration

Engram is running as an MCP server at `http://127.0.0.1:7437/mcp`.

### Available Tools

| Tool | Purpose |
|------|---------|
| `set_workspace` | Register this workspace at session start |
| `query_memory` | Retrieve stored context, tasks, and code knowledge |
| `create_task` | Create a new task in the workspace task list |
| `update_task` | Update task status or details |
| `map_code` | Index code files for semantic navigation |
| `unified_search` | Search across all content types |
| `query_changes` | Query git commit history by file, symbol, or date |

### Recommended Workflow

1. **Session start**: Always call `set_workspace` first to bind this workspace.
2. **Context loading**: Call `query_memory` to retrieve relevant prior context.
3. **Task management**: Track all work items with `create_task` and `update_task`.
4. **Code exploration**: Use `map_code` before navigating unfamiliar modules.
5. **Change awareness**: Use `query_changes` to understand what changed recently.
<!-- engram:end -->