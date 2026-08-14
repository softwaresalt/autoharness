"""Plan 2 V1 constrained control-surface wiring (121.007-T).

This module defines the CLOSED set of Observe panels and Steer actions the
Gradio UI is ever allowed to expose, and the (lazy-import) adapter that
wires those specs to a real ``gradio.Blocks`` app.

Two invariants matter more than anything else here:

1. ``OBSERVE_PANELS``/``STEER_ACTIONS`` are exhaustive over
   :class:`autoharness.remote.contracts.ObserveCommand` /
   :class:`autoharness.remote.contracts.SteerCommand` -- nothing more,
   nothing less. There is no raw shell textbox, code editor, or
   general-purpose chat surface anywhere in this module (T7: no browser
   terminal, closed command vocabulary only).
2. ``gradio`` is an OPTIONAL extra (``autoharness[remote]``). Importing
   this module must never require gradio to be installed -- the import is
   deferred to inside :func:`build_gradio_app` so the base install stays
   gradio-free.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from typing import Callable, Mapping, Protocol

from autoharness.remote.contracts import ObserveCommand, SteerCommand
from autoharness.remote.errors import RemoteError
from autoharness.remote.tunnel import NonLoopbackBindError, validate_loopback_bind


@dataclass(frozen=True)
class ObservePanelSpec:
    """A single closed-vocabulary Observe panel."""

    command: ObserveCommand
    label: str


@dataclass(frozen=True)
class SteerActionSpec:
    """A single closed-vocabulary Steer action.

    ``confirm`` marks actions that require an explicit UI confirmation
    step before dispatch -- CANCEL is the only V1 action that requires
    this, since it is destructive to the running session.
    """

    command: SteerCommand
    label: str
    confirm: bool = False


# Exhaustive over ObserveCommand -- see SurfaceSpecClosureTests for the
# enforced closure check.
OBSERVE_PANELS: tuple[ObservePanelSpec, ...] = (
    ObservePanelSpec(ObserveCommand.STATUS, "Status"),
    ObservePanelSpec(ObserveCommand.PHASE, "Phase"),
    ObservePanelSpec(ObserveCommand.PROGRESS, "Progress"),
    ObservePanelSpec(ObserveCommand.OUTPUT_TAIL, "Output Tail"),
    ObservePanelSpec(ObserveCommand.JOURNAL_TAIL, "Journal Tail"),
)

# Exhaustive over SteerCommand -- see SurfaceSpecClosureTests for the
# enforced closure check.
STEER_ACTIONS: tuple[SteerActionSpec, ...] = (
    SteerActionSpec(SteerCommand.PAUSE, "Pause"),
    SteerActionSpec(SteerCommand.RESUME, "Resume"),
    SteerActionSpec(SteerCommand.CANCEL, "Cancel", confirm=True),
    SteerActionSpec(SteerCommand.REQUEST_CHECKPOINT, "Request Checkpoint"),
)


class _Launchable(Protocol):
    def launch(self, *, server_name: str, **kwargs: object) -> object: ...


def validate_gradio_bind(host: str) -> None:
    """Enforce the same loopback-only rule at the UI launch boundary."""

    try:
        validate_loopback_bind(host)
    except NonLoopbackBindError as exc:
        raise ValueError(str(exc)) from exc


def render_callback_result(result: object) -> str:
    """Render protocol results/errors without flattening their structure."""

    if isinstance(result, RemoteError):
        value: object = {
            "ok": False,
            "error": {
                "kind": result.kind.value,
                "exit_code": result.exit_code,
                "message": str(result),
            },
        }
    else:
        value = _json_ready(result)
        if value is result:
            return str(result)
    return json.dumps(value, sort_keys=True, default=str)


def _json_ready(value: object) -> object:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def build_surface_spec() -> dict[str, tuple[object, ...]]:
    """Return the closed Observe/Steer surface spec as a plain mapping."""

    return {"observe": OBSERVE_PANELS, "steer": STEER_ACTIONS}


def build_gradio_app(
    *,
    dispatch_observe: Callable[[ObserveCommand], object],
    dispatch_steer: Callable[[SteerCommand], object],
):
    """Wire :data:`OBSERVE_PANELS`/:data:`STEER_ACTIONS` into a gradio app.

    ``gradio`` is imported LAZILY here (never at module scope) so the base
    ``autoharness`` install never requires the optional ``remote`` extra.

    Raises:
        ImportError: gradio is not installed. The error message points at
            the ``autoharness[remote]`` extra so the fix is actionable.
    """

    try:
        import gradio as gr
    except ImportError as exc:
        raise ImportError(
            "gradio is required to build the Plan 2 remote control-plane UI; "
            "install it with the optional 'remote' extra: pip install autoharness[remote]"
        ) from exc

    with gr.Blocks() as app:
        for panel in OBSERVE_PANELS:
            button = gr.Button(panel.label)
            output = gr.Textbox(label=panel.label, interactive=False)
            button.click(
                fn=lambda command=panel.command: _dispatch_and_render(dispatch_observe, command),
                outputs=output,
            )
        for action in STEER_ACTIONS:
            button = gr.Button(action.label)
            output = gr.Textbox(label=action.label, interactive=False)
            button.click(
                fn=lambda command=action.command: _dispatch_and_render(dispatch_steer, command),
                outputs=output,
            )

    return app


def _dispatch_and_render(dispatch: Callable[[object], object], command: object) -> str:
    try:
        return render_callback_result(dispatch(command))
    except RemoteError as exc:
        return render_callback_result(exc)


def launch_gradio_app(
    app: _Launchable, *, bind_host: str = "127.0.0.1", **kwargs: object
) -> object:
    """Launch a built app only after validating its loopback bind host."""

    validate_gradio_bind(bind_host)
    if "server_name" in kwargs:
        raise ValueError("server_name is controlled by the loopback-only bind boundary")
    return app.launch(server_name=bind_host, **kwargs)
