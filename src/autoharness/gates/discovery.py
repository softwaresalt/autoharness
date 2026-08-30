"""Git-diff discovery: list files modified relative to a task branch base.

Runs ``git diff --name-only <base>...<head>`` and returns forward-slash,
repo-relative paths. Degrades gracefully (empty list + warning) when git is
unavailable or the working directory is not a git repository — it never raises.
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Callable

logger = logging.getLogger("autoharness.gates.discovery")

# A runner takes an argv list + cwd and returns (returncode, stdout, stderr).
Runner = Callable[[list[str], "Path | None"], "tuple[int, str, str]"]
_FULL_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class InvalidGitRefError(ValueError):
    """Raised when a ref is unsafe or not a validated full commit SHA."""

    exit_code = 2


class GitDiffDiscoveryError(RuntimeError):
    """Raised when a caller opts into fail-closed diff-discovery semantics.

    ``discover_modified_files`` degrades gracefully (empty list + warning) by
    default so existing callers (e.g. ``gates/gate.py``'s ``check()``) keep
    their long-standing "no repo / unknown ref => no changes" behavior
    unchanged. Callers that instead need to distinguish "diff genuinely could
    not be computed" (e.g. unrelated histories with no merge-base for a
    triple-dot diff) from "diff succeeded with zero changed files" — where a
    silent empty list would misrepresent the former as the latter — pass
    ``raise_on_failure=True`` to opt into this exception instead.
    """


def _default_runner(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _is_full_sha(value: str) -> bool:
    return bool(_FULL_SHA_PATTERN.fullmatch(value))


def resolve_commit_ref(
    ref: str,
    *,
    cwd: Path | None = None,
    runner: Runner | None = None,
) -> str | None:
    """Resolve ``ref`` to a validated 40-char commit SHA, or ``None``.

    Uses ``git rev-parse --verify --end-of-options <ref>^{commit}`` so an
    option-like ref is never reinterpreted as a flag.
    """
    run = runner or _default_runner
    argv = ["git", "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"]
    try:
        returncode, stdout, _stderr = run(argv, cwd)
    except FileNotFoundError:
        logger.warning("git executable not found; unable to resolve commit ref %r.", ref)
        return None
    except OSError as exc:  # pragma: no cover - defensive
        logger.warning("git rev-parse failed to execute for %r (%s).", ref, exc)
        return None

    if returncode != 0:
        return None

    resolved = stdout.strip()
    return resolved if _is_full_sha(resolved) else None


def parse_diff_output(text: str) -> list[str]:
    """Parse ``git diff --name-only`` output into normalized path list.

    Splits on newlines, normalizes backslashes to forward slashes, drops empty
    lines, and de-duplicates while preserving first-seen order.
    """
    seen: set[str] = set()
    result: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip().replace("\\", "/")
        if not line or line in seen:
            continue
        seen.add(line)
        result.append(line)
    return result


def discover_modified_files(
    base: str,
    head: str = "HEAD",
    *,
    cwd: Path | None = None,
    runner: Runner | None = None,
    raise_on_failure: bool = False,
) -> list[str]:
    """Return repo-relative, forward-slash paths modified between base and head.

    ``base`` and ``head`` must already be validated full hex SHAs. By default,
    returns an empty list (and logs a warning) when git is unavailable, the
    directory is not a repository, or the diff otherwise fails to execute
    (e.g. unrelated histories with no merge-base for a triple-dot diff) —
    this is the long-standing contract relied on by existing callers. Pass
    ``raise_on_failure=True`` to instead raise :class:`GitDiffDiscoveryError`
    on any of those failure conditions, for callers that must not conflate
    "diff could not be computed" with "diff computed zero changes".
    """
    if not _is_full_sha(base) or not _is_full_sha(head):
        raise InvalidGitRefError("discover_modified_files requires validated 40-char hex SHAs")

    run = runner or _default_runner
    argv = ["git", "diff", "--name-only", "--end-of-options", f"{base}...{head}", "--"]
    try:
        returncode, stdout, stderr = run(argv, cwd)
    except FileNotFoundError as exc:
        logger.warning("git executable not found; treating as no modified files discovered.")
        if raise_on_failure:
            raise GitDiffDiscoveryError("git executable not found") from exc
        return []
    except OSError as exc:  # pragma: no cover - defensive
        logger.warning("git diff failed to execute (%s); no modified files discovered.", exc)
        if raise_on_failure:
            raise GitDiffDiscoveryError(f"git diff failed to execute: {exc}") from exc
        return []

    if returncode != 0:
        logger.warning(
            "git diff --name-only %s...%s exited %s (not a repo, or unknown ref); "
            "no modified files discovered. stderr: %s",
            base,
            head,
            returncode,
            stderr.strip(),
        )
        if raise_on_failure:
            raise GitDiffDiscoveryError(
                f"git diff --name-only {base}...{head} exited {returncode}: {stderr.strip()}"
            )
        return []

    return parse_diff_output(stdout)
