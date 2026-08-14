"""Production composition for the Plan 2 V1 remote control plane.

The control plane is an adapter around the existing supervisor objects. It
does not own session state, journal retention, or a second execution loop.
Gradio callbacks forward caller-supplied, workspace/session-bound request
envelopes to the Observe and Steer services.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable, Mapping

from autoharness.remote.binding import (
    WorkspaceSessionBinding,
    generate_binding_secret,
)
from autoharness.remote.contracts import (
    RemoteResponse,
    decode_request,
)
from autoharness.remote.observe import BoundedOutputTail, ObserveService
from autoharness.remote.rate_limit import TokenBucketRateLimiter
from autoharness.remote.steer import SteerDispatcher
from autoharness.remote.tunnel import (
    SubprocessTunnelProcess,
    TunnelLifecycle,
    build_devtunnel_argv,
    resolve_devtunnel_executable,
)
from autoharness.remote.ui import build_gradio_app, launch_gradio_app
from autoharness.supervise.events import EventBus
from autoharness.supervise.session import SessionStateMachine


class RemoteControlPlane:
    """Own the authenticated UI/tunnel lifecycle for one supervisor session."""

    def __init__(
        self,
        *,
        state_machine: SessionStateMachine,
        journal: object,
        event_bus: EventBus,
        local_channel: object,
        binding: WorkspaceSessionBinding,
        observe: ObserveService,
        steer: SteerDispatcher,
        tunnel: TunnelLifecycle,
        bind_host: str,
        port: int,
    ) -> None:
        self.state_machine = state_machine
        self.binding = binding
        self.observe = observe
        self.steer = steer
        self.tunnel = tunnel
        self.bind_host = bind_host
        self.port = port
        self._event_bus = event_bus
        self._local_channel = local_channel
        self._app: object | None = None
        self.started = False

    @classmethod
    def create(
        cls,
        *,
        workspace_root: Path,
        session_id: str,
        state_machine: SessionStateMachine,
        journal: object,
        event_bus: EventBus,
        local_channel: object,
        on_pause: Callable[[], object] | None = None,
        on_resume: Callable[[], object] | None = None,
        on_cancel: Callable[[], object] | None = None,
        emit: Callable[[object], int | None] | None = None,
        on_tunnel_loss: Callable[[], None] | None = None,
        bind_host: str = "127.0.0.1",
        port: int = 7860,
        secret: bytes | None = None,
    ) -> "RemoteControlPlane":
        if port < 1 or port > 65535:
            raise ValueError("remote control-plane port must be between 1 and 65535")
        binding = WorkspaceSessionBinding(
            workspace_root=str(workspace_root),
            session_id=session_id,
            secret=generate_binding_secret() if secret is None else secret,
        )
        rate_limiter = TokenBucketRateLimiter()
        output_tail = BoundedOutputTail(capacity=200)
        observe = ObserveService(
            state_machine=state_machine,
            journal=journal,
            output_tail=output_tail,
            binding=binding,
            rate_limiter=rate_limiter,
        )
        observe.attach(event_bus)
        steer = SteerDispatcher(
            state_machine=state_machine,
            local_channel=local_channel,
            journal=journal,
            binding=binding,
            rate_limiter=rate_limiter,
            on_pause=on_pause,
            on_resume=on_resume,
            on_cancel=on_cancel,
            emit=emit,
        )
        executable = resolve_devtunnel_executable()
        argv = build_devtunnel_argv(executable, port)
        tunnel = TunnelLifecycle(
            bind_host=bind_host,
            process_factory=lambda: SubprocessTunnelProcess(argv),
            on_loss=on_tunnel_loss,
        )
        return cls(
            state_machine=state_machine,
            journal=journal,
            event_bus=event_bus,
            local_channel=local_channel,
            binding=binding,
            observe=observe,
            steer=steer,
            tunnel=tunnel,
            bind_host=bind_host,
            port=port,
        )

    @property
    def token(self) -> str:
        """Return the session-scoped token for the authenticated devtunnel UI."""

        return self.binding.issue_token()

    def dispatch_observe(self, payload: bytes | str | Mapping[str, object]) -> RemoteResponse:
        request = decode_request(_encode_request_payload(payload))
        return self.observe.handle(request, self.token, now=time.time())

    def dispatch_steer(self, payload: bytes | str | Mapping[str, object]) -> RemoteResponse:
        request = decode_request(_encode_request_payload(payload))
        return self.steer.dispatch(request, self.token, now=time.time())

    def start(self) -> None:
        if self.started:
            return
        self._app = build_gradio_app(
            dispatch_observe=self.dispatch_observe,
            dispatch_steer=self.dispatch_steer,
        )
        launch_gradio_app(
            self._app,
            bind_host=self.bind_host,
            server_port=self.port,
            share=False,
            prevent_thread_lock=True,
        )
        self.tunnel.start()
        self.started = True

    def stop(self) -> None:
        self.tunnel.teardown()
        self.started = False

__all__ = ["RemoteControlPlane"]


def _encode_request_payload(payload: bytes | str | Mapping[str, object]) -> bytes:
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    if isinstance(payload, Mapping):
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")
    raise TypeError(
        "remote request payload must be bytes, JSON text, or a JSON object mapping"
    )
