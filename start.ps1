# Runtime registration is handled by the setup commands.
# This script only launches Copilot CLI with workspace-local state.
# Re-run `autoharness setup-copilot-cli` after upgrading autoharness so
# updated Auto-MergeInstall / Auto-Tune agent files are recopied into the
# standard Copilot CLI global config directory.

$env:COPILOT_HOME = if ($env:COPILOT_HOME) { $env:COPILOT_HOME } else { ".\.copilot" }
# $env:ENGRAM_DATA_DIR = ".\.engram"   # Uncomment when the agent-engram capability pack is active
$env:GITHUB_TOKEN = (gh auth token)
$copilotExe = if ($env:COPILOT_EXE_PATH) {
    $env:COPILOT_EXE_PATH
} elseif ($env:COPILOT_EXE) {
    $env:COPILOT_EXE
} else {
    $copilotCommand = Get-Command "copilot" -ErrorAction SilentlyContinue
    if ($copilotCommand) { $copilotCommand.Source } else { $null }
}

if (-not $copilotExe) {
    throw "Unable to locate Copilot CLI. Set COPILOT_EXE_PATH (or COPILOT_EXE for backward compatibility) or add 'copilot' to PATH."
}

& $copilotExe
