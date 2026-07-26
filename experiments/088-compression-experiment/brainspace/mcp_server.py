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

from brainspace.retrieval import RetrievalError, retrieve_chunk, retrieve_full  # noqa: E402
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
    # Only branch into paginated mode when the caller actually supplied
    # pagination arguments. A handle-only call (exactly as the emitted
    # footer instructs) must return the COMPLETE original regardless of
    # length -- falling through to retrieve_chunk's 65,536-char schema
    # default would silently truncate longer originals to a prefix.
    paginated = "offset" in arguments or "limit" in arguments
    try:
        if paginated:
            offset = arguments.get("offset", 0)
            limit = arguments.get("limit", 65536)
            page = retrieve_chunk(store, handle, offset=offset, limit=limit)
            text = page["chunk"]
            meta = {
                "offset": page["offset"],
                "total_length": page["total_length"],
                "has_more": page["has_more"],
            }
        else:
            text = retrieve_full(store, handle)
            meta = {"offset": 0, "total_length": len(text), "has_more": False}
    except (RetrievalError, ValueError) as exc:
        return _text_result(str(exc), is_error=True)

    return _text_result(text, is_error=False, meta=meta)


def handle_request(request, store):
    """Handle one JSON-RPC request against ``store``. Pure, testable core.

    ``main()`` is the thin stdio transport wrapper around this function --
    keeping the dispatch logic here (not inline in the stdin read loop)
    lets ``initialize``/``tools/call`` conformance be verified directly,
    without spinning a real stdio client/server pair.

    Returns ``None`` for JSON-RPC *notifications* (no ``"id"`` field, e.g.
    the client's post-initialize ``notifications/initialized``) -- per
    JSON-RPC 2.0 / MCP, notifications MUST receive no response at all
    (P-018 re-review finding #2, new round): a method-not-found response
    with ``id: null`` is not a valid reply to a notification.

    ``request`` is untyped (not annotated ``dict``) because a syntactically
    valid JSON payload is not guaranteed to decode to an *object* -- a bare
    list, string, number, or ``null`` all parse successfully but are not a
    JSON-RPC Request. Calling ``.get()`` on those crashes with
    ``AttributeError`` (P-018 final-convergence finding #2), which would
    take down this long-lived stdio server on a single malformed line. Per
    JSON-RPC 2.0 §5.1, a non-object request is reported as ``-32600``
    Invalid Request with ``id: null`` (the id cannot be recovered from a
    non-object payload), and the server MUST keep serving afterward.
    """
    if not isinstance(request, dict):
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request"},
        }
    method = request.get("method")
    is_notification = "id" not in request
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
    if is_notification:
        # Unrecognized notification (e.g. a future notifications/* method):
        # still no response, per JSON-RPC 2.0 semantics.
        return None
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"unknown method: {method}"},
    }


def handle_line(line: str, store):
    """Parse one raw stdio line as JSON and dispatch it via
    :func:`handle_request`. Returns a response dict, or ``None`` if no
    reply should be sent (a notification, per JSON-RPC 2.0 semantics).

    This is the pure, testable seam between the stdio transport loop and
    request handling (P-018 final-convergence finding #2): a line that
    fails to parse as JSON at all is a ``-32700`` Parse error (JSON-RPC 2.0
    §4.2); a line that parses but is not a JSON object falls through to
    ``handle_request``'s own ``-32600`` Invalid Request check. Either way
    this function -- and therefore the long-lived stdio server calling it
    -- must never raise for a malformed line and must keep serving
    afterward.
    """
    try:
        request = json.loads(line)
    except json.JSONDecodeError:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Parse error"},
        }
    return handle_request(request, store)


def main() -> int:  # pragma: no cover -- thin stdio transport wrapper
    from brainspace.store import BrainspaceStore

    workspace_root = resolve_workspace_root(None)
    store = BrainspaceStore(workspace_root)
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            response = handle_line(line, store)
            if response is not None:
                # Notifications (handle_line/handle_request returned None)
                # must receive no reply at all -- per JSON-RPC 2.0 / MCP
                # semantics.
                print(json.dumps(response), flush=True)
    finally:
        store.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
