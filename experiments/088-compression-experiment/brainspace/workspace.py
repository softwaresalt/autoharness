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
   supplied (the hook's case). Validated as related to the process's
   actual working directory tree, same as ``explicit_root``/env pin (a
   crafted or stale payload cwd must never point the store outside the
   workspace).
3. ``os.getcwd()`` — the process's own working directory (the server's
   fallback when no payload/env pin is available).
"""

import os

from brainspace import config


class WorkspaceContainmentError(Exception):
    """Raised when a workspace-root candidate is unrelated to the process's
    actual working directory tree (Constitution IV containment)."""


def _discover_repo_root(start: str):
    """Walk upward from ``start`` looking for a repository marker (``.git``).

    Returns the marker's containing directory, or ``None`` if no marker is
    found anywhere between ``start`` and the filesystem root. ``.git`` may be
    a directory (ordinary clone) or a file (worktree/submodule pointer);
    ``os.path.exists`` covers both.
    """
    current = os.path.realpath(start)
    while True:
        if os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _is_ancestor_or_equal(ancestor: str, path: str) -> bool:
    try:
        return os.path.commonpath([ancestor, path]) == ancestor
    except ValueError:
        # e.g. different drives on Windows -- definitionally unrelated.
        return False


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

    A candidate that is a proper ANCESTOR of cwd is additionally bounded to
    a discovered repository root (P-018 round-7 finding): accepting ANY
    ancestor purely because ``commonpath(candidate, cwd) == candidate`` lets
    a misconfigured env pin or a crafted/stale payload cwd point the store at
    an arbitrarily broad, unrelated parent -- e.g. ``/`` or ``/home`` -- just
    because it is technically an ancestor of the real cwd. Only ancestors at
    or below the nearest discoverable ``.git`` boundary (walking up from the
    real cwd) are trusted; a descendant-of-cwd candidate (the reverse,
    nested-workspace-pin relationship) carries no such risk and needs no
    repo-root bound, since it can never be broader than cwd itself.
    """
    real_candidate = os.path.realpath(candidate)
    real_cwd = os.path.realpath(os.getcwd())

    if real_candidate == real_cwd:
        return
    if _is_ancestor_or_equal(real_cwd, real_candidate):
        # candidate is a descendant of cwd -- narrower than cwd, no escape risk.
        return
    if _is_ancestor_or_equal(real_candidate, real_cwd):
        # candidate is a proper ancestor of cwd -- only trust it up to the
        # discovered repository root, never unbounded ancestry.
        repo_root = _discover_repo_root(real_cwd)
        if repo_root is not None and _is_ancestor_or_equal(repo_root, real_candidate):
            return
        raise WorkspaceContainmentError(
            f"{source} is an ancestor of the current working directory but "
            f"is not bounded by a discoverable repository root: {candidate!r} "
            f"is too broad relative to cwd {os.getcwd()!r}"
        )
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

    ``explicit_root`` is checked with ``is not None`` rather than truthiness:
    an *explicitly supplied* empty string (e.g. a CLI's ``--repo-root ""``)
    must never be treated as "not supplied" and silently fall through to the
    ambient env pin -- that would let a malformed explicit argument change
    which workspace's rows a command like ``purge_cli --mode all`` acts on
    (P-018 round-3 follow-up finding). An empty explicit root is rejected
    outright since it can never be a valid, containment-checkable path.
    """
    if explicit_root is not None:
        if not explicit_root.strip():
            raise WorkspaceContainmentError(
                "explicit_root was supplied but is empty; refusing to fall "
                "back to an ambient BRAINSPACE_WORKSPACE pin for an "
                "explicitly-provided (if malformed) argument"
            )
        _validate_related_to_process_cwd(explicit_root, source="explicit_root")
        return explicit_root
    env_root = os.environ.get(config.WORKSPACE_ENV_VAR)
    if env_root:
        _validate_related_to_process_cwd(env_root, source="BRAINSPACE_WORKSPACE")
        return env_root
    if payload and isinstance(payload, dict) and payload.get("cwd"):
        payload_cwd = payload["cwd"]
        # P-018 round-3 follow-up finding: this branch previously returned
        # payload["cwd"] verbatim with NO containment check, so a crafted or
        # stale hook payload could point the store at an arbitrary absolute
        # path unrelated to the process's actual working directory tree.
        # Callers that cannot tolerate this validation (e.g. an unhandled
        # WorkspaceContainmentError) must fail safe -- see hook_cli.py.
        #
        # ``isinstance(payload, dict)`` (P-018 final-convergence follow-up
        # finding): a syntactically valid JSON payload is not guaranteed to
        # decode to an object -- a non-empty JSON array such as ``["cwd"]``
        # is truthy but has no ``.get()``, so ``payload.get("cwd")`` would
        # raise ``AttributeError`` here and crash the hook mid-resolution
        # instead of emitting its required fail-safe ``{}`` passthrough.
        #
        # 089.001-T: ``payload["cwd"]`` itself is not guaranteed to be a
        # string even when the outer payload is a well-formed dict -- a
        # crafted or stale payload could carry a truthy non-string value
        # (e.g. a list). ``os.path.realpath()`` raises a bare ``TypeError``
        # for a non-str/bytes/PathLike argument, which would crash the hook
        # instead of the required fail-safe ``WorkspaceContainmentError`` ->
        # ``{}`` passthrough contract, so this must be rejected before it
        # ever reaches ``_validate_related_to_process_cwd``.
        if not isinstance(payload_cwd, str):
            raise WorkspaceContainmentError(
                f"payload cwd must be a string, got {type(payload_cwd).__name__!r}: "
                f"{payload_cwd!r}"
            )
        _validate_related_to_process_cwd(payload_cwd, source="payload cwd")
        return payload_cwd
    return os.getcwd()
