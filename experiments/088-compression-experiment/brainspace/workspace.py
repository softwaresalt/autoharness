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


class WorkspaceContainmentError(Exception):
    """Raised when a workspace-root candidate is unrelated to the process's
    actual working directory tree (Constitution IV containment)."""


def _validate_related_to_process_cwd(candidate: str, *, source: str) -> None:
    """Reject a workspace-root candidate that shares no ancestry with the
    process's actual working directory.

    ``BRAINSPACE_WORKSPACE``/``explicit_root`` exist to PIN the same root
    across processes whose own ``os.getcwd()`` may legitimately differ (e.g.
    a session cwd inside a subdirectory of the repo), so the accepted
    relationship can point EITHER way: the candidate may be an ancestor of
    the process cwd (the common "pin the repo root while cd'd into a
    subdir" case), the process cwd may be an ancestor of the candidate (an
    explicit nested-workspace pin), or they may be identical. What must
    never be accepted is a candidate that shares no ancestry with the
    process's actual working directory at all -- that would let a
    misconfigured env var or CLI argument point the store (and therefore
    ``purge_cli --mode all``) at a completely unrelated filesystem location.
    """
    real_candidate = os.path.realpath(candidate)
    real_cwd = os.path.realpath(os.getcwd())
    try:
        common = os.path.commonpath([real_candidate, real_cwd])
    except ValueError:
        # e.g. different drives on Windows -- definitionally unrelated.
        common = None
    if common not in (real_candidate, real_cwd):
        raise WorkspaceContainmentError(
            f"{source} resolves outside the current process working "
            f"directory tree: {candidate!r} is unrelated to cwd {os.getcwd()!r}"
        )


def resolve_workspace_root(payload=None, *, explicit_root=None) -> str:
    """Resolve the workspace root the same way for every 088-F entry point.

    ``explicit_root`` (e.g. a CLI's own ``--repo-root`` argument) takes the
    HIGHEST precedence -- an operator's explicit, per-invocation intent must
    win over the ambient ``BRAINSPACE_WORKSPACE`` env pin (P-018 re-review
    finding #4, round 2), or e.g. ``purge_cli.py --mode all --repo-root X``
    could silently purge a different workspace's live rows.

    Both ``explicit_root`` and the ``BRAINSPACE_WORKSPACE`` env pin are
    validated as related to the process's actual working directory tree
    before being returned (P-018 round-3 finding #3) -- an unrelated
    candidate is rejected with ``WorkspaceContainmentError`` rather than
    silently honored.
    """
    if explicit_root:
        _validate_related_to_process_cwd(explicit_root, source="explicit_root")
        return explicit_root
    env_root = os.environ.get(config.WORKSPACE_ENV_VAR)
    if env_root:
        _validate_related_to_process_cwd(env_root, source="BRAINSPACE_WORKSPACE")
        return env_root
    if payload and payload.get("cwd"):
        return payload["cwd"]
    return os.getcwd()
