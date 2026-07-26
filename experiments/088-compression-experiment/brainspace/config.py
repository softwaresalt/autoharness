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

#: Compact deterministic footer template appended so the model can request
#: the byte-equivalent original. No timestamps/mutable counters (086 risk:
#: prompt-cache fragility).
RETRIEVAL_FOOTER_TEMPLATE = (
    "\n\n[compressed by 088-F experiment; retrieve full output with "
    "output_retrieve(handle=\"{handle}\")]"
)
