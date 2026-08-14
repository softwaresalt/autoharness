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

from dataclasses import dataclass
from typing import Callable

from autoharness.remote.contracts import ObserveCommand, SteerCommand


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
                fn=lambda command=panel.command: dispatch_observe(command),
                outputs=output,
            )
        for action in STEER_ACTIONS:
            button = gr.Button(action.label)
            output = gr.Textbox(label=action.label, interactive=False)
            button.click(
                fn=lambda command=action.command: dispatch_steer(command),
                outputs=output,
            )

    return app
