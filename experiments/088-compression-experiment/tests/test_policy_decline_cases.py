"""Tests for the decline-case policy classifier (088.004-T).

Extends the secret-screen decline case with the full taxonomy from the
spike/plan: tiny outputs, gate/readiness verdicts, active stack traces, and
operator/approval text. Each must classify to a specific decline reason so
callers (hook + benchmark oracle) can report *why* a case declined rather
than hiding it.
"""

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


def test_unwritable_store_reason_is_available_as_a_named_constant():
    # Exercised by the hook's fail-safe passthrough path, not by text
    # classification -- the reason must still be a defined enum member so
    # the benchmark can report it explicitly (not hide it).
    assert DeclineReason.UNWRITABLE_STORE is not None
