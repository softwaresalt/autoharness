<#
.SYNOPSIS
    Acquires an advisory file lock for agent concurrency control.
.DESCRIPTION
    Creates a .{filename}.lock file in the same directory as the target file.
    Fails with exit code 1 if the lock already exists (another process holds it).
.PARAMETER FilePath
    Path to the file to lock, relative to the workspace root.
.EXAMPLE
    scripts/acquire_lock.ps1 src/main.rs
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$FilePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $FilePath)) {
    Write-Error "Target file does not exist: $FilePath"
    exit 1
}

$resolvedPath = Resolve-Path -LiteralPath $FilePath
$directory = Split-Path -Parent $resolvedPath
$fileName = Split-Path -Leaf $resolvedPath
$lockFile = Join-Path $directory ".$fileName.lock"

if (Test-Path -LiteralPath $lockFile) {
    $lockContent = Get-Content -LiteralPath $lockFile -Raw
    Write-Warning "Lock already held on: $FilePath"
    Write-Warning "Lock info: $lockContent"
    exit 1
}

$agentName = if ($env:AGENT_NAME) { $env:AGENT_NAME } else { "unknown" }
$timestamp = Get-Date -Format 'o'
$pid_val = $PID

$lockContent = @"
agent: $agentName
timestamp: $timestamp
pid: $pid_val
file: $FilePath
"@

try {
    # Use exclusive file creation to minimize race window
    $stream = [System.IO.File]::Open(
        $lockFile,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    $writer = [System.IO.StreamWriter]::new($stream)
    $writer.Write($lockContent)
    $writer.Close()
    $stream.Close()
    Write-Host "Lock acquired: $lockFile"
    exit 0
}
catch [System.IO.IOException] {
    # Another process created the lock between our check and creation
    Write-Warning "Lock already held on: $FilePath (race condition)"
    exit 1
}
catch {
    Write-Error "Failed to create lock file: $_"
    exit 1
}
