<#
.SYNOPSIS
    Releases an advisory file lock for agent concurrency control.
.DESCRIPTION
    Deletes the .{filename}.lock file created by acquire_lock.ps1.
    If the lock file does not exist, emits a warning but exits successfully.
.PARAMETER FilePath
    Path to the file to unlock, relative to the workspace root.
.EXAMPLE
    scripts/release_lock.ps1 src/main.rs
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$FilePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $FilePath)) {
    # Target file may have been deleted or moved; still clean up the lock
    Write-Warning "Target file does not exist: $FilePath"
}

$resolvedDir = if (Test-Path -LiteralPath $FilePath) {
    Split-Path -Parent (Resolve-Path -LiteralPath $FilePath)
} else {
    Split-Path -Parent $FilePath
}

$fileName = Split-Path -Leaf $FilePath
$lockFile = Join-Path $resolvedDir ".$fileName.lock"

if (-not (Test-Path -LiteralPath $lockFile)) {
    Write-Warning "No lock file found for: $FilePath (already released or never locked)"
    exit 0
}

try {
    Remove-Item -LiteralPath $lockFile -Force
    Write-Host "Lock released: $lockFile"
    exit 0
}
catch {
    Write-Error "Failed to remove lock file: $_"
    exit 1
}
