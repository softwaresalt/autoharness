# Runtime registration is handled by the setup commands.
# This script only launches Copilot CLI with workspace-local state.
# Re-run `autoharness setup-copilot-cli` after upgrading autoharness so
# updated Auto-MergeInstall / Auto-Tune agent files are recopied into the
# standard Copilot CLI global config directory.

$env:COPILOT_HOME = if ($env:COPILOT_HOME) { $env:COPILOT_HOME } else { "" }
# $env:ENGRAM_DATA_DIR = ".\.engram"   # Uncomment when the agent-engram capability pack is active
$env:GITHUB_TOKEN = (gh auth token)
$copilotExe = if ($env:COPILOT_EXE) {
    $env:COPILOT_EXE
} else {
    (Get-Command "copilot.exe" -ErrorAction SilentlyContinue).Source
}

if (-not $copilotExe) {
    throw "Unable to locate copilot.exe. Set COPILOT_EXE or add copilot.exe to PATH."
}

& $copilotExe
