"""Tests for the decline-case policy classifier (088.004-T).

Extends the secret-screen decline case with the full taxonomy from the
spike/plan: tiny outputs, gate/readiness verdicts, active stack traces, and
operator/approval text. Each must classify to a specific decline reason so
callers (hook + benchmark oracle) can report *why* a case declined rather
than hiding it.
"""

import pytest

from brainspace.policy import DeclineReason, classify_decline_reason


def test_tiny_output_declines():
    assert classify_decline_reason("ok") == DeclineReason.TINY_OUTPUT


def test_secret_bearing_declines():
    text = "AKIAABCDEFGHIJKLMNOP\n" + ("padding\n" * 60)
    assert classify_decline_reason(text) == DeclineReason.SECRET_BEARING


def test_gate_readiness_verdict_declines():
    text = (
        "## Local Review Readiness\n"
        "- Reviewed HEAD: `abc123`\n"
        "- Outcome: READY_WITH_FOLLOWUPS\n"
        "- Blocking findings: P0=0, P1=0\n" + ("padding line\n" * 40)
    )
    assert classify_decline_reason(text) == DeclineReason.GATE_READINESS_VERDICT


def test_p014_gate_output_declines():
    text = "P-014 GATE PASSED: local readiness verified at HEAD=abc123\n" + (
        "padding\n" * 60
    )
    assert classify_decline_reason(text) == DeclineReason.GATE_READINESS_VERDICT


def test_active_stack_trace_declines():
    text = (
        "Traceback (most recent call last):\n"
        '  File "app.py", line 10, in <module>\n'
        "ValueError: boom\n" + ("padding\n" * 40)
    )
    assert classify_decline_reason(text) == DeclineReason.ACTIVE_STACK_TRACE


def test_failure_bearing_success_declines():
    text = "command output\nexit code: 1\nstderr: something went wrong\n" + (
        "padding\n" * 60
    )
    assert classify_decline_reason(text) == DeclineReason.FAILURE_BEARING_SUCCESS


def test_operator_approval_text_declines():
    text = (
        "Do you approve this destructive operation? (y/n)\n" + ("padding\n" * 60)
    )
    assert classify_decline_reason(text) == DeclineReason.OPERATOR_APPROVAL_TEXT


def test_compressible_candidate_returns_none():
    text = "repeated noisy log line\n" * 200
    assert classify_decline_reason(text) is None


def test_blocking_findings_p0_p1_line_declines():
    text = (
        "Summary of review outcome\n"
        "Blocking findings: P0=1, P1=0\n" + ("padding line\n" * 40)
    )
    assert classify_decline_reason(text) == DeclineReason.GATE_READINESS_VERDICT


def test_ci_aggregation_status_line_declines():
    text = "CI aggregation: failed\n" + ("padding line\n" * 60)
    assert classify_decline_reason(text) == DeclineReason.GATE_READINESS_VERDICT


def test_p0_finding_bullet_line_declines():
    text = (
        "Review findings\n"
        "- **P0**: containment bypass in resolver.py\n" + ("padding line\n" * 40)
    )
    assert classify_decline_reason(text) == DeclineReason.GATE_READINESS_VERDICT


def test_p1_finding_bullet_line_declines():
    text = (
        "Review findings\n"
        "- **P1**: TTL silently extended on dedup\n" + ("padding line\n" * 40)
    )
    assert classify_decline_reason(text) == DeclineReason.GATE_READINESS_VERDICT


def test_plain_outcome_ready_line_declines():
    # P-018 final-convergence follow-up finding: only the READY_WITH_* /
    # BLOCKED siblings were covered -- a standalone readiness summary
    # reporting a clean "Outcome: READY" (without the "## Local Review
    # Readiness" heading itself, e.g. quoted in another status message)
    # previously passed through to compression, contrary to the
    # requirement that every gate/readiness verdict form is always
    # declined, never compressed.
    text = (
        "Merge readiness summary\n"
        "- Outcome: READY\n"
        "- Blocking findings: none\n" + ("padding line\n" * 40)
    )
    assert classify_decline_reason(text) == DeclineReason.GATE_READINESS_VERDICT


def test_outcome_ready_is_case_insensitive():
    text = "outcome: ready\n" + ("padding line\n" * 40)
    assert classify_decline_reason(text) == DeclineReason.GATE_READINESS_VERDICT


# --- 093.001-T: broadened colon-agnostic failure-signal coverage -----------
#
# The original detector required a colon ("exit code:\\s*[1-9]"), so common
# non-colon / alternate non-zero-exit and stderr forms escaped classification
# and could have their failure line collapsed into the omitted middle. These
# controls close that gap while proving the zero-exit / benign forms stay
# compressible (no false-positive regression) and secret precedence holds.

_PAD = "\n" + ("padding line\n" * 60)


@pytest.mark.parametrize(
    "failure_line",
    [
        "exit code 1",  # space, no colon
        "exit code 137",  # multi-digit, no colon
        "exited with code 1",
        "exited with exit code 1",
        "Process finished with exit code 1",
        "make: *** [build] Error 2",
        "*** [target] Error 1",
        "npm ERR! code ELIFECYCLE",
        "returncode 1",  # bare space form (not returncode=1)
    ],
)
def test_broadened_failure_forms_decline(failure_line):
    text = "command output\n" + failure_line + _PAD
    assert classify_decline_reason(text) == DeclineReason.FAILURE_BEARING_SUCCESS


@pytest.mark.parametrize(
    "benign_line",
    [
        "exit code: 0",
        "exit code 0",
        "exited with code 0",
        "Process finished with exit code 0",
        "the build failed with a warning; an error was logged earlier",
        "All checks passed",
    ],
)
def test_benign_zero_exit_forms_stay_compressible(benign_line):
    text = "command output\n" + benign_line + _PAD
    assert classify_decline_reason(text) is None


def test_failure_bearing_secret_precedence_preserved():
    # A broadened failure line + a secret must still classify as
    # SECRET_BEARING -- secret screening always wins (acceptance criterion).
    text = "exit code 1\nAKIAABCDEFGHIJKLMNOP\n" + ("padding line\n" * 60)
    assert classify_decline_reason(text) == DeclineReason.SECRET_BEARING


@pytest.mark.parametrize(
    "benign_line",
    [
        "exit code1",  # concatenated, no separator -> not a failure signal
        "exit status1",
        "returncode1",
        "the exit code was reported elsewhere",
    ],
)
def test_concatenated_failure_forms_stay_compressible(benign_line):
    # 093.001-T review finding: the separator must be a colon or horizontal
    # whitespace -- a digit fused directly to the marker is not a failure form.
    text = "command output\n" + benign_line + _PAD
    assert classify_decline_reason(text) is None


def test_cross_line_exit_code_is_not_a_failure_signal():
    # 093.001-T review finding: the horizontal-only separator must never span a
    # newline, so "exit code" ending a line followed by a line starting with a
    # digit is NOT classified as a failure-bearing success.
    text = "build output\nexit code\n1 item completed successfully\n" + (
        "padding line\n" * 60
    )
    assert classify_decline_reason(text) is None


def test_unwritable_store_reason_is_available_as_a_named_constant():
    # Exercised by the hook's fail-safe passthrough path, not by text
    # classification -- the reason must still be a defined enum member so
    # the benchmark can report it explicitly (not hide it).
    assert DeclineReason.UNWRITABLE_STORE is not None
