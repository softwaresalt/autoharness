"""Tests for the AUC token-savings measurement harness (088.005-T).

Single concern: measurement only. No benchmark orchestration, no hook
internals — callers pass in an (original, compressed_view, footer) triple
already produced elsewhere.
"""

import pytest

from brainspace import measurement
from brainspace.tokenizer_fallback import estimate_tokens


def test_fallback_estimator_is_deterministic_and_positive():
    text = "the quick brown fox jumps over the lazy dog " * 20
    a = estimate_tokens(text)
    b = estimate_tokens(text)
    assert a == b
    assert a > 0


def test_fallback_estimator_scales_with_length():
    short = "hello world"
    long = "hello world " * 50
    assert estimate_tokens(long) > estimate_tokens(short)


def test_count_tokens_uses_fallback_when_no_model_tokenizer_available(monkeypatch):
    # Force the "no model tokenizer" path regardless of what's installed.
    monkeypatch.setattr(measurement, "_load_model_tokenizer", lambda: None)
    text = "some sample text for token counting " * 10
    result = measurement.count_tokens(text)
    assert result == estimate_tokens(text)


def test_measure_reports_raw_compressed_and_net_savings():
    original = "repeated noisy log line\n" * 200
    compressed = "head...\n[190 lines omitted]\n...tail"
    footer = (
        '\n\n[compressed by 088-F experiment; retrieve full output with '
        'output_retrieve(handle="abc123")]'
    )
    result = measurement.measure(original, compressed, footer)
    assert result.raw_tokens > result.compressed_tokens
    assert result.net_savings_tokens == result.raw_tokens - result.compressed_tokens
    assert result.net_savings_tokens > 0


def test_measure_projects_auc_over_1_3_5_10_turns():
    original = "repeated noisy log line\n" * 200
    compressed = "head...\n[190 lines omitted]\n...tail"
    footer = (
        '\n\n[compressed by 088-F experiment; retrieve full output with '
        'output_retrieve(handle="abc123")]'
    )
    result = measurement.measure(original, compressed, footer)
    assert set(result.projected_savings_by_turn.keys()) == {1, 3, 5, 10}
    # Projected savings must scale linearly with turn count (same output
    # re-sent each turn) — this is the AUC assumption stated in the task.
    assert (
        result.projected_savings_by_turn[10]
        == result.net_savings_tokens * 10
    )
    assert (
        result.projected_savings_by_turn[3]
        == result.net_savings_tokens * 3
    )


def test_measure_flags_when_net_savings_is_negative_or_zero():
    # Tiny output: compressed view + footer overhead exceeds the raw size.
    original = "short"
    compressed = "short"
    footer = (
        '\n\n[compressed by 088-F experiment; retrieve full output with '
        'output_retrieve(handle="abc123")]'
    )
    result = measurement.measure(original, compressed, footer)
    assert result.net_savings_tokens <= 0
    assert result.is_safe_win is False


def test_measure_flags_cap_violation_when_additional_context_exceeds_10kb():
    original = "x" * 50_000
    compressed = "y" * 11_000  # compressed view alone exceeds the 10 KB cap
    footer = "footer"
    result = measurement.measure(original, compressed, footer)
    assert result.exceeds_additional_context_cap is True


def test_measure_does_not_flag_cap_violation_when_within_limit():
    original = "x" * 50_000
    compressed = "y" * 500
    footer = "footer"
    result = measurement.measure(original, compressed, footer)
    assert result.exceeds_additional_context_cap is False


def test_measure_is_safe_win_requires_positive_net_and_cap_compliance():
    original = "repeated noisy log line\n" * 200
    compressed = "head...\n[190 lines omitted]\n...tail"
    footer = (
        '\n\n[compressed by 088-F experiment; retrieve full output with '
        'output_retrieve(handle="abc123")]'
    )
    result = measurement.measure(original, compressed, footer)
    assert result.is_safe_win is True


