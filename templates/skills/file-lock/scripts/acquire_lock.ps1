<#
.SYNOPSIS
    Acquires an advisory file lock for agent concurrency control.
.DESCRIPTION
    Creates a .{filename}.lock file in the same directory as the target file.
    Fails with exit code 1 if the lock already exists (another process holds it).

    Enforces workspace-root containment (H2/H4): the target file must resolve,
    after full symlink/junction dereferencing, to a path inside the workspace
    root. Prefix-string comparison is never used; containment is decided by
    path-segment comparison so a sibling directory that merely shares the
    root's name as a string prefix (e.g. `ws-evil` vs `ws`) is never
    mistaken for a contained path.
.PARAMETER FilePath
    Path to the file to lock, relative to the workspace root.
.PARAMETER WorkspaceRoot
    Optional. The workspace root all lock targets must be contained within.
    When omitted, the root is derived from `git rev-parse --show-toplevel`
    run from this script's own directory. That derived root is trusted only
    when this script's own resolved directory is a direct `scripts` child of
    the derived root -- i.e. the derived root is REQUIRED to equal the
    parent of this script's own `scripts` directory. This guards against a
    nested checkout that has no `.git` of its own silently widening to an
    ancestor repository's root (finding 2): in that scenario `git
    rev-parse --show-toplevel` returns the outer, wider repository, whose
    `scripts` child does not match this script's own directory, so the
    check fails closed and the caller must supply -WorkspaceRoot explicitly.
.EXAMPLE
    scripts/acquire_lock.ps1 src/main.rs
.EXAMPLE
    scripts/acquire_lock.ps1 src/main.rs -WorkspaceRoot C:\repo
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$FilePath,

    [Parameter(Mandatory = $false)]
    [string]$WorkspaceRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Real-path resolution -------------------------------------------------
#
# `Resolve-Path` and `[System.IO.Path]::GetFullPath` do NOT dereference
# directory symlinks/junctions on Windows -- they return the literal path
# through the reparse point unresolved (confirmed in task 0's behaviour
# matrix, docs/research/2026-09-10-ship3-file-lock-behavior-matrix-and-token-vectors.md).
# `GetFinalPathNameByHandle` is used instead of the newer
# `FileSystemInfo.ResolveLinkTarget`/`.LinkTarget` APIs because those are
# .NET-Core-only; this P/Invoke call resolves the full reparse-point chain
# in one call and works identically under Windows PowerShell 5.1 and
# PowerShell 7+ (H5).
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

if (-not ('AutoharnessFileLockPathResolver' -as [type])) {
    Add-Type -TypeDefinition $autoharnessResolverSource -ErrorAction Stop
}

function Get-AutoharnessRealPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [AutoharnessFileLockPathResolver]::GetRealPath($Path)
}

function Test-AutoharnessPathContained {
    # Path-segment containment check (H4): a candidate is contained only when
    # it equals the root or begins with the root followed by a directory
    # separator. A bare string-prefix check (`StartsWith($root)` with no
    # separator) is forbidden -- it would wrongly treat "$root-evil" as
    # contained within "$root".
    param(
        [Parameter(Mandatory = $true)][string]$RealRoot,
        [Parameter(Mandatory = $true)][string]$RealCandidate
    )
    if ($RealCandidate.Equals($RealRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    $rootWithSeparator = $RealRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    return $RealCandidate.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)
}

# --- Token/digest (O2, TC1-TC6) --------------------------------------------
#
# TC1: CSPRNG only, >=128 bits. Get-Random/$RANDOM are forbidden non-CSPRNG
# sources; System.Security.Cryptography.RandomNumberGenerator is used here.
# V-a (docs/research/2026-09-10-ship3-file-lock-behavior-matrix-and-token-vectors.md)
# fixes the concrete choice: 32 bytes (256 bits), lowercase hex, fixed length
# 64 characters.
function New-AutoharnessLockToken {
    # RandomNumberGenerator.Fill() is .NET-Core-only (added 3.0+) and is
    # unavailable under Windows PowerShell 5.1's .NET Framework runtime --
    # the portable choice (works on both pwsh and powershell.exe, mirroring
    # the P/Invoke portability rationale used for real-path resolution) is
    # the classic instance-based Create()/GetBytes() API.
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($bytes)
    }
    finally {
        $rng.Dispose()
    }
    return -join ($bytes | ForEach-Object { $_.ToString('x2') })
}

# TC3: SHA-256 digest of the token's canonical UTF-8 bytes (no BOM, no
# trailing newline -- V-a/V-b). `Encoding.UTF8.GetBytes` does not add a BOM
# (only file-writing APIs do, per task 0's empirical finding); this operates
# on the in-memory string directly, never via a file.
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

function Resolve-AutoharnessWorkspaceRoot {
    param([Parameter(Mandatory = $false)][string]$ExplicitRoot)

    if ($ExplicitRoot) {
        if (-not (Test-Path -LiteralPath $ExplicitRoot)) {
            Write-Error "autoharness-file-lock: -WorkspaceRoot does not exist: $ExplicitRoot"
            exit 1
        }
        return Get-AutoharnessRealPath (Resolve-Path -LiteralPath $ExplicitRoot).Path
    }

    # No explicit root supplied: derive a default via git, but only trust it
    # when this script's own directory is a direct `scripts` child of the
    # derived top-level (see the -WorkspaceRoot parameter help above and
    # task 0's case-7 matrix entry for the exact rationale).
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) {
        Write-Error "autoharness-file-lock: cannot derive a default workspace root (no script directory available); pass -WorkspaceRoot explicitly."
        exit 1
    }
    $realScriptDir = Get-AutoharnessRealPath $scriptDir

    $gitTopLevel = $null
    try {
        $gitOutput = & git -C $scriptDir rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and $gitOutput) {
            $gitTopLevel = $gitOutput.Trim()
        }
    }
    catch {
        $gitTopLevel = $null
    }

    if (-not $gitTopLevel) {
        Write-Error "autoharness-file-lock: no -WorkspaceRoot supplied and no git repository found from this script's directory; pass -WorkspaceRoot explicitly."
        exit 1
    }

    $realGitTopLevel = Get-AutoharnessRealPath $gitTopLevel
    $expectedScriptsDir = Join-Path $realGitTopLevel 'scripts'
    $realExpectedScriptsDir = if (Test-Path -LiteralPath $expectedScriptsDir) {
        Get-AutoharnessRealPath $expectedScriptsDir
    } else {
        $expectedScriptsDir
    }

    if (-not $realExpectedScriptsDir.Equals($realScriptDir, [System.StringComparison]::OrdinalIgnoreCase)) {
        Write-Error "autoharness-file-lock: git-derived root '$realGitTopLevel' does not match this script's own installed location; this workspace is likely a nested checkout without its own .git (widening guard, finding 2). Pass -WorkspaceRoot explicitly."
        exit 1
    }

    return $realGitTopLevel
}

# --- Resolve workspace root and target -------------------------------------

$realWorkspaceRoot = Resolve-AutoharnessWorkspaceRoot -ExplicitRoot $WorkspaceRoot

if (-not (Test-Path -LiteralPath $FilePath)) {
    Write-Error "Target file does not exist: $FilePath"
    exit 1
}

$resolvedPath = (Resolve-Path -LiteralPath $FilePath).Path
$realTargetPath = Get-AutoharnessRealPath $resolvedPath

if (-not (Test-AutoharnessPathContained -RealRoot $realWorkspaceRoot -RealCandidate $realTargetPath)) {
    Write-Error "autoharness-file-lock: target path escapes the workspace root and was rejected (root=$realWorkspaceRoot, target=$realTargetPath)."
    exit 1
}

$directory = Split-Path -Parent $realTargetPath
$fileName = Split-Path -Leaf $realTargetPath
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
$lockToken = New-AutoharnessLockToken
$ownerDigest = Get-AutoharnessTokenDigest -Token $lockToken

# O1: `agent`/`pid` remain a courtesy/anti-accident identity only (never
# authorisation -- see TC5/O2). O2: `owner_digest` is the capability check;
# the token itself is NEVER persisted, only its digest.
$lockContent = @"
agent: $agentName
timestamp: $timestamp
pid: $pid_val
file: $FilePath
owner_digest: $ownerDigest
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
    # TC5: the token is a short-lived secret returned on stdout so the
    # caller can capture it. It is printed here, ONCE, on success, and MUST
    # NEVER be re-echoed by this script (or release_lock.ps1) in any later
    # status, verbose, or error output.
    Write-Host "LOCK_TOKEN=$lockToken"
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
