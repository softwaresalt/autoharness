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
from brainspace.workspace import resolve_workspace_root  # noqa: E402

_PROTOCOL_VERSION = "2024-11-05"
_SERVER_NAME = "brainspace-ccr"
_SERVER_VERSION = "0.1.0"


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


def _text_result(text: str, *, is_error: bool, meta: dict = None) -> dict:
    """Build a conformant MCP ``CallToolResult``.

    Per the MCP 2024-11-05 spec, ``content`` is an array of typed content
    blocks and tool failures are signalled via ``isError``, not a bespoke
    top-level ``error`` key. Pagination metadata (offset/total_length/
    has_more) has no dedicated field in the spec's result shape, so it is
    carried in the generic ``_meta`` extension point that ``Result``
    objects support.
    """
    result = {"content": [{"type": "text", "text": text}], "isError": is_error}
    if meta is not None:
        result["_meta"] = meta
    return result


def dispatch_tool_call(store, tool_name: str, arguments: dict) -> dict:
    """Dispatch a single tool call against the given store instance."""
    if tool_name != "output_retrieve":
        return _text_result(f"unknown tool: {tool_name}", is_error=True)

    handle = arguments.get("handle")
    offset = arguments.get("offset", 0)
    limit = arguments.get("limit", 65536)
    try:
        page = retrieve_chunk(store, handle, offset=offset, limit=limit)
    except (RetrievalError, ValueError) as exc:
        return _text_result(str(exc), is_error=True)

    meta = {
        "offset": page["offset"],
        "total_length": page["total_length"],
        "has_more": page["has_more"],
    }
    return _text_result(page["chunk"], is_error=False, meta=meta)


def handle_request(request: dict, store) -> dict:
    """Handle one JSON-RPC request against ``store``. Pure, testable core.

    ``main()`` is the thin stdio transport wrapper around this function --
    keeping the dispatch logic here (not inline in the stdin read loop)
    lets ``initialize``/``tools/call`` conformance be verified directly,
    without spinning a real stdio client/server pair.
    """
    method = request.get("method")
    req_id = request.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": _PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": _SERVER_NAME, "version": _SERVER_VERSION},
            },
        }
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": list_tools()},
        }
    if method == "tools/call":
        params = request.get("params", {})
        result = dispatch_tool_call(
            store, params.get("name", ""), params.get("arguments", {})
        )
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"unknown method: {method}"},
    }


def main() -> int:  # pragma: no cover -- thin stdio transport wrapper
    from brainspace.store import BrainspaceStore

    workspace_root = resolve_workspace_root(None)
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

            response = handle_request(request, store)
            print(json.dumps(response), flush=True)
    finally:
        store.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
