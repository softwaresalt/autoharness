"""Deterministic validation gates for autoharness.

This package implements the Phase 1 deterministic gating layer described in
``docs/design-docs/autoharness-evals-gates-design.md`` and the two companion
deliberations. It is intentionally self-contained: modules in this package MUST
NOT import install/tune modules (``verify_workspace``, ``schema_contracts``) so
gating can evolve independently (Plan Review P2-2).
"""

from __future__ import annotations
