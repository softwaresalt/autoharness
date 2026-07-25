#!/usr/bin/env python3
"""Minimal stdio JSON-RPC MCP-compatible retrieval server (088.003-T).

A dependency-free implementation of just enough of the MCP stdio protocol
(``initialize``, ``tools/list``, ``tools/call``) to register the throwaway
``output_retrieve`` tool via ``.mcp.json``. This is a prototype, not a
production MCP SDK integration -- ``dispatch_tool_call`` / ``list_tools`` are
the units under test; the ``main()`` stdio loop is a thin, largely untested
transport wrapper.
"""

import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_EXPERIMENT_ROOT = os.path.dirname(_THIS_DIR)
if _EXPERIMENT_ROOT not in sys.path:
    sys.path.insert(0, _EXPERIMENT_ROOT)

from brainspace.retrieval import RetrievalError, retrieve_chunk  # noqa: E402


def list_tools():
    """Return the MCP tool schema for ``output_retrieve``."""
    return [
        {
            "name": "output_retrieve",
            "description": (
                "Retrieve the byte-equivalent original tool output for a "
                "088-F brainspace compression handle. Returns the full "
                "content, or a page of it plus has_more when offset/limit "
                "are supplied -- never silently truncated."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "handle": {"type": "string"},
                    "offset": {"type": "integer", "default": 0},
                    "limit": {"type": "integer", "default": 65536},
                },
                "required": ["handle"],
            },
        }
    ]


def dispatch_tool_call(store, tool_name: str, arguments: dict) -> dict:
    """Dispatch a single tool call against the given store instance."""
    if tool_name != "output_retrieve":
        return {"error": f"unknown tool: {tool_name}"}

    handle = arguments.get("handle")
    offset = arguments.get("offset", 0)
    limit = arguments.get("limit", 65536)
    try:
        page = retrieve_chunk(store, handle, offset=offset, limit=limit)
    except RetrievalError as exc:
        return {"error": str(exc)}

    return {
        "content": page["chunk"],
        "offset": page["offset"],
        "total_length": page["total_length"],
        "has_more": page["has_more"],
    }


def main() -> int:  # pragma: no cover -- thin stdio transport wrapper
    from brainspace.store import BrainspaceStore

    workspace_root = os.environ.get("BRAINSPACE_WORKSPACE") or os.getcwd()
    store = BrainspaceStore(workspace_root)
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue

            method = request.get("method")
            req_id = request.get("id")
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"protocolVersion": "2024-11-05"},
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": list_tools()},
                }
            elif method == "tools/call":
                params = request.get("params", {})
                result = dispatch_tool_call(
                    store, params.get("name", ""), params.get("arguments", {})
                )
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"unknown method: {method}"},
                }

            print(json.dumps(response), flush=True)
    finally:
        store.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
