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
    assert result["content"] == original
    assert result.get("has_more") is False


def test_output_retrieve_paginated_mode(store):
    original = "".join(f"row-{i}\n" for i in range(2000))
    handle = store.put(original)
    result = dispatch_tool_call(
        store, "output_retrieve", {"handle": handle, "offset": 0, "limit": 100}
    )
    assert result["content"] == original[:100]
    assert result["has_more"] is True


def test_output_retrieve_unknown_handle_reports_error_not_exception(store):
    result = dispatch_tool_call(store, "output_retrieve", {"handle": "nope"})
    assert result.get("error") is not None


def test_unknown_tool_name_reports_error(store):
    result = dispatch_tool_call(store, "not_a_real_tool", {})
    assert result.get("error") is not None


def test_list_tools_returns_output_retrieve_schema():
    from brainspace.mcp_server import list_tools

    tools = list_tools()
    names = [t["name"] for t in tools]
    assert "output_retrieve" in names
