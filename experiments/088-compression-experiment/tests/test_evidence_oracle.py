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


# --- 093.002-T: broadened colon-agnostic failure-signal parity -------------
#
# The oracle required-fact patterns must recognize the SAME broadened
# non-zero-exit / stderr forms as policy.py (093.001-T), so a compressed
# view that drops one of these failure facts is reported as evidence loss
# regardless of colon form. The oracle intentionally still matches zero-exit
# forms and uses whole-line matches for markers such as `npm ERR!`.


def test_oracle_flags_dropped_exit_code_no_colon():
    original = "line\n" * 40 + "exit code 1\n" + "line\n" * 40
    compressed = "head lines...\n...tail lines (no exit status)"
    result = evaluate_oracle(original, compressed)
    assert result.passed is False
    assert any("exit code 1" in fact for fact in result.missing_facts)


def test_oracle_passes_when_exit_code_no_colon_preserved():
    original = "line\n" * 40 + "exit code 1\n" + "line\n" * 40
    compressed = "head...\nexit code 1\n...tail"
    result = evaluate_oracle(original, compressed)
    assert result.passed is True


def test_oracle_flags_dropped_exited_with_code():
    original = "build\n" + ("padding\n" * 40) + "exited with code 1\n"
    compressed = "build summary\n...omitted..."
    result = evaluate_oracle(original, compressed)
    assert result.passed is False


def test_oracle_flags_dropped_make_error_line():
    original = "compiling\n" + ("padding\n" * 40) + "make: *** [build] Error 2\n"
    compressed = "compiling summary\n...omitted..."
    result = evaluate_oracle(original, compressed)
    assert result.passed is False
    assert any("Error 2" in fact for fact in result.missing_facts)


def test_oracle_flags_dropped_npm_err_whole_line():
    original = "installing\n" + ("padding\n" * 40) + "npm ERR! code ELIFECYCLE\n"
    compressed = "installing summary\n...omitted..."
    result = evaluate_oracle(original, compressed)
    assert result.passed is False
    # Whole-line marker match: the full npm ERR! line is the required fact.
    assert any("npm ERR! code ELIFECYCLE" in fact for fact in result.missing_facts)


# --- Negative controls (093.002-T review finding) -------------------------
# The broadened separator is horizontal-only: it must never span a newline and
# must not fuse to an adjacent digit. Because the oracle scans the full
# multi-line string, a colon-optional + \s* form would synthesize a spurious
# "exit code 1" fact across unrelated lines; these controls lock that out.


def test_oracle_does_not_synthesize_cross_line_exit_code_fact():
    # "exit code" ends one line; the next line merely starts with a digit.
    # No "exit code 1" fact exists, so dropping the region must NOT fail.
    original = (
        "build log\n" + ("padding\n" * 20) + "exit code\n1 item completed\n"
    )
    compressed = "build log summary\n...omitted..."
    result = evaluate_oracle(original, compressed)
    assert all("exit code 1" not in fact for fact in result.missing_facts)


def test_oracle_does_not_treat_concatenated_exit_code_as_fact():
    # "exit code1" has no separator -> not a required failure fact.
    original = "run log\n" + ("padding\n" * 20) + "exit code1\n"
    compressed = "run log summary\n...omitted..."
    result = evaluate_oracle(original, compressed)
    assert all(
        "exit code" not in fact.lower() for fact in result.missing_facts
    )
