"""Decline-case + negative-control policy (088.004-T).

Classifies a candidate tool output into a specific decline reason so callers
(the hook and the benchmark oracle) can report *why* a case declined rather
than silently passing it through or hiding it. Order matters: secret
screening takes priority over every other decline reason (secrets must never
reach a "compressible" decision on a technicality).
"""

import re

from brainspace import config
from brainspace.secret_screen import contains_secret


class DeclineReason:
    """Named decline reasons — a defined, reportable taxonomy."""

    TINY_OUTPUT = "tiny_output"
    SECRET_BEARING = "secret_bearing"
    GATE_READINESS_VERDICT = "gate_readiness_verdict"
    ACTIVE_STACK_TRACE = "active_stack_trace"
    FAILURE_BEARING_SUCCESS = "failure_bearing_success"
    OPERATOR_APPROVAL_TEXT = "operator_approval_text"
    UNWRITABLE_STORE = "unwritable_store"


_GATE_VERDICT_PATTERNS = [
    re.compile(r"##\s*Local Review Readiness"),
    re.compile(r"P-0\d\d\s+(GATE|VIOLATION)"),
    re.compile(r"\b(READY_WITH_FOLLOWUPS|READY_WITH_CONDITIONS|BLOCKED)\b"),
    # P-018 final-convergence follow-up finding: the plain successful
    # readiness form ("Outcome: READY") was not covered by any pattern --
    # only its READY_WITH_* / BLOCKED siblings were -- so a standalone
    # readiness summary reporting a clean "Outcome: READY" (without the
    # "## Local Review Readiness" heading itself, e.g. a status line quoted
    # elsewhere) passed through to compression, contrary to the
    # requirement that every gate/readiness verdict form is always
    # declined, never compressed.
    re.compile(r"(?i)\bOutcome:\s*READY\b"),
    re.compile(r"\bMERGE_(CONFIRMED|NOT_CONFIRMED|AUTHORIZED)\b"),
    re.compile(r"\breviewDecision\b"),
    re.compile(r"\bautoharness gate\b"),
    re.compile(r"(?i)Blocking findings:\s*P0=\d+,\s*P1=\d+"),
    re.compile(r"(?i)CI aggregation:\s*\S+"),
    re.compile(r"(?i)(^|\W)P[01]\b\s*[:)]|\*\*P[01]\*\*"),
]

_STACK_TRACE_PATTERNS = [
    re.compile(r"Traceback \(most recent call last\):"),
    re.compile(r"^\s*at .+\(.+:\d+:\d+\)", re.MULTILINE),  # JS-style frames
    re.compile(r"panic:"),
    re.compile(r"Exception in thread"),
]

_FAILURE_BEARING_PATTERNS = [
    re.compile(r"(?i)exit code:\s*[1-9]\d*"),
    re.compile(r"(?i)exit status\s*[1-9]\d*"),
    re.compile(r"(?i)returncode=[1-9]\d*"),
    re.compile(r"(?i)^stderr:", re.MULTILINE),
]

_OPERATOR_APPROVAL_PATTERNS = [
    re.compile(r"(?i)do you approve"),
    re.compile(r"(?i)\(y/n\)"),
    re.compile(r"(?i)please confirm"),
    re.compile(r"(?i)operator approval"),
]


def classify_decline_reason(text: str):
    """Return the ``DeclineReason`` that applies to ``text``, or ``None``.

    ``None`` means the output is a compression candidate — it still must
    pass the never-expand guard downstream.
    """
    if contains_secret(text):
        return DeclineReason.SECRET_BEARING

    if len(text) < config.NEVER_EXPAND_MIN_CHARS:
        return DeclineReason.TINY_OUTPUT

    if any(p.search(text) for p in _GATE_VERDICT_PATTERNS):
        return DeclineReason.GATE_READINESS_VERDICT

    if any(p.search(text) for p in _STACK_TRACE_PATTERNS):
        return DeclineReason.ACTIVE_STACK_TRACE

    if any(p.search(text) for p in _FAILURE_BEARING_PATTERNS):
        return DeclineReason.FAILURE_BEARING_SUCCESS

    if any(p.search(text) for p in _OPERATOR_APPROVAL_PATTERNS):
        return DeclineReason.OPERATOR_APPROVAL_TEXT

    return None
