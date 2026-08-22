"""GIT_CONFIG_* self-consistency normalizer (144.005-T).

Deliverable per plan Task 5 / hardening A1, A7, A7R, R4 (BINDING). Flat
module directly under ``tests/`` (A1/R4 -- no new package). Operates ONLY on
the ``GIT_CONFIG_COUNT`` / ``GIT_CONFIG_KEY_<n>`` / ``GIT_CONFIG_VALUE_<n>``
injection triple, matched by EXACT name shape with an integer suffix (A7).
Git has a SECOND, unrelated injection channel
(``GIT_CONFIG_PARAMETERS``/``GIT_CONFIG_GLOBAL``/``GIT_CONFIG_SYSTEM``/
``GIT_CONFIG_NOSYSTEM``/any other ``GIT_CONFIG*`` name) that this module
NEVER touches -- a prefix match on ``GIT_CONFIG*`` would silently disable
those.
"""

from __future__ import annotations

import os
from typing import Mapping

_COUNT_KEY = "GIT_CONFIG_COUNT"


def _key_name(n: int) -> str:
    return f"GIT_CONFIG_KEY_{n}"


def _value_name(n: int) -> str:
    return f"GIT_CONFIG_VALUE_{n}"


def consistent_git_env(base: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return an environment mapping whose ``GIT_CONFIG_*`` triple is
    self-consistent: only ``(KEY_n, VALUE_n)`` pairs where BOTH are present
    are kept (A7R -- symmetric: dropped iff either name is ABSENT; empty is
    NOT absent), survivors are renumbered contiguously from 0 preserving
    original relative order, and ``GIT_CONFIG_COUNT`` is set to the
    surviving count. Every other variable -- including the second,
    unrelated ``GIT_CONFIG*`` injection channel -- passes through
    unchanged. Never mutates ``os.environ`` (purity).

    If ``GIT_CONFIG_COUNT`` is absent entirely, or present but malformed
    (non-integer, or a negative integer), the mapping is returned unchanged
    for git itself to reject or ignore (A7: never invent, default, or
    repair a malformed count).
    """
    source: dict[str, str] = dict(os.environ) if base is None else dict(base)

    count_raw = source.get(_COUNT_KEY)
    if count_raw is None:
        return source

    try:
        count = int(count_raw)
    except ValueError:
        return source
    if count < 0:
        return source

    survivors: list[tuple[str, str]] = []
    any_dropped = False
    for n in range(count):
        key_val = source.get(_key_name(n))
        value_val = source.get(_value_name(n))
        if key_val is None or value_val is None:
            any_dropped = True
            continue
        survivors.append((key_val, value_val))

    if not any_dropped:
        # Provable no-op (property 3): identical content AND identical key
        # ordering, because it IS the same mapping, merely copied.
        return source

    result = dict(source)
    for n in range(count):
        result.pop(_key_name(n), None)
        result.pop(_value_name(n), None)
    for new_n, (key_val, value_val) in enumerate(survivors):
        result[_key_name(new_n)] = key_val
        result[_value_name(new_n)] = value_val
    result[_COUNT_KEY] = str(len(survivors))
    return result
