"""Tests for the postToolUse compression hook prototype (088.002-T).

Covers: matcher scoping, secret-screen-before-store, never-expand guard,
decide-then-stash ordering (no store row on decline), deterministic
placeholders, and fail-safe passthrough on any internal error.
"""

import pytest

from brainspace import config
from brainspace.hook import process_post_tool_use, process_post_tool_use_failure
from brainspace.store import BrainspaceStore


@pytest.fixture(autouse=True)
def enable_experiment(monkeypatch):
    monkeypatch.setenv(config.ENABLED_ENV_VAR, "1")


@pytest.fixture
def store(tmp_path):
    s = BrainspaceStore(str(tmp_path))
    yield s
    s.close()


def _payload(tool_name, text):
    return {
        "sessionId": "s1",
        "timestamp": 1234567890,
        "cwd": "/workspace",
        "toolName": tool_name,
        "toolArgs": {},
        "toolResult": {"resultType": "success", "textResultForLlm": text},
    }


def test_disabled_flag_always_passes_through(monkeypatch, store):
    monkeypatch.delenv(config.ENABLED_ENV_VAR, raising=False)
    big_text = ("line of noisy output\n" * 100)
    result = process_post_tool_use(_payload("bash", big_text), store)
    assert result == {}
    assert store.row_count() == 0


def test_out_of_matcher_scope_tool_passes_through(store):
    text = "line of noisy output\n" * 100
    result = process_post_tool_use(_payload("ask_user", text), store)
    assert result == {}
    assert store.row_count() == 0


def test_tiny_output_declines_never_expand_guard(store):
    result = process_post_tool_use(_payload("bash", "ok"), store)
    assert result == {}
    assert store.row_count() == 0


def test_secret_bearing_output_declines_before_store(store):
    text = "AKIAABCDEFGHIJKLMNOP\n" + ("padding line\n" * 50)
    result = process_post_tool_use(_payload("bash", text), store)
    assert result == {}
    assert store.row_count() == 0  # no durable row for a declined attempt


def test_large_compressible_output_is_compressed_and_stashed(store):
    text = "repeated noisy log line\n" * 200
    result = process_post_tool_use(_payload("bash", text), store)
    assert "modifiedResult" in result
    modified = result["modifiedResult"]
    assert modified["resultType"] == "success"
    assert len(modified["textResultForLlm"]) < len(text)
    assert store.row_count() == 1


def test_compressed_view_contains_deterministic_handle_footer(store):
    text = "repeated noisy log line\n" * 200
    result1 = process_post_tool_use(_payload("bash", text), store)
    result2 = process_post_tool_use(_payload("bash", text), store)
    footer1 = result1["modifiedResult"]["textResultForLlm"]
    footer2 = result2["modifiedResult"]["textResultForLlm"]
    assert footer1 == footer2  # deterministic — no timestamps/mutable counters
    assert store.row_count() == 1  # identical content maps to same handle


def test_stashed_original_is_byte_equivalent_retrievable(store):
    text = "repeated noisy log line\n" * 200
    result = process_post_tool_use(_payload("bash", text), store)
    footer = result["modifiedResult"]["textResultForLlm"]
    # Extract handle from the footer and confirm byte-equivalent retrieval.
    import re

    match = re.search(r'output_retrieve\(handle="([0-9a-f]+)"\)', footer)
    assert match is not None
    handle = match.group(1)
    assert store.get(handle) == text


def test_store_error_falls_back_to_byte_identical_passthrough(store, monkeypatch):
    text = "repeated noisy log line\n" * 200

    def _boom(_self, _text):
        raise RuntimeError("simulated store failure")

    monkeypatch.setattr(BrainspaceStore, "put", _boom)
    result = process_post_tool_use(_payload("bash", text), store)
    assert result == {}  # fail-safe passthrough, never partial elision


def test_gate_readiness_verdict_declines_before_store(store):
    text = "P-014 GATE PASSED: local readiness verified at HEAD=abc123\n" + (
        "padding\n" * 60
    )
    result = process_post_tool_use(_payload("bash", text), store)
    assert result == {}
    assert store.row_count() == 0


def test_active_stack_trace_declines_before_store(store):
    text = "Traceback (most recent call last):\n" + ("  File x, line y\n" * 60)
    result = process_post_tool_use(_payload("bash", text), store)
    assert result == {}
    assert store.row_count() == 0


def test_failure_bearing_output_declines_before_store(store):
    text = "command output\nexit code: 1\nstderr: something went wrong\n" + (
        "padding\n" * 60
    )
    result = process_post_tool_use(_payload("bash", text), store)
    assert result == {}
    assert store.row_count() == 0


def test_operator_approval_text_declines_before_store(store):
    text = "Do you approve this destructive operation? (y/n)\n" + ("padding\n" * 60)
    result = process_post_tool_use(_payload("bash", text), store)
    assert result == {}
    assert store.row_count() == 0


def test_post_tool_use_failure_is_never_rewritten(store):
    payload = {
        "sessionId": "s1",
        "timestamp": 1,
        "cwd": "/workspace",
        "toolName": "bash",
        "toolArgs": {},
        "error": "command failed with exit code 1",
    }
    assert process_post_tool_use_failure(payload) == {}
    assert process_post_tool_use_failure({"anything": "goes"}) == {}
