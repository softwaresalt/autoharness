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
# PowerShell 7+ (H5). This resolver is Windows-only (kernel32.dll does not
# exist on Linux/macOS); on non-Windows platforms (reachable only via
# PowerShell 7+/pwsh) `Get-AutoharnessRealPath` below shells out to the
# external `realpath` command instead, mirroring the sibling `.sh` scripts.
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

# The kernel32 P/Invoke resolver above is Windows-only. `$IsWindows` is
# defined by PowerShell 6+ (pwsh) on every platform but does not exist under
# Windows PowerShell 5.1 (Desktop edition), which only ever runs on Windows --
# so an undefined `$IsWindows` variable means "Windows PowerShell 5.1",
# which is unconditionally Windows. This is evaluated once at script scope
# rather than inside the function so `Add-Type` (an expensive, one-time,
# process-wide type registration) is skipped entirely on non-Windows instead
# of merely guarding the call site.
$autoharnessIsWindowsPlatform = if (Test-Path variable:IsWindows) { $IsWindows } else { $true }

# Shared path-equality comparison mode, derived from the same platform flag:
# Windows filesystems (NTFS) are case-preserving but case-insensitive, so
# OrdinalIgnoreCase is correct there; Linux/macOS filesystems are
# case-sensitive by default, so any path-equality/prefix check on those
# platforms must use Ordinal instead, or a case-only sibling path (e.g.
# "/tmp/WS" vs root "/tmp/ws") would be wrongly treated as identical/contained.
$autoharnessPathComparisonMode = if ($autoharnessIsWindowsPlatform) {
    [System.StringComparison]::OrdinalIgnoreCase
} else {
    [System.StringComparison]::Ordinal
}

if ($autoharnessIsWindowsPlatform) {
    if (-not ('AutoharnessFileLockPathResolver' -as [type])) {
        Add-Type -TypeDefinition $autoharnessResolverSource -ErrorAction Stop
    }
}

