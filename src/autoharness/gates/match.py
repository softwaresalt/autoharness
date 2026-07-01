"""Doublestar glob matching over forward-slash-normalized paths.

Resolves design-doc §6.2 at the match layer: discovered paths are normalized to
forward-slash form before matching, and case sensitivity follows the host
filesystem (sensitive on POSIX, insensitive on Windows) unless overridden.

Uses only the standard library (a small glob→regex translator) to avoid adding
a dependency.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache


def normalize_path(path: str) -> str:
    """Normalize a path to forward-slash form, collapsing backslashes."""
    return path.replace("\\", "/")


@lru_cache(maxsize=512)
def translate_glob(pattern: str) -> str:
    """Translate a doublestar glob into an anchored regular expression.

    Semantics:
      * ``**`` matches any number of path segments, including zero (crosses ``/``).
      * ``*`` matches any run of characters within a single segment (not ``/``).
      * ``?`` matches a single character that is not ``/``.
    """
    pattern = normalize_path(pattern)
    out: list[str] = ["^"]
    i = 0
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                j = i + 2
                if j < n and pattern[j] == "/":
                    # "**/" matches zero or more leading segments.
                    out.append("(?:[^/]*/)*")
                    i = j + 1
                    continue
                # "**" at end or fused with more text: match across separators.
                out.append(".*")
                i = j
                continue
            out.append("[^/]*")
            i += 1
            continue
        if c == "?":
            out.append("[^/]")
            i += 1
            continue
        if c == "/":
            out.append("/")
            i += 1
            continue
        out.append(re.escape(c))
        i += 1
    out.append("$")
    return "".join(out)


def _default_case_sensitive() -> bool:
    return os.name != "nt"


def path_matches(pattern: str, path: str, *, case_sensitive: bool | None = None) -> bool:
    """Return True when ``path`` matches the doublestar ``pattern``.

    Both pattern and path are normalized to forward-slash form first.
    """
    if case_sensitive is None:
        case_sensitive = _default_case_sensitive()
    flags = 0 if case_sensitive else re.IGNORECASE
    regex = re.compile(translate_glob(pattern), flags)
    return regex.match(normalize_path(path)) is not None


def filter_matching(
    pattern: str,
    paths: "list[str]",
    *,
    case_sensitive: bool | None = None,
) -> "list[str]":
    """Return the subset of ``paths`` that match ``pattern`` (order preserved)."""
    return [p for p in paths if path_matches(pattern, p, case_sensitive=case_sensitive)]
