"""postToolUse compression hook prototype (088.002-T / 088.004-T).

Pipeline: matcher scope -> decline-case policy pre-screen (secrets, tiny
output, gate/readiness verdicts, active stack traces, failure-bearing
output, operator-approval text; see ``brainspace.policy``) -> type router
(JSON / git log / unified diff / prose; see ``_detect_content_type`` and
``_compress_view``) -> never-expand token+char guard -> DECIDE-THEN-STASH
(policy + never-expand decision BEFORE any durable write) -> write original
to the store -> return ``modifiedResult`` with a compressed view plus a
compact deterministic handle, else return ``{}`` to pass through unchanged.

Fail-safe: on ANY error (store, screen, guard, or unexpected payload shape),
return ``{}`` so the original passes through byte-identically. This never
emits a "placeholder-free elision" — either the full original is preserved,
or the compressed view was proven to preserve the required signal.

``postToolUseFailure`` outputs are NEVER rewritten (Copilot CLI cannot
replace them anyway; this is documented explicitly here for clarity).
"""

import json
import re

from brainspace import config
from brainspace.measurement import (
    ModelTokenizerUnavailable,
    count_tokens_strict,
    is_model_tokenizer_available,
)
from brainspace.policy import classify_decline_reason

_MATCHER_RE = re.compile(rf"^(?:{config.DEFAULT_MATCHER})$")


def _matches_scope(tool_name: str) -> bool:
    if not tool_name:
        return False
    return bool(_MATCHER_RE.match(tool_name))


# --- Type router (088.002-T review finding #14) -----------------------
#
# The compressor is type-agnostic head/tail-only truncation for "prose"
# style output, but that loses inline evidence (e.g. PR/issue reference
# numbers embedded in commit messages) for structured JSON / git log /
# unified-diff output when it appears deep in the "omitted middle" — this
# is exactly the known ``git-log-stat-history`` benchmark evidence-loss
# case. For those three types, route through an evidence-preserving
# compressor that keeps every line matching a required-evidence pattern
# (commit/diff headers, exit/stderr markers, PR/issue references) no
# matter where it appears, and only collapses runs of lines that match
# none of them.

_DIFF_HEADER_RE = re.compile(r"^diff --git ", re.MULTILINE)
_HUNK_HEADER_RE = re.compile(r"^@@ .*@@", re.MULTILINE)
_COMMIT_HEADER_RE = re.compile(r"^commit [0-9a-f]{7,40}\b", re.MULTILINE)

# Horizontal-only failure-signal separator (parity with policy._SEP): a colon
# (optionally followed by spaces/tabs) or one-or-more spaces/tabs, never a
# newline. Rejects concatenated ("exit code1") false protection and keeps the
# evidence-line match same-line (093.002-T review finding). The evidence layer
# uses \d+ (zero-exit forms are also protected, by design).
_SEP = r"(?::[ \t]*|[ \t]+)"
_RC_SEP = r"(?:=[ \t]*|[ \t]+)"

_EVIDENCE_LINE_PATTERNS = [
    re.compile(rf"(?i)exit code{_SEP}\d+"),
    re.compile(rf"(?i)exit status{_SEP}\d+"),
    # "exited with code 1", "exited with exit code 1",
    # "Process finished with exit code 1" (zero-exit forms also protected).
    re.compile(rf"(?i)(?:exited|finished) with (?:exit )?code{_SEP}\d+"),
    re.compile(rf"(?i)returncode{_RC_SEP}\d+"),
    # GNU make failure line: "*** [target] Error 1".
    re.compile(r"\*\*\*[ \t]*\[[^\]]*\][ \t]+Error[ \t]+\d+"),
    # npm failure marker.
    re.compile(r"(?i)npm ERR!"),
    re.compile(r"(?i)^stderr:"),
    re.compile(r"P-0\d\d\s+(?:GATE|VIOLATION)"),
    re.compile(r"\bHEAD=\S+"),
    re.compile(r"#\d+"),  # PR / issue reference numbers
    re.compile(r"^commit [0-9a-f]{7,40}\b"),
    re.compile(r"^Author:\s"),
    re.compile(r"^Date:\s"),
    re.compile(r"^diff --git "),
    re.compile(r"^@@ .*@@"),
    re.compile(r"^--- "),
    re.compile(r"^\+\+\+ "),
]


def _detect_content_type(text: str) -> str:
    """Classify ``text`` as ``"json"``, ``"diff"``, ``"log"``, or ``"prose"``."""
    stripped = text.strip()
    if stripped[:1] in ("{", "["):
        try:
            json.loads(stripped)
            return "json"
        except (ValueError, TypeError):
            pass
    if _DIFF_HEADER_RE.search(text) or _HUNK_HEADER_RE.search(text):
        return "diff"
    if _COMMIT_HEADER_RE.search(text):
        return "log"
    return "prose"


