"""Supervisor core contracts (118-F).

This package hosts the pure, I/O-free contract modules that a future
supervisor CLI adapter builds on: a typed result envelope
(:mod:`autoharness.supervise.result`), an error taxonomy with a
machine-readable exit-code contract (:mod:`autoharness.supervise.errors`),
the stable event/approval/gated-action catalog
(:mod:`autoharness.supervise.contracts`), the single secret-redaction choke
point (:mod:`autoharness.supervise.redact`), and the atomic single-session
guard lock (:mod:`autoharness.supervise.locking`).

Nothing in this package changes the observable behavior of any existing
production surface (``start.ps1``/``start.sh`` are untouched); it is a wholly
new, additive module tree.
"""

from __future__ import annotations
