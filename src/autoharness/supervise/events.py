"""In-process event bus with mandatory redaction-on-emit (119.004-T).

:class:`EventBus` fans out ALREADY-CONSTRUCTED event dataclass instances
(from :mod:`autoharness.supervise.contracts` -- this module does NOT define
any event type, only delivers them) to subscribers. There is exactly one
emission entry point, :meth:`EventBus.emit`, and it ALWAYS routes the
event's payload through :func:`autoharness.supervise.redact.redact_record`
before delivery. There is no public method that bypasses redaction.

**Redaction integration approach**: event dataclasses are frozen and are
neither ``Mapping`` nor ``str``, so :meth:`emit` converts the event to a
mapping via ``dataclasses.asdict``, redacts that mapping through the single
choke point (:func:`redact_record`), then reconstructs a NEW instance of the
same event type from the redacted mapping and delivers that reconstructed,
already-redacted instance to subscribers. The original, unredacted instance
is NEVER handed to a subscriber. When redaction fails closed (the payload is
unsupported or unsafe), the event is DROPPED -- not delivered to any
subscriber -- and a warning is recorded on :attr:`EventBus.warnings` for
observability; there is no raw pass-through fallback.

**H7 anti-drift enforcement (behavioral, not lexical -- F28 ruling)**:
:func:`install_no_listen_guard` installs a ``sys.addaudithook`` (once per
process -- CPython audit hooks cannot be individually removed) that hooks
the ``socket.bind`` audit event and raises :class:`ListeningSocketDetected`
whenever a socket bind is attempted while the guard's context is active.
Because ``sys.addaudithook`` hooks are permanent for the process, the
context manager itself gates enforcement via a re-entrant depth counter
rather than installing/removing the hook per use. ``socket.bind`` is the
correct audit event to hook: CPython's ``socketmodule.c`` raises it for
every call to ``socket.socket.bind`` regardless of which higher-level API
triggered it (``socket.create_server``, ``socketserver.TCPServer``,
``http.server.HTTPServer``, ``asyncio.start_server`` all eventually call
``sock.bind()`` under the hood), which is why one hook catches all four.

A fast lexical import-denylist pre-filter
(:func:`check_import_denylist`) is retained purely as a documented
SECONDARY check -- explicitly NOT the primary enforcement mechanism.
"""

from __future__ import annotations

import contextvars
import dataclasses
import sys
import uuid
from typing import Any, Callable, Iterable, Optional, Union

from autoharness.supervise.redact import Redactor, redact_record

EventPredicate = Callable[[Any], bool]
EventHandler = Callable[[Any], None]


class ListeningSocketDetected(Exception):
    """Raised by the no-listen guard when a socket bind is attempted.

    This is the behavioral (audit-hook-based) H7 anti-drift signal: it
    fires for ANY listening-socket-style bind performed while
    :func:`install_no_listen_guard`'s context is active, regardless of
    which higher-level networking API triggered it.
    """


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------


class EventBus:
    """Fans out already-constructed event instances, always through redaction.

    The public API surface is intentionally exactly three methods:
    :meth:`subscribe`, :meth:`unsubscribe`, :meth:`emit`. There is no
    ``emit_raw``/``publish_unredacted`` escape hatch.
    """

    def __init__(self, redactor: Optional[Redactor] = None) -> None:
        self._redactor = redactor
        self._subscriptions: dict[str, tuple[EventPredicate, EventHandler]] = {}
        #: Human-readable warnings recorded when an event is dropped because
        #: it could not be safely redacted. Observability only -- callers
        #: are never handed the raw dropped payload.
        self.warnings: list[str] = []

    def subscribe(self, event_type_or_predicate: Union[type, EventPredicate], handler: EventHandler) -> str:
        """Subscribe ``handler`` to events matching a type or a predicate.

        ``event_type_or_predicate`` is either a dataclass type (matched via
        ``isinstance``) or an arbitrary ``Callable[[event], bool]``
        predicate. Returns an opaque token for :meth:`unsubscribe`.
        """

        predicate: EventPredicate
        if isinstance(event_type_or_predicate, type):
            expected_type = event_type_or_predicate

            def predicate(event: Any, _expected_type: type = expected_type) -> bool:
                return isinstance(event, _expected_type)

        elif callable(event_type_or_predicate):
            predicate = event_type_or_predicate
        else:
            raise TypeError(
                "subscribe() requires a type or a callable predicate, got "
                f"{type(event_type_or_predicate)!r}"
            )

        token = uuid.uuid4().hex
        self._subscriptions[token] = (predicate, handler)
        return token

    def unsubscribe(self, token: str) -> None:
        """Remove a subscription. Idempotent: an unknown token is a no-op."""

        self._subscriptions.pop(token, None)

    def emit(self, event: Any) -> None:
        """Redact ``event`` and deliver the redacted result to subscribers.

        ``event`` MUST be an already-constructed frozen dataclass instance
        (one of the event types in
        :mod:`autoharness.supervise.contracts`). This is the SOLE emission
        entry point: every delivered event has already passed through
        :func:`redact_record`. When redaction fails closed, the event is
        dropped (never delivered) and a warning is recorded.
        """

        if not dataclasses.is_dataclass(event) or isinstance(event, type):
            raise TypeError(
                f"emit() requires an already-constructed event dataclass instance, got {type(event)!r}"
            )

        payload = dataclasses.asdict(event)
        redacted_payload, warning = redact_record(payload, self._redactor)
        if redacted_payload is None:
            self.warnings.append(warning or "event dropped: redaction failed")
            return

        try:
            redacted_event = type(event)(**redacted_payload)
        except TypeError:
            # The redacted mapping no longer matches the dataclass's own
            # constructor signature (e.g. a field was type-coerced in an
            # incompatible way). Fail closed rather than delivering a raw
            # or malformed event.
            self.warnings.append(
                f"event dropped: could not reconstruct redacted {type(event).__name__}"
            )
            return

        for predicate, handler in list(self._subscriptions.values()):
            if predicate(redacted_event):
                handler(redacted_event)


