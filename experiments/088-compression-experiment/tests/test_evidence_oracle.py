"""Tests for the evidence oracle (088.004-T).

For each benchmark task, required inline facts (exit status, stderr, gate
verdicts, IDs) must remain visible in the compressed view WITHOUT retrieval.
"""

from brainspace.evidence_oracle import evaluate_oracle


def test_passes_when_exit_status_preserved_in_compressed_view():
    original = "line\n" * 50 + "exit code: 1\n" + "line\n" * 50
    compressed = "head lines...\nexit code: 1\n...tail lines"
    result = evaluate_oracle(original, compressed)
    assert result.passed is True


def test_fails_when_exit_status_dropped_from_compressed_view():
    original = "line\n" * 50 + "exit code: 1\n" + "line\n" * 50
    compressed = "head lines...\n...tail lines (no exit status)"
    result = evaluate_oracle(original, compressed)
    assert result.passed is False
    assert "exit code: 1" in result.missing_facts


def test_fails_when_pr_id_dropped():
    original = "opened PR #427 for review\n" + ("padding\n" * 40)
    compressed = "opened a pull request for review\n...omitted..."
    result = evaluate_oracle(original, compressed)
    assert result.passed is False


def test_passes_when_pr_id_preserved():
    original = "opened PR #427 for review\n" + ("padding\n" * 40)
    compressed = "opened PR #427 for review\n...omitted..."
    result = evaluate_oracle(original, compressed)
    assert result.passed is True


def test_passes_when_no_required_facts_present():
    original = "just some prose describing the change with no facts\n" * 10
    compressed = "a short summary of the same prose"
    result = evaluate_oracle(original, compressed)
    assert result.passed is True
    assert result.missing_facts == []


def test_fails_when_gate_verdict_dropped():
    original = "P-014 GATE PASSED: local readiness verified at HEAD=abcdef1\n" + (
        "padding\n" * 40
    )
    compressed = "the gate passed\n...omitted..."
    result = evaluate_oracle(original, compressed)
    assert result.passed is False


def test_fails_when_stderr_line_dropped():
    original = "output\nstderr: disk full\n" + ("padding\n" * 40)
    compressed = "output summary\n...omitted..."
    result = evaluate_oracle(original, compressed)
    assert result.passed is False
