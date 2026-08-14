---
title: "Spike: Plan 2 V1 framework selection under fixed security non-negotiables"
type: spike
doc_type: spike
source: docs/spikes/2026-08-14-plan2-v1-framework-spike.md
date: 2026-08-14
shipment: 130-S
feature: 121-F
task: 121.003-T
status: complete
tags:
  - plan-2
  - v1
  - framework-spike
  - gradio
  - devtunnel
---

# Spike — Plan 2 V1 Framework Selection (121.003-T)

## Purpose

`121-F`/`130-S` implement Plan 2 V1 (Observe + Steer) against the fixed
non-negotiables locked at planning: loopback-only binding, devtunnel as the
sole V1 auth mechanism, a closed structured command vocabulary (no raw
shell), no browser terminal, and a strict Observe/Steer-only remote surface
(Approve/Privileged remain local-only). This spike is the **only** task
permitted to resolve open question Q1 from
`docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md`
section 12 ("Is Gradio the right surface, or is a minimal purpose-built
control page a smaller attack surface for a fixed command vocabulary?").
No other product or security ruling from that document is revisited here.

## Candidates considered

| Candidate | Description | Loopback-only bind | Closed vocabulary only | No raw/general-purpose component | Decision |
|---|---|---|---|---|---|
| **Gradio `Blocks`** | Declarative component graph (buttons, textboxes) wired to Python callbacks; no client-side scripting surface exposed to the operator | Yes — `server_name="127.0.0.1"` is an explicit launch argument, never `0.0.0.0` | Yes — every control is a typed `gr.Button`/`gr.Textbox` bound 1:1 to a single closed-vocabulary command; there is no generic "run" input | Yes — Gradio ships no terminal/code-editor/shell component; only the fixed, hand-authored panel set in `autoharness.remote.ui` is ever rendered | **SELECTED** |
| Minimal purpose-built HTML/JS control page (hand-rolled static page + small HTTP handler) | A bespoke, single-purpose page serving only the approved Observe/Steer actions | Yes, in principle — bind choice is ours either way | Yes, in principle — we would author every element | Yes, in principle — no vendored generic UI framework at all | Rejected (see F2) |
| General-purpose web framework (Flask/FastAPI + custom frontend) | Full HTTP framework with hand-rolled routes and a custom frontend | Yes, in principle | Requires discipline — the framework itself imposes no vocabulary closure | Requires discipline — nothing prevents a future contributor from adding a raw endpoint | Rejected (see F3) |
| Full terminal-in-browser (e.g. xterm.js over a PTY bridge) | Interactive terminal emulation streamed to the browser | N/A | **No** — this is raw stdin passthrough by definition | **No** — a terminal emulator is exactly the "raw/general-purpose component" this shipment must not expose | Rejected outright (T6, permanently out of scope per `121-F` goals) |

## Findings

### F1 — Gradio's declarative component model enforces closure structurally, not by convention

`autoharness.remote.ui.OBSERVE_PANELS`/`STEER_ACTIONS` are closed, frozen
tuples exhaustive over `ObserveCommand`/`SteerCommand`
(`autoharness.remote.contracts`), and `build_gradio_app()` wires exactly
one `gr.Button` + one read-only `gr.Textbox` per spec entry — there is no
code path in the adapter that accepts an arbitrary command string or
exposes a generic input. `SurfaceSpecClosureTests`
(`tests/test_remote_ui.py`) pins this: the two closed-vocabulary
enumerations are asserted equal to `set(ObserveCommand)`/`set(SteerCommand)`
at test time, so a future accidental panel addition would fail loudly
rather than silently widening the exposed surface.

### F2 — A hand-rolled static page trades a maintained, widely-audited
component library for a bespoke HTTP/templating surface with no
corresponding reduction in the actual attack surface that matters here

The threat model in the design doc (T6/T7) cares about *what commands can
reach the supervisor and what host the listener binds to* — not about
which library renders buttons. A hand-rolled page would still need its own
request parsing, its own static-asset serving, and its own protection
against injecting a raw command through a form field; none of that is
free, and all of it would be new, unaudited surface built and maintained
by this project instead of reusing Gradio's own maintained
request-handling path. Given the actual security-relevant boundary is
enforced at the protocol layer (`autoharness.remote.contracts`,
`autoharness.remote.binding`) and not at the rendering layer, a
bespoke page would add engineering cost without closing any gap
`Blocks` leaves open.

### F3 — A general-purpose web framework (Flask/FastAPI) shifts vocabulary
closure from structural to disciplinary

Flask/FastAPI (or any general HTTP framework) impose no ceiling on what a
route can accept: a future contributor could add an arbitrary
`/exec`-shaped endpoint with nothing in the framework itself preventing
it. Gradio's `Blocks` graph has no equivalent "add any route" escape
hatch in the intended usage pattern this module exercises — every
interactive element in `autoharness.remote.ui` is declared once, in one
module, against the closed spec tuples. Choosing a general framework here
would relocate the vocabulary-closure guarantee from "the component graph
cannot represent anything else" to "no one adds a bad route," which is a
materially weaker guarantee for a remotely-reachable, credential-adjacent
surface.

### F4 — Gradio is an optional extra, never a base dependency

`pyproject.toml` declares `[project.optional-dependencies] remote =
["gradio>=6.20.0"]`. `autoharness.remote.ui` imports `gradio` lazily, only
inside `build_gradio_app()` (`GradioLazyImportTests` in
`tests/test_remote_ui.py` pins this) — the base `autoharness` install
never requires gradio, preserving the design doc's §10 deployment
guarantee that Plan 2 adds only an optional adapter over existing
services.

## Decision

**Gradio `Blocks` is selected** as the V1 UI framework, wired exclusively
through `autoharness.remote.ui.build_surface_spec()` /
`build_gradio_app()`. This satisfies every non-negotiable constraint in
this spike's scope:

* Loopback-only bind is enforced independently by
  `autoharness.remote.tunnel.validate_loopback_bind()` (Gradio's own
  `server_name` argument is set to the validated loopback host; Gradio
  does not weaken or bypass this check).
* The closed structured command vocabulary is enforced by
  `autoharness.remote.contracts.ensure_remotely_dispatchable()` before any
  UI callback reaches `SteerDispatcher`/`ObserveService` — the UI layer is
  a thin renderer over an already-closed protocol, never a second
  authority.
* No raw/general-purpose component (shell textbox, code editor, generic
  chat, terminal emulator) is ever instantiated — the panel/action specs
  are exhaustive and test-pinned.

## Explicit non-expansion of scope

This spike does not revisit or expand:

* Approve/Privileged tier exposure (remains local-only, per `121-F` DoD).
* Browser terminal streaming (permanently out of scope per `121-F` goals
  and design-doc T6).
* Application-layer identity verification beyond devtunnel's own
  authenticated access control (Q3 remains an accepted V1 risk, documented
  separately in the 121.001-T operations/security doc).
* Remote retention of session/journal data (the local journal remains the
  sole source of truth; no new persistence was introduced by this
  framework choice).

## Recommendation

Proceed with the already-implemented `autoharness.remote.ui` Gradio
adapter as the final V1 framework decision. No further framework
evaluation is required for `121-F`.
