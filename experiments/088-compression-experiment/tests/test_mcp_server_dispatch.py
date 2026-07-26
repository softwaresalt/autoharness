"""Tests for the minimal MCP-compatible retrieval server dispatch (088.003-T).

Tests the pure dispatch function directly (no stdio transport) so the tool
contract is verified without spinning a real MCP client/server pair.
"""

import pytest

from brainspace.mcp_server import dispatch_tool_call
from brainspace.store import BrainspaceStore


@pytest.fixture
def store(tmp_path):
    s = BrainspaceStore(str(tmp_path))
    yield s
    s.close()


def test_output_retrieve_full_mode_returns_original(store):
    original = "hello world\n" * 50
    handle = store.put(original)
    result = dispatch_tool_call(store, "output_retrieve", {"handle": handle})
    assert result["isError"] is False
    assert result["content"] == [{"type": "text", "text": original}]
    assert result["_meta"]["has_more"] is False


def test_output_retrieve_paginated_mode(store):
    original = "".join(f"row-{i}\n" for i in range(2000))
    handle = store.put(original)
    result = dispatch_tool_call(
        store, "output_retrieve", {"handle": handle, "offset": 0, "limit": 100}
    )
    assert result["isError"] is False
    assert result["content"] == [{"type": "text", "text": original[:100]}]
    assert result["_meta"]["has_more"] is True
    assert result["_meta"]["offset"] == 0
    assert result["_meta"]["total_length"] == len(original)


def test_output_retrieve_unknown_handle_reports_error_not_exception(store):
    result = dispatch_tool_call(store, "output_retrieve", {"handle": "nope"})
    assert result["isError"] is True
    assert result["content"][0]["type"] == "text"
    assert "not found" in result["content"][0]["text"]


def test_output_retrieve_invalid_limit_reports_error_not_exception(store):
    original = "hello world\n" * 50
    handle = store.put(original)
    result = dispatch_tool_call(
        store, "output_retrieve", {"handle": handle, "offset": 0, "limit": 0}
    )
    assert result["isError"] is True


def test_unknown_tool_name_reports_error(store):
    result = dispatch_tool_call(store, "not_a_real_tool", {})
    assert result["isError"] is True
    assert result["content"][0]["type"] == "text"


def test_list_tools_returns_output_retrieve_schema():
    from brainspace.mcp_server import list_tools

    tools = list_tools()
    names = [t["name"] for t in tools]
    assert "output_retrieve" in names


def test_handle_request_initialize_is_mcp_conformant(store):
    from brainspace.mcp_server import handle_request

    request = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
    response = handle_request(request, store)
    result = response["result"]
    # MCP 2024-11-05 InitializeResult requires protocolVersion, capabilities,
    # and serverInfo -- protocolVersion alone is not a conformant response.
    assert result["protocolVersion"] == "2024-11-05"
    assert "capabilities" in result and isinstance(result["capabilities"], dict)
    assert "serverInfo" in result
    assert "name" in result["serverInfo"]
    assert "version" in result["serverInfo"]


def test_handle_request_tools_call_returns_call_tool_result_shape(store):
    from brainspace.mcp_server import handle_request

    original = "hello world\n" * 50
    handle = store.put(original)
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "output_retrieve", "arguments": {"handle": handle}},
    }
    response = handle_request(request, store)
    result = response["result"]
    assert result["isError"] is False
    assert isinstance(result["content"], list)
    assert result["content"][0]["type"] == "text"
    assert result["content"][0]["text"] == original


def test_handle_request_tools_list_returns_tools(store):
    from brainspace.mcp_server import handle_request

    request = {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
    response = handle_request(request, store)
    names = [t["name"] for t in response["result"]["tools"]]
    assert "output_retrieve" in names


def test_handle_request_unknown_method_reports_json_rpc_error(store):
    from brainspace.mcp_server import handle_request

    request = {"jsonrpc": "2.0", "id": 4, "method": "does/not/exist"}
    response = handle_request(request, store)
    assert response["error"]["code"] == -32601
