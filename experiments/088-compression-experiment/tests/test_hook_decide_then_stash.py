"""Tests for the postToolUse compression hook prototype (088.002-T).

Covers: matcher scoping, secret-screen-before-store, never-expand guard,
decide-then-stash ordering (no store row on decline), deterministic
placeholders, and fail-safe passthrough on any internal error.
"""

import pytest

from brainspace import config
from brainspace import hook as hook_module
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


def test_large_compressible_output_is_compressed_and_stashed(store, monkeypatch):
    # Compression requires a real model tokenizer to prove the never-expand
    # invariant (P-018 round-6 finding) -- simulate one being available so
    # this test exercises the compress-and-stash path regardless of whether
    # the real ``tiktoken`` dependency happens to be installed in whatever
    # environment runs the suite.
    monkeypatch.setattr(hook_module, "is_model_tokenizer_available", lambda: True)
    text = "repeated noisy log line\n" * 200
    result = process_post_tool_use(_payload("bash", text), store)
    assert "modifiedResult" in result
    modified = result["modifiedResult"]
    assert modified["resultType"] == "success"
    assert len(modified["textResultForLlm"]) < len(text)
    assert store.row_count() == 1


def test_compressed_view_contains_deterministic_handle_footer(store, monkeypatch):
    monkeypatch.setattr(hook_module, "is_model_tokenizer_available", lambda: True)
    text = "repeated noisy log line\n" * 200
    result1 = process_post_tool_use(_payload("bash", text), store)
    result2 = process_post_tool_use(_payload("bash", text), store)
    footer1 = result1["modifiedResult"]["textResultForLlm"]
    footer2 = result2["modifiedResult"]["textResultForLlm"]
    assert footer1 == footer2  # deterministic — no timestamps/mutable counters
    assert store.row_count() == 1  # identical content maps to same handle


def test_stashed_original_is_byte_equivalent_retrievable(store, monkeypatch):
    monkeypatch.setattr(hook_module, "is_model_tokenizer_available", lambda: True)
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


def test_never_expand_guard_also_enforces_additional_context_byte_cap(store):
    # P-018 re-review finding #1 (new round): the never-expand guard
    # previously only compared character counts against the original, so a
    # structured (git-log-style) result with many protected evidence lines
    # (commit/Author/Date headers) could remain well under the *original*
    # length yet still exceed the 10 KB additionalContext cap the Copilot
    # CLI enforces. Build such a case: each iteration contributes ~120
    # protected bytes (commit/Author/Date headers, never collapsed) plus a
    # large filler run that DOES compress away -- across enough iterations
    # the surviving protected content alone exceeds the 10 KB cap, while the
    # overall compressed size is still comfortably shorter than the huge
    # original (so the old char-only check would have let it through).
    blocks = []
    for i in range(100):
        blocks.append(f"commit {i:07x}deadbeef1234567890abcdef")
        blocks.append("Author: Someone <someone@example.com>")
        blocks.append("Date:   Mon Jan 1 00:00:00 2024 +0000")
        blocks.extend(["    filler filler filler filler filler filler"] * 50)
    text = "\n".join(blocks)

    result = process_post_tool_use(_payload("bash", text), store)

    assert result == {}
    assert store.row_count() == 0


def test_never_expand_guard_uses_real_token_comparison_not_char_count_only(
    store, monkeypatch
):
    # P-018 round-5 finding: the never-expand guard previously compared only
    # character counts, but a char-shorter candidate is not guaranteed to
    # tokenize to fewer tokens (dense punctuation/unicode can tokenize less
    # efficiently than the prose it replaced). Force a token counter where
    # the compressed candidate -- despite being far fewer CHARACTERS than
    # the original -- reports MORE tokens, and prove the guard declines
    # (and stashes nothing) on the token comparison alone, not just chars.
    # A model tokenizer must be simulated as available so this exercises
    # the token-comparison branch itself rather than the round-6
    # no-tokenizer decline added below.
    monkeypatch.setattr(hook_module, "is_model_tokenizer_available", lambda: True)
    text = "repeated noisy log line\n" * 200

    def _adversarial_token_counter(candidate_text):
        return 1 if candidate_text == text else 10**6

    monkeypatch.setattr(hook_module, "count_tokens", _adversarial_token_counter)

    result = process_post_tool_use(_payload("bash", text), store)

    assert result == {}
    assert store.row_count() == 0


def test_never_expand_guard_declines_without_model_tokenizer_even_when_compressible(
    store, monkeypatch
):
    # P-018 round-6 finding: count_tokens() silently falls back to the cheap
    # char/4 estimator when no real model tokenizer is available, which
    # cannot PROVE the never-expand invariant -- the committed benchmark
    # report already treats this exact state as INCONCLUSIVE (criterion 1
    # unproven), so the live hook must hold itself to the same evidence bar
    # and decline (never stash/rewrite) rather than act on an unproven
    # estimate, even for clearly, dramatically compressible content.
    monkeypatch.setattr(hook_module, "is_model_tokenizer_available", lambda: False)
    text = "repeated noisy log line\n" * 200

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