# ---------------------------------------------------------------------------
# H7 anti-drift: behavioral no-listen guard (sys.addaudithook)
# ---------------------------------------------------------------------------

# sys.addaudithook installs a PERMANENT hook for the life of the process --
# CPython provides no removal API. We install it (idempotently) exactly
# once, and gate its actual raising behavior on a re-entrant depth counter
# so install_no_listen_guard() can be used as a per-test context manager
# without leaking a hard-installed hook's effect outside its own scope.
_guard_depth: contextvars.ContextVar[int] = contextvars.ContextVar(
    "autoharness_supervise_no_listen_guard_depth", default=0
)
_hook_installed = False

# Audit events that indicate a listening-socket-style bind. socket.bind is
# raised by CPython's socketmodule.c for every socket.socket.bind() call,
# which is the common underlying primitive for socket.create_server,
# socketserver.TCPServer, http.server.HTTPServer, and asyncio.start_server.
_GUARDED_AUDIT_EVENTS = frozenset({"socket.bind"})


def _audit_hook(event_name: str, args: tuple[Any, ...]) -> None:
    if event_name not in _GUARDED_AUDIT_EVENTS:
        return
    if _guard_depth.get() <= 0:
        return
    raise ListeningSocketDetected(
        f"listening socket operation detected while the no-listen guard was active: "
        f"{event_name} args={args!r}"
    )


class _NoListenGuardContext:
    """Re-entrant context manager gating the permanent audit hook's raising."""

    def __enter__(self) -> "_NoListenGuardContext":
        self._token = _guard_depth.set(_guard_depth.get() + 1)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        _guard_depth.reset(self._token)


def install_no_listen_guard() -> _NoListenGuardContext:
    """Activate the H7 no-listen guard for the duration of a ``with`` block.

    Installs the underlying ``sys.addaudithook`` at most once per process
    (idempotent -- audit hooks cannot be removed). Returns a context manager;
    only bind attempts made WHILE that context is active raise
    :class:`ListeningSocketDetected`. Usable by both tests and production
    code that wants to self-check a code region for accidental listening
    sockets.
    """

    global _hook_installed
    if not _hook_installed:
        sys.addaudithook(_audit_hook)
        _hook_installed = True
    return _NoListenGuardContext()


# ---------------------------------------------------------------------------
# Secondary, documented-only lexical import denylist
# ---------------------------------------------------------------------------

# NOT the primary enforcement mechanism (see module docstring) -- a fast,
# purely lexical pre-filter for well-known server-framework/tunnel package
# names. The audit-hook guard above is what actually proves absence of
# listening sockets.
_DENYLISTED_MODULE_NAMES = frozenset({"gradio", "fastapi", "flask", "uvicorn", "aiohttp"})


def check_import_denylist(module_names: Iterable[str]) -> list[str]:
    """Return the subset of ``module_names`` matching the lexical denylist.

    Matches exact names in :data:`_DENYLISTED_MODULE_NAMES`
    (case-insensitive) plus any name containing the substring
    ``"devtunnel"`` (case-insensitive), covering the various
    devtunnel-client package name shapes.
    """

    violations: list[str] = []
    for name in module_names:
        lowered = name.lower()
        if lowered in _DENYLISTED_MODULE_NAMES or "devtunnel" in lowered:
            violations.append(name)
    return violations
