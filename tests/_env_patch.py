"""Restore-by-diff environment patching helper (144.002-T).

Deliverable per plan Task 2 / hardening A1, A4, A5, R4, R9 (BINDING). This
module is a FLAT module directly under ``tests/`` -- NOT a ``tests/support/``
package -- per A1/R4 (the original plan text said
``tests/support/env_patch.py``; A1/R4 supersede it). It contains NO
``tests/__init__.py``/``tests/conftest.py`` companion; the module name does
not match the ``test*.py`` discovery pattern, so it is never collected as a
test module itself.

``patched_environ`` is the mechanism-A root fix: unlike
``unittest.mock.patch.dict(os.environ, ...)``, which captures and restores
the ENTIRE ``os.environ`` mapping on exit (via ``os.environ.clear()`` +
``os.environ.update(original)``), this helper touches ONLY the keys named in
its own ``overrides`` and restores ONLY those keys by targeted diff. It never
calls ``os.environ.clear()``, so every variable this call did not touch is
never removed and re-added -- and therefore never destroyed by the Win32
``SetEnvironmentVariableW(name, "")`` empty-value-deletes semantics that
``os.environ[name] = ""`` would otherwise trigger on restore.
"""

from __future__ import annotations

import contextlib
import os
from typing import Iterator


@contextlib.contextmanager
def patched_environ(**overrides: "str | None") -> Iterator[None]:
    """Set/delete only the named keys; restore only those keys on exit.

    A value of ``None`` deletes the key for the duration of the block. A
    string value sets the key to that value for the duration of the block.
    Restoration is by targeted diff: keys absent before the block are
    deleted on exit, keys present before the block are re-set to their
    prior value on exit. ``os.environ.clear()`` is NEVER called, so
    untouched variables are never removed and re-added and therefore never
    destroyed by the Win32 empty-value-delete behavior.

    Raises:
        ValueError: if any override value is the empty string ``""``, on
            EVERY platform (A4, BINDING) -- ``patched_environ(X="")`` would
            itself invoke the exact Win32 empty-value delete this helper
            exists to avoid, producing a helper correct on Linux and broken
            on Windows. Raised before any mutation.
        RuntimeError: if any key about to be touched currently holds an
            empty-string value (A5, BINDING) -- exactly
            ``GIT_CONFIG_VALUE_2``'s shape. Faithful restore is impossible
            on Windows in that case (the restore path would itself
            reintroduce the defect), so entry fails closed, before any
            mutation, naming the offending key.
    """
    # A4 (BINDING): reject empty-string overrides uniformly, before any
    # mutation, on every platform (no platform branch).
    for key, value in overrides.items():
        if value == "":
            raise ValueError(
                f"patched_environ() override for {key!r} is the empty "
                f"string; pass None to delete the key, or a non-empty "
                f"string to set it. An empty-string override would itself "
                f"invoke the Win32 empty-value-delete behavior this helper "
                f"exists to avoid."
            )

    # A5 (BINDING): fail closed at ENTRY if any key about to be touched
    # currently holds an empty-string value. Entry-time failure means
    # nothing is mutated yet -- no torn state. Inspect ALL prior values
    # before performing ANY mutation below.
    prior: dict[str, str | None] = {}
    for key in overrides:
        current = os.environ.get(key)
        if current == "":
            raise RuntimeError(
                f"patched_environ() cannot safely touch {key!r}: its "
                f"current value is the empty string, and restoring an "
                f"empty-string value via os.environ[key] = '' would itself "
                f"trigger Windows' SetEnvironmentVariableW empty-value-"
                f"delete behavior, reintroducing the defect through this "
                f"helper's own restore path."
            )
        prior[key] = current

    # Mutation phase: only the named keys, no clear().
    for key, value in overrides.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    try:
        yield
    finally:
        # Restoration by targeted diff: keys absent before are deleted,
        # keys present before are re-set to their prior value. No
        # os.environ.clear() anywhere in this module.
        for key, previous_value in prior.items():
            if previous_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous_value
