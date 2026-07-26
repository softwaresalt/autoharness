"""Shared workspace-root resolution (finding #12).

The hook (``hook_cli.py``) runs as a fresh subprocess per tool call and sees
the Copilot CLI session ``cwd`` in its payload. The MCP retrieval server
(``mcp_server.py``) is a long-lived process that, before this module existed,
resolved its own root independently from ``BRAINSPACE_WORKSPACE`` or its own
``os.getcwd()`` -- never from a per-call payload. If a tool runs from a
subdirectory of the repository, those two resolutions could diverge: the hook
would store under the subdirectory's store root while the server looked only
under the top-level root, so retrieval would silently miss.

Both entry points MUST call ``resolve_workspace_root`` so they agree on the
same root given the same environment/payload inputs. Precedence:

1. ``BRAINSPACE_WORKSPACE`` env var — an explicit pin. Set this when a
   session may ``cd`` into subdirectories, to guarantee hook/server
   agreement regardless of per-call ``cwd``.
2. ``payload["cwd"]`` — the Copilot CLI session cwd, when a payload is
   supplied (the hook's case).
3. ``os.getcwd()`` — the process's own working directory (the server's
   fallback when no payload/env pin is available).
"""

import os

from brainspace import config


def resolve_workspace_root(payload=None, *, explicit_root=None) -> str:
    """Resolve the workspace root the same way for every 088-F entry point.

    ``explicit_root`` (e.g. a CLI's own ``--repo-root`` argument) takes the
    HIGHEST precedence -- an operator's explicit, per-invocation intent must
    win over the ambient ``BRAINSPACE_WORKSPACE`` env pin (P-018 re-review
    finding #4, new round), or e.g. ``purge_cli.py --mode all --repo-root X``
    could silently purge a different workspace's live rows.
    """
    if explicit_root:
        return explicit_root
    env_root = os.environ.get(config.WORKSPACE_ENV_VAR)
    if env_root:
        return env_root
    if payload and payload.get("cwd"):
        return payload["cwd"]
    return os.getcwd()