def test_measure_dual_reports_fallback_and_model_results_separately():
    original = "repeated noisy log line\n" * 200
    compressed = "head...\n[190 lines omitted]\n...tail"
    footer = (
        '\n\n[compressed by 088-F experiment; retrieve full output with '
        'output_retrieve(handle="abc123")]'
    )
    dual = measurement.measure_dual(original, compressed, footer)
    assert set(dual.keys()) == {"fallback", "model"}
    assert dual["fallback"].compressed_tokens < dual["fallback"].raw_tokens


def test_measure_dual_reports_none_for_model_when_tokenizer_unavailable(monkeypatch):
    monkeypatch.setattr(measurement, "_load_model_tokenizer", lambda: None)
    original = "repeated noisy log line\n" * 200
    compressed = "head...\n[190 lines omitted]\n...tail"
    footer = "footer"
    dual = measurement.measure_dual(original, compressed, footer)
    assert dual["model"] is None


def test_measure_dual_reports_none_for_model_when_encode_raises_for_this_input(monkeypatch):
    # P-018 round-8 finding: a tokenizer that LOADED successfully can still
    # raise for a specific input's encode() call. measure_dual() must
    # report this honestly as "no model result" rather than crashing or
    # silently substituting the fallback estimator's numbers.
    def _raising_tokenizer(text):
        raise RuntimeError("simulated encode failure for this input")

    monkeypatch.setattr(measurement, "_load_model_tokenizer", lambda: _raising_tokenizer)
    original = "repeated noisy log line\n" * 200
    compressed = "head...\n[190 lines omitted]\n...tail"
    footer = "footer"
    dual = measurement.measure_dual(original, compressed, footer)
    assert dual["model"] is None
    assert dual["fallback"] is not None


def test_count_tokens_strict_raises_when_no_model_tokenizer_available(monkeypatch):
    monkeypatch.setattr(measurement, "_load_model_tokenizer", lambda: None)
    with pytest.raises(measurement.ModelTokenizerUnavailable):
        measurement.count_tokens_strict("some text")


def test_count_tokens_strict_raises_when_tokenizer_encode_fails_for_this_input(monkeypatch):
    # P-018 round-8 finding: is_model_tokenizer_available() only proves the
    # tokenizer LOADED -- it does not prove encode() succeeds for every
    # input. count_tokens_strict() must never silently fall back to the
    # estimator on an encode failure; it must raise so the caller (e.g. the
    # hook's never-expand guard) can decline instead of masking the failure.
    def _raising_tokenizer(text):
        raise RuntimeError("simulated encode failure for this input")

    monkeypatch.setattr(measurement, "_load_model_tokenizer", lambda: _raising_tokenizer)
    with pytest.raises(measurement.ModelTokenizerUnavailable):
        measurement.count_tokens_strict("some text")


def test_count_tokens_strict_returns_zero_for_empty_text(monkeypatch):
    monkeypatch.setattr(measurement, "_load_model_tokenizer", lambda: lambda t: 999)
    assert measurement.count_tokens_strict("") == 0


def test_count_tokens_strict_uses_real_tokenizer_when_available(monkeypatch):
    monkeypatch.setattr(measurement, "_load_model_tokenizer", lambda: lambda t: 42)
    assert measurement.count_tokens_strict("some text") == 42


def test_count_tokens_still_falls_back_silently_for_non_strict_callers(monkeypatch):
    # count_tokens() (the non-strict variant) is intentionally left
    # fallback-tolerant for reporting-only callers that already treat a
    # missing/failed model tokenizer as a distinct honesty signal elsewhere
    # (e.g. is_model_tokenizer_available()); only the strict variant used to
    # AUTHORIZE a decision must refuse to mask an encode failure.
    def _raising_tokenizer(text):
        raise RuntimeError("simulated encode failure for this input")

    monkeypatch.setattr(measurement, "_load_model_tokenizer", lambda: _raising_tokenizer)
    text = "some sample text for token counting " * 10
    assert measurement.count_tokens(text) == estimate_tokens(text)
