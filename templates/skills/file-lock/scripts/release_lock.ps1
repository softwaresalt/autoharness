<#
.SYNOPSIS
    Releases an advisory file lock for agent concurrency control.
.DESCRIPTION
    Deletes the .{filename}.lock file created by acquire_lock.ps1.
    If the lock file does not exist, emits a warning but exits successfully.

    Requires proof of ownership (O2): the caller must supply, via -Token or
    the LOCK_TOKEN environment variable, the same token acquire_lock.ps1
    returned on stdout at acquire time. Release refuses (non-zero exit,
    lock left in place) when the token is absent or does not match the
    recorded owner_digest, unless the operator supplies -Force. -Force
    breaks the lock unconditionally and is intended for operator use only
    (O3: these are advisory locks, not an adversarial security boundary).
.PARAMETER FilePath
    Path to the file to unlock, relative to the workspace root.
.PARAMETER Token
    The capability token returned by acquire_lock.ps1 at acquire time. Falls
    back to the LOCK_TOKEN environment variable when not supplied.
.PARAMETER Force
    Operator-only override: break the lock even without a matching token.
.EXAMPLE
    scripts/release_lock.ps1 src/main.rs -Token <token>
.EXAMPLE
    scripts/release_lock.ps1 src/main.rs -Force
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$FilePath,

    [Parameter(Mandatory = $false)]
    [string]$Token,

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Real-path resolution (same rationale as acquire_lock.ps1) ------------
$autoharnessResolverSource = @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

public static class AutoharnessFileLockPathResolver
{
    private const uint FILE_FLAG_BACKUP_SEMANTICS = 0x02000000;
    private const uint GENERIC_READ = 0x80000000;
    private const uint FILE_SHARE_READ = 0x1;
    private const uint FILE_SHARE_WRITE = 0x2;
    private const uint FILE_SHARE_DELETE = 0x4;
    private const uint OPEN_EXISTING = 3;

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern SafeFileHandle CreateFile(
        string lpFileName, uint dwDesiredAccess, uint dwShareMode,
        IntPtr lpSecurityAttributes, uint dwCreationDisposition,
        uint dwFlagsAndAttributes, IntPtr hTemplateFile);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern uint GetFinalPathNameByHandle(
        SafeFileHandle hFile, StringBuilder lpszFilePath, uint cchFilePath, uint dwFlags);

    public static string GetRealPath(string path)
    {
        using (SafeFileHandle handle = CreateFile(path, GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, IntPtr.Zero,
            OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero))
        {
            if (handle.IsInvalid)
            {
                throw new IOException("autoharness-file-lock: unable to open path for real-path resolution: " + path);
            }
            StringBuilder sb = new StringBuilder(4096);
            uint result = GetFinalPathNameByHandle(handle, sb, (uint)sb.Capacity, 0);
            if (result == 0 || result >= sb.Capacity)
            {
                throw new IOException("autoharness-file-lock: unable to resolve final real path for: " + path);
            }
            string resolved = sb.ToString();
            if (resolved.StartsWith(@"\\?\") && !resolved.StartsWith(@"\\?\UNC\"))
            {
                resolved = resolved.Substring(4);
            }
            return resolved;
        }
    }
}
'@

# The kernel32 P/Invoke resolver above is Windows-only (same rationale as
# acquire_lock.ps1). `$IsWindows` is defined by PowerShell 6+ (pwsh) on every
# platform but does not exist under Windows PowerShell 5.1 (Desktop
# edition), which only ever runs on Windows -- so an undefined `$IsWindows`
# variable means "Windows PowerShell 5.1", which is unconditionally Windows.
$autoharnessIsWindowsPlatform = if (Test-Path variable:IsWindows) { $IsWindows } else { $true }

if ($autoharnessIsWindowsPlatform) {
    if (-not ('AutoharnessFileLockPathResolver' -as [type])) {
        Add-Type -TypeDefinition $autoharnessResolverSource -ErrorAction Stop
    }
}

function Get-AutoharnessRealPath {
    # On Windows: the kernel32 P/Invoke resolver above. On non-Windows
    # (Linux/macOS, reachable only via PowerShell 7+/pwsh): kernel32.dll does
    # not exist, so shell out to the external `realpath` command instead --
    # the same tool and invocation form used by the sibling `.sh` scripts.
    param([Parameter(Mandatory = $true)][string]$Path)
    if ($autoharnessIsWindowsPlatform) {
        return [AutoharnessFileLockPathResolver]::GetRealPath($Path)
    }
    $resolved = & realpath $Path 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $resolved) {
        throw "autoharness-file-lock: unable to resolve real path via realpath: $Path"
    }
    return $resolved
}

# TC3: same digest computation as acquire_lock.ps1 (V-b canonicalization).
function Get-AutoharnessTokenDigest {
    param([Parameter(Mandatory = $true)][string]$Token)
    $tokenBytes = [System.Text.Encoding]::UTF8.GetBytes($Token)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $digestBytes = $sha.ComputeHash($tokenBytes)
    }
    finally {
        $sha.Dispose()
    }
    return -join ($digestBytes | ForEach-Object { $_.ToString('x2') })
}