def _is_evidence_line(line: str) -> bool:
    return any(pattern.search(line) for pattern in _EVIDENCE_LINE_PATTERNS)


def _compress_lines_preserving_evidence(lines, keep_edge: int) -> str:
    """Collapse non-evidence line runs while ALWAYS keeping evidence lines.

    Unlike plain head/tail truncation, an evidence-bearing line (commit /
    diff headers, exit/stderr markers, PR/issue references) is preserved
    verbatim no matter where it appears in the text, not only at the head
    or tail.
    """
    total = len(lines)
    protected = [False] * total
    for i in range(min(keep_edge, total)):
        protected[i] = True
    for i in range(max(0, total - keep_edge), total):
        protected[i] = True
    for i, line in enumerate(lines):
        if _is_evidence_line(line):
            protected[i] = True

    out = []
    i = 0
    while i < total:
        if protected[i]:
            out.append(lines[i])
            i += 1
            continue
        j = i
        while j < total and not protected[j]:
            j += 1
        omitted = j - i
        out.append(f"... [{omitted} lines omitted by 088-F compression experiment] ...")
        i = j
    return "\n".join(out)


def _compress_view(text: str) -> str:
    """Collapse repeated bulk while preserving required inline evidence.

    Routes by detected content type:

    * ``json`` / ``log`` / ``diff`` — evidence-preserving compression that
      keeps every line matching a required-evidence pattern (see
      ``_EVIDENCE_LINE_PATTERNS``) regardless of position, and collapses
      only the remaining bulk runs.
    * ``prose`` — the original simple strategy: keep the first and last N
      lines verbatim (where exit codes, stderr, and final status usually
      live), collapsing the remaining middle into a single summary line.

    This is a prototype compressor; evidence preservation is verified
    independently by the 088.004-T evidence oracle before any savings
    claim is reported.
    """
    lines = text.splitlines(keepends=False)
    keep_edge = 5
    if len(lines) <= keep_edge * 2:
        return text

    content_type = _detect_content_type(text)
    if content_type in ("json", "log", "diff"):
        return _compress_lines_preserving_evidence(lines, keep_edge)

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
        # write the original at all. Three independent checks are required
        # (P-018 re-review finding #1, then finding round-5 #2): a
        # structured result with many protected evidence lines can stay
        # well under the *original* character count yet still exceed the
        # 10 KB additionalContext byte cap the Copilot CLI enforces -- a
        # char-count-only comparison would silently let that oversized,
        # cap-violating result through. Separately, a char-shorter
        # candidate is not guaranteed to tokenize to fewer tokens (e.g.
        # dense punctuation/unicode can tokenize less efficiently than the
        # original prose it replaced), so the "never-expand" promise this
        # module's docstring makes must be proven with an actual token
        # comparison (the same tokenizer 088.005-T's measurement harness
        # uses — a model tokenizer when available, else the cheap fallback
        # estimator), not inferred from character counts alone.
        footer_estimate = config.RETRIEVAL_FOOTER_TEMPLATE.format(handle="0" * 16)
        candidate = compressed + footer_estimate
        if len(candidate) >= len(text):
            return {}
        if len(candidate.encode("utf-8")) > config.ADDITIONAL_CONTEXT_CAP_BYTES:
            return {}
        # A real model tokenizer is required to PROVE the never-expand
        # invariant, not merely estimate it: without one, count_tokens()
        # silently falls back to the cheap char/4 estimator, which the
        # benchmark report itself refuses to treat as proof of lower
        # model-token counts (it reports that same state as INCONCLUSIVE,
        # not a safe win). The live hook must hold itself to the same
        # evidence bar -- decline before store.put() rather than stash and
        # rewrite output on an unproven estimate that could, in reality,
        # expand actual Copilot-model tokens (P-018 round-6 finding).
        #
        # ``is_model_tokenizer_available()`` only proves the tokenizer
        # LOADED successfully -- it does not prove ``encode()`` will
        # succeed for this specific text. Use ``count_tokens_strict()``
        # (never silently falls back) so a per-call encode failure on the
        # actual input declines rather than being masked by the fallback
        # estimator while still being treated as a proven real-model
        # comparison (P-018 round-8 finding).
        if not is_model_tokenizer_available():
            return {}
        try:
            if count_tokens_strict(candidate) >= count_tokens_strict(text):
                return {}
        except ModelTokenizerUnavailable:
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
