"""Plan 2 V1 remote control-plane package.

This package is the implementation of Plan 2 V1: a single, combined
Observe + Steer remote control surface layered ON TOP OF the local Copilot
CLI supervisor (:mod:`autoharness.supervise`) rather than a rewrite or
parallel authority path. Grounded in
``docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md``
and the Plan 1 event/journal seams (``events.py``, ``journal.py``).

Hard V1 boundaries enforced across every module in this package:

* Only the ``OBSERVE`` and ``STEER`` authority tiers are ever remotely
  reachable. ``APPROVE`` and ``PRIVILEGED`` actions (``session_restart``,
  ``force_unlock``) remain LOCAL-ONLY -- see :mod:`autoharness.remote.contracts`.
* Every remote command is drawn from a small, closed, structured
  vocabulary (:class:`~autoharness.remote.contracts.ObserveCommand`,
  :class:`~autoharness.remote.contracts.SteerCommand`). There is no raw
  shell, no general-purpose component, and no browser terminal streaming
  anywhere in this package -- that surface is permanently out of scope.
* Every request must be cryptographically bound to a specific
  ``(workspace_root, session_id)`` pair (:mod:`autoharness.remote.binding`)
  and pass a token-bucket rate limit
  (:mod:`autoharness.remote.rate_limit`, 30 requests/min, burst 5) before
  it can touch any local supervisor seam.
* The local session journal remains the sole source of truth. Remote
  Observe clients are stateless readers; this package introduces no
  second remote retention store.
* Plan 2 is independent of Plan 1: nothing in this package modifies
  :mod:`autoharness.supervise` behavior, and Plan 1 never imports Plan 2.
"""

from __future__ import annotations
