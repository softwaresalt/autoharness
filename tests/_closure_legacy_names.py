"""Test-only legacy (R2) closure filename helper (plan C6, 167-F).

The canonical builder (``build_closure_path``) can never emit an R2 name -- by
contract C2 no builder output matches R2 -- so legacy date-prefixed fixtures
cannot be builder-created. This module is the SINGLE test-side definition of
the legacy shape. It is never imported by production code and is not part of
the contract module.

The module name does not match the ``test*.py`` discovery pattern, so it is
never collected as a test module itself.
"""

from __future__ import annotations

from autoharness.gates.closure_contract import RECOGNIZED_CLOSURE_PATTERNS

_LEGACY_PATTERN = RECOGNIZED_CLOSURE_PATTERNS[1]


def legacy_closure_filename(shipment_id: str, suffix: str, *, date: str = "2026-09-11") -> str:
    """Return a legacy ``{date}-{shipment_id}-{suffix}-closure.md`` filename.

    The legacy corpus lowercases identifiers (``2026-09-11-162-s-154-f-closure.md``);
    callers pass the exact casing they want to exercise. The result is asserted
    to match R2 so a malformed fixture fails loudly rather than silently
    testing the unrecognized path.
    """
    name = f"{date}-{shipment_id}-{suffix}-closure.md"
    if _LEGACY_PATTERN.match(name) is None:
        raise ValueError(f"legacy fixture name {name!r} does not match the R2 legacy pattern")
    return name
