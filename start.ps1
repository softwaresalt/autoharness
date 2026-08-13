# Runtime registration is handled by the setup commands.
#
# This script is a thin compatibility shim: it delegates the entire
# supervised Copilot CLI session lifecycle -- workspace bootstrap, sidecar
# preflight, CLI resolution, spawn, and lifecycle supervision -- to
# `autoharness run`. See src/autoharness/supervise/ (bootstrap.py,
# sidecar.py, resolve.py, app.py) for the implementation this script no
# longer duplicates.
#
# Auto-MergeInstall / Auto-Tune are GLOBAL agents provided by the autoharness
# marketplace plugin. They are the versions used when upgrading autoharness and
# are intentionally NOT copied into this workspace's local agent config -- a
# stale local copy would shadow the global agent during an upgrade. Upgrade
# them globally with `copilot plugin install autoharness@autoharness`.

autoharness run --workspace $PSScriptRoot -- @args
exit $LASTEXITCODE
