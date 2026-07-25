"""Tests for the default benchmark corpus builder (088.006-T).

The corpus builder captures REAL, read-only autoharness command output
where safe to do so, and falls back to a clearly-labeled synthetic
representative sample when a live surface (e.g. Engram/graphtor MCP
indices) is not available in the current environment. These tests use a
stubbed command runner so they do not depend on external tools being
installed/available in every CI environment.
"""

from brainspace.benchmark import BenchmarkCase
from brainspace.corpus import build_default_corpus, last_nonblank_line


def test_last_nonblank_line_returns_final_non_empty_line():
    text = "line one\nline two\n\n   \nline three\n"
    assert last_nonblank_line(text) == "line three"


def test_last_nonblank_line_handles_empty_text():
    assert last_nonblank_line("") == ""


def test_build_default_corpus_uses_injected_command_runner(tmp_path):
    calls = []

    def fake_runner(args, cwd):
        calls.append((tuple(args), cwd))
        return f"stub output for {' '.join(args)}\n" + ("padding\n" * 50) + "final line"

    cases = build_default_corpus(str(tmp_path), command_runner=fake_runner)
    assert len(calls) > 0
    assert all(isinstance(c, BenchmarkCase) for c in cases)


def test_build_default_corpus_includes_compression_positive_and_decline_cases(tmp_path):
    def fake_runner(args, cwd):
        return f"stub output for {' '.join(args)}\n" + ("padding\n" * 50) + "final line"

    cases = build_default_corpus(str(tmp_path), command_runner=fake_runner)
    categories = {"decline": 0, "positive": 0}
    for case in cases:
        if case.expect_decline:
            categories["decline"] += 1
        else:
            categories["positive"] += 1
    assert categories["decline"] > 0
    assert categories["positive"] > 0


def test_build_default_corpus_marks_unavailable_live_surface_as_synthetic(tmp_path):
    def fake_runner(args, cwd):
        return f"stub output for {' '.join(args)}\n" + ("padding\n" * 50) + "final line"

    cases = build_default_corpus(str(tmp_path), command_runner=fake_runner)
    provenances = {c.name: c.provenance for c in cases}
    # At least one corpus entry documents a non-live/synthetic provenance
    # (e.g. the engram/graphtor search-results representative sample).
    assert any(p != "live" for p in provenances.values())


def test_build_default_corpus_live_cases_carry_required_fact_from_output(tmp_path):
    def fake_runner(args, cwd):
        return "line one\n" + ("padding\n" * 50) + "the final captured line"

    cases = build_default_corpus(str(tmp_path), command_runner=fake_runner)
    live_cases = [c for c in cases if c.provenance == "live" and not c.expect_decline]
    assert len(live_cases) > 0
    for case in live_cases:
        assert case.required_fact  # every live positive case has a fact to check
