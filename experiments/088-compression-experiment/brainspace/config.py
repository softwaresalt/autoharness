"""Configuration and flag gate for the 088-F compression experiment.

Disabled by default (Constitution / plan condition #1). Nothing durable
happens unless ``BRAINSPACE_EXPERIMENT_ENABLED=1`` is set in the environment.
"""

import os

#: Master flag. Disabled by default — the hook must no-op (return ``{}``)
#: and the store must not be created unless this is explicitly enabled.
ENABLED_ENV_VAR = "BRAINSPACE_EXPERIMENT_ENABLED"


def is_enabled() -> bool:
    """Return True only when the experiment flag is explicitly set to "1"."""
    return os.environ.get(ENABLED_ENV_VAR) == "1"


#: Store location, relative to the workspace root (Constitution IV: repo-local,
#: gitignored, never user-home/global, never OS temp, never .git/).
STORE_RELATIVE_DIR = os.path.join(".autoharness", "cache", "brainspace")
STORE_DB_FILENAME = "ccr.sqlite3"

#: Explicit workspace-root pin (finding #12): when set, this takes
#: precedence over any per-invocation ``cwd`` so the hook (subprocess per
#: tool call, sees the session ``cwd``) and the MCP server (long-lived
#: process, sees only its own ``cwd``/env at startup) resolve the SAME
#: store root even when a tool runs from a subdirectory. See
#: ``brainspace.workspace.resolve_workspace_root``.
WORKSPACE_ENV_VAR = "BRAINSPACE_WORKSPACE"

#: Retention: short TTL + size cap (086-F carried forward). Never silently
#: extended on dedup/access.
DEFAULT_TTL_SECONDS = 4 * 60 * 60  # 4 hours — session/window bounded
DEFAULT_MAX_STORE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MiB

#: Never-expand guard: minimum raw size (chars) before compression is even
#: considered. Below this, placeholder + retrieval-footer overhead always
#: loses the token-level check, so the hook must decline.
NEVER_EXPAND_MIN_CHARS = 400

#: additionalContext is capped at 10 KB by the Copilot CLI postToolUse
#: contract (CONFIRMED — see docs/decisions/2026-07-25-...-findings.md).
ADDITIONAL_CONTEXT_CAP_BYTES = 10 * 1024

#: Matcher scope (spike §7.1): noisy tools plus MCP result tools.
DEFAULT_MATCHER = r"bash|view|task|.*_mcp.*"

#: P-018 round-10/11 finding: the ``postToolUse`` hook payload does not
#: identify which Copilot model/tokenizer is actually in play for the live
#: session, so a real model tokenizer must never be ASSUMED (e.g.
#: hardcoding ``cl100k_base``) -- doing so lets a session on a different
#: model be rewritten based on an unrelated token count, silently
#: defeating the never-expand guard's own promise. Instead, the operator
#: must explicitly BIND this environment variable to one of the encodings
#: this experiment has been reviewed against; any unset or unrecognized
#: value is treated as "unbound" and the model tokenizer is reported
#: unavailable (fail-safe: decline compression rather than guess).
MODEL_ENCODING_ENV_VAR = "BRAINSPACE_MODEL_ENCODING"

#: Explicit allowlist of model/tokenizer encodings this experiment has been
#: reviewed against. Do not add an encoding here without also confirming
#: (and documenting) which Copilot model(s) actually use it.
SUPPORTED_MODEL_ENCODINGS = frozenset({"cl100k_base", "o200k_base"})


def get_bound_model_encoding():
    """Return the operator-declared, explicitly-supported model encoding
    for this session, or ``None`` if unbound or unrecognized.

    An installed ``tiktoken`` alone is never sufficient to authorize the
    never-expand guard's real-model comparison -- the operator must
    explicitly declare which encoding matches the live session's actual
    model via :data:`MODEL_ENCODING_ENV_VAR`. Unset or unrecognized values
    fail closed (return ``None``), which the measurement module treats as
    "no model tokenizer available" so the guard declines rather than
    silently rewriting on a mismatched model's token count.
    """
    value = os.environ.get(MODEL_ENCODING_ENV_VAR)
    if value in SUPPORTED_MODEL_ENCODINGS:
        return value
    return None

#: Compact deterministic footer template appended so the model can request
#: the byte-equivalent original. No timestamps/mutable counters (086 risk:
#: prompt-cache fragility).
RETRIEVAL_FOOTER_TEMPLATE = (
    "\n\n[compressed by 088-F experiment; retrieve full output with "
    "output_retrieve(handle=\"{handle}\")]"
)
