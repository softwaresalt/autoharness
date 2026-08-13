"""Local console-only structured command + approval channel (120.005-T).

Implements the request/response contract already defined in
``contracts.py`` (``ApprovalRequested``/``ApprovalResolved``) for the two
gated actions in :data:`autoharness.supervise.contracts.GATED_ACTION_CATALOG`
(``session_restart``, ``force_unlock``).

:class:`ConsoleApprovalService` is CONSTRUCTIBLE and INJECTABLE -- no
import-time singleton, no module-level mutable default. It never opens any
socket/port/HTTP/tunnel of any kind (verified in
``tests/test_supervise_approvals.py`` by wrapping calls in
:func:`autoharness.supervise.events.install_no_listen_guard`, reusing the
SAME H7 behavioral guard rather than reinventing one here).

**Fail-closed contract (H2)**: an unregistered/unknown gated-action
identifier raises :class:`~autoharness.supervise.contracts.UnknownGatedActionError`,
propagated verbatim -- never caught-and-defaulted. When ``interactive`` is
``False``, or the operator's input does not match one of the action's
declared ``options`` (interactive fail-closed re-routing), the resolution
falls back to the action's declared :class:`~autoharness.supervise.contracts.FallbackPolicy`:
``UseSafeDefault`` resolves to its ``reference_or_value``; ``Refuse``
resolves to the literal string ``"REFUSED"``. This service NEVER silently
auto-approves a gated action.

Interactive-mode ``timeout`` is documented as an ADVISORY, best-effort
limitation: Python's builtin ``input()`` has no reliable cross-platform
timeout mechanism, so this module does not attempt to enforce one; the
hard, always-tested H2 contract is the NON-interactive fallback path
above, not an interactive timeout.
"""

from __future__ import annotations

from typing import Callable, Optional

from autoharness.supervise.contracts import (
    ApprovalResolved,
    Refuse,
    UseSafeDefault,
    get_gated_action,
)

_STRUCTURED_COMMANDS = frozenset({"status", "pause", "resume", "cancel"})


class ConsoleApprovalService:
    """Console-only approval + minimal structured local command channel.

    No constructor arguments are required -- every method takes its own
    injectable ``input_fn``/``output_fn`` so tests never touch real stdio.
    """

    def request_approval(
        self,
        identifier: str,
        *,
        interactive: bool = True,
        input_fn: Callable[..., str] = input,
        output_fn: Callable[..., None] = print,
        timeout: Optional[float] = None,
    ) -> ApprovalResolved:
        """Request approval for the gated action ``identifier``.

        Raises :class:`~autoharness.supervise.contracts.UnknownGatedActionError`
        for an unregistered identifier -- this propagates unchanged, it is
        never caught and defaulted here.
        """

        spec = get_gated_action(identifier)  # fail closed: let this propagate.

        if interactive:
            output_fn(spec.summary)
            output_fn(f"Options: {', '.join(spec.options)}")
            output_fn(f"Fallback if unresolved: {spec.fallback_policy.describe()}")
            choice = input_fn("> ")
            if choice in spec.options:
                return ApprovalResolved(kind=identifier, resolution=choice, resolved_by="operator")
            # Unrecognized operator input fails closed to the declared
            # fallback policy rather than re-prompting indefinitely or
            # silently proceeding with an unrecognized value.
            return ApprovalResolved(
                kind=identifier,
                resolution=_fallback_resolution(spec.fallback_policy),
                resolved_by="fallback_policy_unrecognized_input",
            )

        # Non-interactive (or advisory-timeout) path: always resolve via the
        # catalog's declared fallback policy. Never auto-approve.
        return ApprovalResolved(
            kind=identifier,
            resolution=_fallback_resolution(spec.fallback_policy),
            resolved_by="fallback_policy",
        )

    def handle_command(self, command: str) -> str:
        """Route a minimal structured local command over the same console channel.

        This is intentionally minimal/pragmatic: the load-bearing acceptance
        criterion for this module is the approval fail-closed contract
        above, not a full REPL. Unknown commands return a descriptive
        string rather than raising.
        """

        if command not in _STRUCTURED_COMMANDS:
            return f"unknown command: {command!r}"
        return f"{command}: acknowledged"


def _fallback_resolution(fallback_policy: object) -> str:
    """Resolve a :class:`~autoharness.supervise.contracts.FallbackPolicy` variant.

    ``UseSafeDefault`` resolves to its declared ``reference_or_value``;
    ``Refuse`` resolves to the literal string ``"REFUSED"``. Every entry in
    :data:`~autoharness.supervise.contracts.GATED_ACTION_CATALOG` is
    guaranteed (by ``GatedActionSpec.__post_init__``) to declare exactly one
    of these two variants, so no other branch is reachable here.
    """

    if isinstance(fallback_policy, UseSafeDefault):
        return fallback_policy.reference_or_value
    if isinstance(fallback_policy, Refuse):
        return "REFUSED"
    raise TypeError(  # pragma: no cover - defensive: catalog invariant guards this
        f"unrecognized FallbackPolicy variant: {fallback_policy!r}"
    )