if (-not (Test-Path -LiteralPath $FilePath)) {
    # Target file may have been deleted or moved; still clean up the lock.
    Write-Warning "Target file does not exist: $FilePath"
}

# Finding 6 fix: always normalise to an absolute path via GetFullPath FIRST,
# which works whether or not the target exists (pure string normalisation,
# no filesystem access) -- Split-Path can therefore never receive a bare
# relative root-level filename and see an empty parent. When the file does
# exist, additionally resolve through any reparse points so acquire and
# release agree on the same REAL path when a symlink is involved.
$absolutePath = [System.IO.Path]::GetFullPath($FilePath)
$targetPath = if (Test-Path -LiteralPath $FilePath) {
    Get-AutoharnessRealPath (Resolve-Path -LiteralPath $FilePath).Path
} else {
    $absolutePath
}

$resolvedDir = Split-Path -Parent $targetPath
$fileName = Split-Path -Leaf $targetPath
$lockFile = Join-Path $resolvedDir ".$fileName.lock"

if (-not (Test-Path -LiteralPath $lockFile)) {
    Write-Warning "No lock file found for: $FilePath (already released or never locked)"
    exit 0
}

$lockContent = Get-Content -LiteralPath $lockFile -Raw
$recordedFields = @{}
foreach ($line in ($lockContent -split "`r?`n")) {
    if ($line -match '^([a-zA-Z_]+):\s*(.*)$') {
        $recordedFields[$Matches[1]] = $Matches[2]
    }
}
$recordedDigest = $recordedFields['owner_digest']
$recordedAgent = if ($recordedFields.ContainsKey('agent')) { $recordedFields['agent'] } else { 'unknown' }
$recordedPid = if ($recordedFields.ContainsKey('pid')) { $recordedFields['pid'] } else { 'unknown' }
$recordedTimestamp = if ($recordedFields.ContainsKey('timestamp')) { $recordedFields['timestamp'] } else { 'unknown' }

$suppliedToken = if ($Token) { $Token } elseif ($env:LOCK_TOKEN) { $env:LOCK_TOKEN } else { $null }

# O2: possession of the token that hashes to the recorded owner_digest is the
# capability check. O1: agent/pid/timestamp are courtesy identity only and
# carry no authorisation weight. TC5d: the refusal/staleness report below
# names agent/pid/timestamp but NEVER the token or owner_digest.
$ownershipVerified = $false
if ($recordedDigest -and $suppliedToken) {
    $suppliedDigest = Get-AutoharnessTokenDigest -Token $suppliedToken
    if ($suppliedDigest.Equals($recordedDigest, [System.StringComparison]::OrdinalIgnoreCase)) {
        $ownershipVerified = $true
    }
}

if (-not $ownershipVerified) {
    $ownerReport = "agent=$recordedAgent, pid=$recordedPid, timestamp=$recordedTimestamp"
    if (-not $Force) {
        # Decision (iii): a refusal is a non-zero exit -- exit 0 would make
        # the refusal indistinguishable from success.
        Write-Error "autoharness-file-lock: refusing to release -- ownership could not be verified ($ownerReport). Supply -Token with the value returned at acquire time, or have the operator supply -Force."
        exit 1
    }
    Write-Warning "autoharness-file-lock: -Force supplied; breaking this lock without a verified token ($ownerReport). O3: this is an advisory lock, not an adversarial guarantee -- only the operator should do this."
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
