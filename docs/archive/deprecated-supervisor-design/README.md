---
title: "Deprecated — Local Copilot CLI Supervisor design/plan/closure docs"
description: "Archived design docs, plans, and closure records for the abandoned local-supervisor / Gradio+devtunnel remote-control-plane architecture (Plan 1 and Plan 2). Superseded by a thin, direct-exec start.ps1/start.sh + config.yaml model. Historical record only — do not implement against these documents."
---

# Deprecated — Local Copilot CLI Supervisor Design

The documents in this directory describe the "local Copilot CLI supervisor"
architecture (`src/autoharness/supervise/`, `src/autoharness/remote/`,
`autoharness run`) and its planned Gradio + Microsoft devtunnel remote
control plane. This entire architecture was abandoned in favor of a thin,
direct-exec startup model: `start.ps1`/`start.sh` launch the configured AI
CLI tool directly, with target selection and arguments read from
`config.yaml` and gitignored overrides from `.env.local`. There is no
process supervision, PTY relay, journaling, locking, or remote control
surface.

These files are retained only as historical record of the prior design and
its shipment history. Do not implement against them.
