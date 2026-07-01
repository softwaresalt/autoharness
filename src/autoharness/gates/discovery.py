"""Git-diff discovery: list files modified relative to a task branch base.

Runs ``git diff --name-only <base>...<head>`` and returns forward-slash,
repo-relative paths. Degrades gracefully (empty list + warning) when git is
unavailable or the working directory is not a git repository — it never raises.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Callable

logger = logging.getLogger("autoharness.gates.discovery")

# A runner takes an argv list + cwd and returns (returncode, stdout, stderr).
Runner = Callable[[list[str], "Path | None"], "tuple[int, str, str]"]


def _default_runner(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


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
) -> list[str]:
    """Return repo-relative, forward-slash paths modified between base and head.

    Returns an empty list (and logs a warning) when git is unavailable or the
    directory is not a repository. Never raises.
    """
    run = runner or _default_runner
    argv = ["git", "diff", "--name-only", f"{base}...{head}"]
    try:
        returncode, stdout, stderr = run(argv, cwd)
    except FileNotFoundError:
        logger.warning("git executable not found; treating as no modified files discovered.")
        return []
    except OSError as exc:  # pragma: no cover - defensive
        logger.warning("git diff failed to execute (%s); no modified files discovered.", exc)
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
        return []

    return parse_diff_output(stdout)
