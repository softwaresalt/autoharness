"""postToolUse compression hook prototype (088.002-T / 088.004-T).

Pipeline: matcher scope -> decline-case policy pre-screen (secrets, tiny
output, gate/readiness verdicts, active stack traces, failure-bearing
output, operator-approval text; see ``brainspace.policy``) -> type router
(implicit in ``_compress_view``) -> never-expand token+char guard ->
DECIDE-THEN-STASH (policy + never-expand decision BEFORE any durable write)
-> write original to the store -> return ``modifiedResult`` with a
compressed view plus a compact deterministic handle, else return ``{}`` to
pass through unchanged.

Fail-safe: on ANY error (store, screen, guard, or unexpected payload shape),
return ``{}`` so the original passes through byte-identically. This never
emits a "placeholder-free elision" — either the full original is preserved,
or the compressed view was proven to preserve the required signal.

``postToolUseFailure`` outputs are NEVER rewritten (Copilot CLI cannot
replace them anyway; this is documented explicitly here for clarity).
"""

import re

from brainspace import config
from brainspace.policy import classify_decline_reason

_MATCHER_RE = re.compile(rf"^(?:{config.DEFAULT_MATCHER})$")


def _matches_scope(tool_name: str) -> bool:
    if not tool_name:
        return False
    return bool(_MATCHER_RE.match(tool_name))


def _compress_view(text: str) -> str:
    """Collapse repeated bulk while preserving head/tail signal.

    Deliberately simple type-agnostic strategy: keep the first and last N
    lines verbatim (where exit codes, stderr, and final status usually
    live), and collapse the remaining repeated middle into a single summary
    line. This is a prototype compressor; evidence preservation is verified
    independently by the 088.004-T evidence oracle before any savings claim
    is reported.
    """
    lines = text.splitlines(keepends=False)
    keep_edge = 5
    if len(lines) <= keep_edge * 2:
        return text
    head = lines[:keep_edge]
    tail = lines[-keep_edge:]
    omitted = len(lines) - (keep_edge * 2)
    summary = f"... [{omitted} lines omitted by 088-F compression experiment] ..."
    return "\n".join(head + [summary] + tail)


def process_post_tool_use(payload, store):
    """Process a ``postToolUse`` event. Returns a dict per the hook contract."""
    try:
        if not config.is_enabled():
            return {}

        tool_result = payload.get("toolResult") or {}
        if tool_result.get("resultType") != "success":
            return {}

        text = tool_result.get("textResultForLlm")
        if not isinstance(text, str) or not text:
            return {}

        tool_name = payload.get("toolName", "")
        if not _matches_scope(tool_name):
            return {}

        # Decline-case policy pre-screen — secrets, tiny outputs, gate/
        # readiness verdicts, active stack traces, failure-bearing output,
        # and operator-approval text all decline BEFORE any durable write,
        # unconditionally (088.004-T).
        if classify_decline_reason(text) is not None:
            return {}

        compressed = _compress_view(text)

        # DECIDE (before stashing): the never-expand guard must hold for the
        # compressed view + footer overhead too, or we decline and never
        # write the original at all.
        footer_estimate_len = len(
            config.RETRIEVAL_FOOTER_TEMPLATE.format(handle="0" * 16)
        )
        if (len(compressed) + footer_estimate_len) >= len(text):
            return {}

        # THEN STASH: only after the decision above holds do we write the
        # original durably.
        handle = store.put(text)

        footer = config.RETRIEVAL_FOOTER_TEMPLATE.format(handle=handle)
        return {
            "modifiedResult": {
                "resultType": "success",
                "textResultForLlm": compressed + footer,
            }
        }
    except Exception:
        # Fail-safe: any store/screen/guard error passes the original
        # through byte-identically. Never emit placeholder-free elision.
        return {}


def process_post_tool_use_failure(payload):
    """``postToolUseFailure`` outputs are NEVER rewritten. Always ``{}``."""
    return {}
