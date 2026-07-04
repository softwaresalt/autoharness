# Runtime registration is handled by the setup commands.
# This script only launches Copilot CLI with workspace-local state.
# Re-run `autoharness setup-copilot-cli` after upgrading autoharness so
# updated Auto-MergeInstall / Auto-Tune agent files are recopied into the
# standard Copilot CLI global config directory.

function Invoke-EngramCommandWithProgress {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,

        [Parameter(Mandatory = $true)]
        [string]$Subcommand,

        [string[]]$GlobalArguments = @(),

        [string[]]$Arguments = @(),

        [Parameter(Mandatory = $true)]
        [string]$Activity,

        [Parameter(Mandatory = $true)]
        [string]$Status
    )

    Write-Host "$Activity — $Status"

    $engramArguments = @("--format", "text")
    $engramArguments += $GlobalArguments
    $engramArguments += $Subcommand
    $engramArguments += $Arguments

    & $Executable @engramArguments
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        throw "engram $Subcommand failed with exit code $exitCode."
    }
}

$envLocalPath = Join-Path $PSScriptRoot ".env.local"
if (Test-Path -LiteralPath $envLocalPath -PathType Leaf) {
    Get-Content -LiteralPath $envLocalPath | ForEach-Object {
        if ($_ -match '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$') {
            $name = $matches[1]
            if ($null -eq [Environment]::GetEnvironmentVariable($name, "Process")) {
                $value = $matches[2]
                if ($value.Length -ge 2) {
                    $firstChar = $value[0]
                    $lastChar = $value[$value.Length - 1]
                    if ((($firstChar -eq '"') -or ($firstChar -eq "'")) -and ($lastChar -eq $firstChar)) {
                        $value = $value.Substring(1, $value.Length - 2)
                    }
                }
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
}

$env:COPILOT_HOME = if ($env:COPILOT_HOME) { $env:COPILOT_HOME } else { Join-Path $PSScriptRoot ".copilot" }
$env:ENGRAM_DATA_DIR = if ($env:ENGRAM_DATA_DIR) { $env:ENGRAM_DATA_DIR } else { Join-Path $PSScriptRoot ".engram" }
if (-not $env:GITHUB_TOKEN) {
    $ghCmd = Get-Command gh -ErrorAction SilentlyContinue
    if ($ghCmd) {
        try {
            $ghToken = (& $ghCmd.Source auth token 2>$null).Trim()
            if ($ghToken) {
                $env:GITHUB_TOKEN = $ghToken
            }
        } catch {
            Write-Warning "gh auth token failed (non-fatal): $_"
        }
    }
}
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

$backlogitCmd = Get-Command backlogit -ErrorAction SilentlyContinue
if ($backlogitCmd) {
    try {
        backlogit sync
    } catch {
        Write-Warning "backlogit sync failed (non-fatal): $_"
    }
}

$engramCmd = Get-Command engram -ErrorAction SilentlyContinue
if ($engramCmd) {
    try {
        Invoke-EngramCommandWithProgress `
            -Executable $engramCmd.Source `
            -Subcommand "sync" `
            -GlobalArguments @("--timeout", "300") `
            -Arguments @("--direct") `
            -Activity "Synchronizing Engram index" `
            -Status "Direct pre-warm before Copilot startup"
    } catch {
        Write-Warning "engram direct pre-warm failed; retrying via daemon sync: $_"
        try {
            & $engramCmd.Source --format text bind
            Invoke-EngramCommandWithProgress `
                -Executable $engramCmd.Source `
                -Subcommand "sync" `
                -GlobalArguments @("--timeout", "300") `
                -Activity "Synchronizing Engram index" `
                -Status "Daemon-backed pre-warm fallback"
        } catch {
            Write-Warning "engram sync failed (non-fatal): $_"
        }
    }
}

$copilotArguments = @()
if (-not ($args -contains "--remote")) {
    $copilotArguments += "--remote"
}
$copilotArguments += $args

& $copilotExe @copilotArguments