function Get-AutoharnessRealPath {
    # On Windows: the kernel32 P/Invoke resolver above, which fully
    # dereferences symlinks/junctions/8.3 short paths and works identically
    # under Windows PowerShell 5.1 and PowerShell 7+ (H5).
    #
    # On non-Windows (Linux/macOS, reachable only via PowerShell 7+/pwsh):
    # kernel32.dll does not exist, so the P/Invoke path is unusable. Shell
    # out to the external `realpath` command instead -- the identical tool
    # and invocation form (`realpath "$path"`, no flags) already used by the
    # sibling `.sh` scripts (acquire_lock.sh/release_lock.sh), so real-path
    # semantics stay consistent across the bash and PowerShell entry points
    # on the same platform. This requires the target to already exist, same
    # as the Windows CreateFile-based resolver (OPEN_EXISTING).
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

function Get-AutoharnessContainmentComparisonMode {
    # H4 containment-check comparison mode, queried per-root rather than
    # assumed from the OS alone (round-8 review fix). Windows 10 1803+
    # supports PER-DIRECTORY case sensitivity (`fsutil file
    # setCaseSensitiveInfo`, used by WSL interop and some containerized
    # workloads); when the root's PARENT directory has that attribute set,
    # sibling directories differing only by case (e.g. "ws" and "WS") can
    # genuinely coexist there. The previous blanket "OrdinalIgnoreCase
    # because this is Windows" assumption would wrongly conflate such a
    # case-differing sibling with the real root, letting a candidate that
    # actually resolved into the sibling be treated as contained. Query the
    # ACTUAL case-sensitivity of the root's parent directory via `fsutil
    # file queryCaseSensitiveInfo` (the attribute governs whether entries
    # WITHIN that parent can coexist by case alone, which is exactly the
    # sibling-collision scenario this containment check must not miss); a
    # query failure (fsutil unavailable, non-NTFS volume, insufficient
    # privilege, any other error) or a root with no parent (the root IS the
    # filesystem root) falls back to OrdinalIgnoreCase, the safe default for
    # the overwhelming majority of ordinary (case-insensitive) NTFS volumes.
    # Non-Windows platforms are case-sensitive by default and always use
    # Ordinal, unchanged from before -- this helper is only consulted on
    # Windows.
    param([Parameter(Mandatory = $true)][string]$RootPath)
    if (-not $autoharnessIsWindowsPlatform) {
        return [System.StringComparison]::Ordinal
    }
    $parentOfRoot = Split-Path -Parent $RootPath
    if ([string]::IsNullOrEmpty($parentOfRoot)) {
        return [System.StringComparison]::OrdinalIgnoreCase
    }
    try {
        # Round-9 review fix: fsutil's actual output is "Case sensitive
        # attribute on directory <path> is enabled." (or "... is disabled."),
        # never containing the substring "is case sensitive" that the
        # original match pattern looked for -- so the enabled case was NEVER
        # detected and this helper always fell through to the
        # OrdinalIgnoreCase default, silently defeating the whole per-
        # directory check this function exists to perform. Match the actual
        # "is enabled." wording instead (confirmed empirically: `fsutil file
        # setCaseSensitiveInfo <dir> enable` followed by `queryCaseSensitiveInfo`
        # prints exactly "... is enabled.", and the disabled case prints
        # "... is disabled." -- the two are disjoint substrings, so this
        # match cannot conflate them).
        $fsutilOutput = & fsutil file queryCaseSensitiveInfo $parentOfRoot 2>$null
        if ($LASTEXITCODE -eq 0 -and (($fsutilOutput -join "`n") -match 'is enabled')) {
            return [System.StringComparison]::Ordinal
        }
    } catch {
        # Fall through to the safe OrdinalIgnoreCase default below.
    }
    return [System.StringComparison]::OrdinalIgnoreCase
}

function Test-AutoharnessPathContained {
    # Path-segment containment check (H4): a candidate is contained only when
    # it begins with the root followed by a directory separator. A bare
    # string-prefix check (`StartsWith($root)` with no separator) is
    # forbidden -- it would wrongly treat "$root-evil" as contained within
    # "$root".
    #
    # The root itself is deliberately NOT treated as contained: accepting
    # equality would let a caller pass the workspace root directory itself
    # as the lock target, and Split-Path would then place the lock file
    # (".<root-name>.lock") in the root's PARENT -- outside the containment
    # boundary this check exists to enforce. Only a proper descendant of the
    # root is a valid lock target.
    #
    # Round-8 review fix: the comparison mode is now derived PER-ROOT via
    # Get-AutoharnessContainmentComparisonMode instead of the coarser
    # OS-only $autoharnessPathComparisonMode -- a blanket "Windows means
    # OrdinalIgnoreCase" assumption misses per-directory case sensitivity
    # (fsutil file setCaseSensitiveInfo), under which a case-only sibling
    # (e.g. "ws" vs "WS") can genuinely coexist even on Windows. This script
    # explicitly supports Linux/macOS pwsh too, where Ordinal is always used
    # regardless of any per-directory query.
    param(
        [Parameter(Mandatory = $true)][string]$RealRoot,
        [Parameter(Mandatory = $true)][string]$RealCandidate
    )
    $comparisonMode = Get-AutoharnessContainmentComparisonMode -RootPath $RealRoot
    $normalizedRoot = $RealRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $normalizedCandidate = $RealCandidate.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    # Round-6/7 review fix: reject equality BEFORE the prefix check. For a
    # filesystem-root value of $RealRoot (e.g. "C:\" or "/"), trimming the
    # trailing separator and re-appending it below recreates the root
    # string exactly, so a bare StartsWith check would wrongly return true
    # for a candidate equal to the root itself -- the equality-rejection
    # contract this function documents above would silently not hold for
    # a root that IS a filesystem root. Comparing the two normalized
    # (separator-trimmed) forms directly, with the same comparison mode
    # used below, closes that gap without changing behaviour for any
    # non-degenerate root.
    if ($normalizedCandidate.Equals($normalizedRoot, $comparisonMode)) {
        return $false
    }
    $rootWithSeparator = $normalizedRoot + [System.IO.Path]::DirectorySeparatorChar
    return $RealCandidate.StartsWith($rootWithSeparator, $comparisonMode)
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

    if (-not $realExpectedScriptsDir.Equals($realScriptDir, $autoharnessPathComparisonMode)) {
        Write-Error "autoharness-file-lock: git-derived root '$realGitTopLevel' does not match this script's own installed location; this workspace is likely a nested checkout without its own .git (widening guard, finding 2). Pass -WorkspaceRoot explicitly."
        exit 1
    }

    return $realGitTopLevel
}

# --- Resolve workspace root and target -------------------------------------

$realWorkspaceRoot = Resolve-AutoharnessWorkspaceRoot -ExplicitRoot $WorkspaceRoot

# FilePath is documented as workspace-root-relative (round-9 review fix):
# anchor a relative value to the resolved workspace root instead of the
# process's current working directory. Unlike release_lock.ps1 (which only
# anchors when -WorkspaceRoot is explicitly supplied, since it has no
# default root of its own), acquire_lock.ps1 ALWAYS resolves a workspace
# root above (explicit or git-derived), so anchoring here is unconditional.
# Without this, a caller invoking the script from a directory other than the
# workspace root could fail to lock the intended in-root target, or lock a
# different same-named file that happens to exist under the caller's CWD.
# An absolute FilePath is left untouched.
if (-not [System.IO.Path]::IsPathRooted($FilePath)) {
    $FilePath = Join-Path $realWorkspaceRoot $FilePath
}

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
    # TC5d: the lock content now carries owner_digest (O2). Printing the raw
    # file content here would leak owner_digest into contention diagnostics,
    # contradicting TC5d's "never print owner_digest or the token"
    # guarantee. Parse and print only the non-sensitive fields (agent, pid,
    # timestamp), the same fields release_lock.ps1 reports in its own
    # ownership-refusal diagnostic.
    $existingLockContent = Get-Content -LiteralPath $lockFile -Raw
    $existingFields = @{}
    foreach ($line in ($existingLockContent -split "`r?`n")) {
        if ($line -match '^([a-zA-Z_]+):\s*(.*)$') {
            $existingFields[$Matches[1]] = $Matches[2]
        }
    }
    $existingAgent = if ($existingFields.ContainsKey('agent')) { $existingFields['agent'] } else { 'unknown' }
    $existingPid = if ($existingFields.ContainsKey('pid')) { $existingFields['pid'] } else { 'unknown' }
    $existingTimestamp = if ($existingFields.ContainsKey('timestamp')) { $existingFields['timestamp'] } else { 'unknown' }
    Write-Warning "Lock already held on: $FilePath"
    Write-Warning "Lock info: agent=$existingAgent, pid=$existingPid, timestamp=$existingTimestamp"
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
    #
    # Write-Output (not Write-Host) is required: Write-Host writes to the
    # host/information stream, which ordinary success-stream capture (e.g.
    # `$result = & ./acquire_lock.ps1 ...`) never receives. Since
    # release_lock.ps1 now requires this token, a caller using standard
    # capture would silently receive no token at all if this stayed on
    # Write-Host. The human-readable "Lock acquired" status line above
    # intentionally remains on Write-Host.
    Write-Output "LOCK_TOKEN=$lockToken"
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
