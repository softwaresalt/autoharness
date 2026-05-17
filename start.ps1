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

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $Executable
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true

    [void]$startInfo.ArgumentList.Add("--format")
    [void]$startInfo.ArgumentList.Add("text")

    foreach ($argument in $GlobalArguments) {
        [void]$startInfo.ArgumentList.Add($argument)
    }

    [void]$startInfo.ArgumentList.Add($Subcommand)

    foreach ($argument in $Arguments) {
        [void]$startInfo.ArgumentList.Add($argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo

    if (-not $process.Start()) {
        throw "Failed to start engram $Subcommand."
    }

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $startedAt = Get-Date
    $percentComplete = 0

    while (-not $process.WaitForExit(250)) {
        $percentComplete = ($percentComplete + 4) % 100
        $elapsedSeconds = [math]::Floor(((Get-Date) - $startedAt).TotalSeconds)
        Write-Progress -Id 1 -Activity $Activity -Status "$Status ($elapsedSeconds s elapsed)" -PercentComplete $percentComplete
    }

    $process.WaitForExit()
    Write-Progress -Id 1 -Activity $Activity -Completed

    $stdout = $stdoutTask.GetAwaiter().GetResult().TrimEnd()
    $stderr = $stderrTask.GetAwaiter().GetResult().TrimEnd()

    if (-not [string]::IsNullOrWhiteSpace($stdout)) {
        Write-Host $stdout
    }

    if ($process.ExitCode -ne 0) {
        if (-not [string]::IsNullOrWhiteSpace($stderr)) {
            throw $stderr
        }

        if (-not [string]::IsNullOrWhiteSpace($stdout)) {
            throw $stdout
        }

        throw "engram $Subcommand failed with exit code $($process.ExitCode)."
    }

    if (-not [string]::IsNullOrWhiteSpace($stderr)) {
        Write-Warning $stderr
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

& $copilotExe --remote
