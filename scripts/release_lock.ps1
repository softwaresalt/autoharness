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
.PARAMETER WorkspaceRoot
    Optional (round-6 review, finding-6 parity). Anchors a RELATIVE FilePath
    to the given root instead of the process's current working directory,
    so a caller invoking acquire and release from two DIFFERENT working
    directories with the same documented workspace-relative path (e.g.
    "sub/file.txt") computes the SAME lock path in both cases. When
    omitted, relative paths continue to resolve against the process CWD
    exactly as before (no default root is derived and no root is
    required) -- this parameter is purely additive and does not change
    behaviour for any absolute-path invocation, or for any caller that
    does not supply it.
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
    [switch]$Force,

    [Parameter(Mandatory = $false)]
    [string]$WorkspaceRoot
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

# V-a: the token this script's sibling acquire_lock.ps1 generates is always
# 64 lowercase hex characters (32 CSPRNG bytes, V-a's fixed-length,
# lowercase-only alphabet). V-c2 requires a wrong-length or wrong-charset
# token to be rejected outright -- non-zero exit, a NAMED validation error,
# no digest ever computed -- rather than silently hashed and compared, which
# would let a truncating or charset-loose implementation slip through.
$autoharnessTokenShapeRegex = '^[0-9a-f]{64}$'

# 1-hour staleness heuristic (concurrency.instructions.md): report the lock
# age so an operator deciding whether to -Force has the same information
# the policy asks them to consider. The recorded timestamp may have been
# written by either acquire variant (PowerShell's round-trip
# `Get-Date -Format 'o'`, or POSIX `date -u +%Y-%m-%dT%H:%M:%SZ`);
# DateTimeOffset.Parse handles both forms. When parsing fails, report the
# age as unknown rather than fabricating a value.
function Get-AutoharnessLockAgeReport {
    param([Parameter(Mandatory = $true)][string]$RecordedTimestamp)
    try {
        $lockTime = [System.DateTimeOffset]::Parse(
            $RecordedTimestamp,
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::None)
        $ageSeconds = [int]([System.DateTimeOffset]::UtcNow - $lockTime.ToUniversalTime()).TotalSeconds
        if ($ageSeconds -lt 0) { $ageSeconds = 0 }
        $ageMinutes = [int]($ageSeconds / 60)
        if ($ageSeconds -ge 3600) {
            return "age=${ageMinutes}m (stale: exceeds the 1-hour heuristic)"
        }
        return "age=${ageMinutes}m"
    }
    catch {
        return "age=unknown (unable to parse timestamp: $RecordedTimestamp)"
    }
}

function Get-AutoharnessSingleQuoted {
    # The refusal remedy embeds the caller-supplied path inside a
    # single-quoted PowerShell command that the operator is expected to
    # copy and paste verbatim. A path containing an embedded "'" would
    # otherwise terminate that quoting early and let trailing characters
    # be interpreted as additional PowerShell syntax (injection via a
    # crafted filename). PowerShell's own single-quoted-string escape rule
    # doubles each embedded quote ('' represents a literal '), so apply
    # that rule here before wrapping the result in an outer quote pair.
    param([Parameter(Mandatory = $true)][string]$Value)
    return "'" + ($Value -replace "'", "''") + "'"
}

# -WorkspaceRoot (optional, round-6 review, finding-6 parity): when supplied
# and $FilePath is relative, anchor it to the given root instead of the
# process CWD, so a caller invoking acquire and release from two DIFFERENT
# working directories with the same documented workspace-relative path
# computes the SAME lock path in both cases. An absolute $FilePath is left
# untouched, and omitting -WorkspaceRoot preserves today's CWD-relative
# behaviour exactly (no default root is derived or required).
if ($WorkspaceRoot) {
    if (-not (Test-Path -LiteralPath $WorkspaceRoot)) {
        Write-Error "--workspace-root does not exist: $WorkspaceRoot"
        exit 1
    }
    $realWorkspaceRootForAnchoring = Get-AutoharnessRealPath (Resolve-Path -LiteralPath $WorkspaceRoot).Path
    if (-not [System.IO.Path]::IsPathRooted($FilePath)) {
        $FilePath = Join-Path $realWorkspaceRootForAnchoring $FilePath
    }
}

if (-not (Test-Path -LiteralPath $FilePath)) {
    # Target file may have been deleted or moved; still clean up the lock.
    Write-Warning "Target file does not exist: $FilePath"
}

# Finding 6 fix: always normalise to an absolute path FIRST, which works
# whether or not the target exists (pure string normalisation, no
# filesystem access beyond consulting the current location) -- Split-Path
# can therefore never receive a bare relative root-level filename and see
# an empty parent. When the file does exist, additionally resolve through
# any reparse points so acquire and release agree on the same REAL path
# when a symlink is involved.
#
# Round-6/7 review fix: use $ExecutionContext.SessionState.Path.Get
# UnresolvedProviderPathFromPSPath instead of [System.IO.Path]::GetFullPath.
# GetFullPath resolves a relative path against .NET's
# Environment.CurrentDirectory, which can silently diverge from
# PowerShell's own logical location ($PWD) -- for example after
# `Set-Location` within a runspace, or whenever the process was launched
# from a different directory than the shell's current provider path
# reflects. In that common interactive case, GetFullPath would compute the
# lock path under the process's startup directory instead of the caller's
# actual current directory, report nothing to release, and leave the real
# lock behind. GetUnresolvedProviderPathFromPSPath is the PowerShell-native
# API for resolving a possibly-nonexistent path against $PWD and correctly
# reflects Set-Location, matching the same PWD-relative semantics
# release_lock.sh gets for free from the shell's own $PWD.
$absolutePath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($FilePath)

function Resolve-AutoharnessBestEffortRealPath {
    # Best-effort REAL path resolution for a lock target that may not fully
    # exist, used by the missing-target recovery below so release agrees
    # with acquire's choice of fully-dereferenced lock location. Tried in
    # order:
    #
    #  1. The path fully exists and fully resolves (symlinks/junctions and
    #     all) -- delegate straight to Get-AutoharnessRealPath.
    #
    #  2. Round-8 review fix: the path exists as a filesystem ENTRY (Test-
    #     Path reports true) but Get-AutoharnessRealPath still throws. This
    #     happens for a BROKEN symlink/reparse point -- one whose own
    #     recorded link target no longer exists. Test-Path on a reparse
    #     point reports the entry's own presence, not its target's, so a
    #     deleted-target symlink still reads as "exists" even though
    #     resolving through it (CreateFile/realpath) fails. Read the
    #     entry's OWN recorded link target instead (Get-Item only needs
    #     reparse-point metadata, not the target, so it works even when the
    #     target is gone) and recurse into resolving THAT path -- this is
    #     exactly the real path acquire stored the lock beside before the
    #     target was deleted. A recorded target that is itself relative is
    #     anchored against the symlink's own parent directory, matching how
    #     the filesystem itself would interpret it. A depth cap guards
    #     against a hand-crafted symlink cycle recursing indefinitely.
    #
    #  3. Neither the path nor its symlink metadata is available (a plain
    #     missing file, or nothing in the chain read succeeded) -- resolve
    #     as much of the PARENT chain as exists (H5 parity, round-6 fix)
    #     and fall back to a purely lexical join for the parts that do not.
    param(
        [Parameter(Mandatory = $true)][string]$AbsolutePath,
        [int]$Depth = 0
    )
    if ($Depth -gt 20) {
        return $AbsolutePath
    }
    if (Test-Path -LiteralPath $AbsolutePath) {
        try {
            return Get-AutoharnessRealPath (Resolve-Path -LiteralPath $AbsolutePath).Path
        } catch {
            # Fall through to the broken-symlink-leaf recovery below.
        }
        try {
            $linkItem = Get-Item -LiteralPath $AbsolutePath -Force -ErrorAction Stop
            if ($linkItem.LinkType -and $linkItem.Target) {
                $rawTarget = @($linkItem.Target)[0]
                if (-not [System.IO.Path]::IsPathRooted($rawTarget)) {
                    $rawTarget = Join-Path (Split-Path -Parent $AbsolutePath) $rawTarget
                }
                return Resolve-AutoharnessBestEffortRealPath -AbsolutePath $rawTarget -Depth ($Depth + 1)
            }
        } catch {
            # Fall through to the lexical/parent-based recovery below.
        }
    }
    # Round-6 review / H5 parity fix: a missing target may still have an
    # existing PARENT directory reached through a symlink/junction (e.g.
    # acquired via a path like "link/file.txt" where "link" points at
    # "realdir", then "file.txt" is deleted while "link" itself remains).
    # acquire_lock always stores the lock beside the FULLY DEREFERENCED
    # real path, so a purely lexical GetFullPath here would compute the
    # WRONG lock path (beside the symlink, not the real directory) and
    # silently leave the actual lock behind -- exactly the defect finding 6
    # exists to eliminate. Resolve the parent through any reparse points
    # when it exists (mirroring the POSIX variant's `realpath
    # "$PARENT_DIR"` behaviour, which dereferences symlinks in the parent
    # chain even when the leaf is missing), and only fall back to a purely
    # lexical path when even the parent does not exist (in which case no
    # lock could exist there regardless, and Test-Path on the computed
    # lock path below will simply report none found).
    $lexicalParent = Split-Path -Parent $AbsolutePath
    $leafName = Split-Path -Leaf $AbsolutePath
    if ($lexicalParent -and (Test-Path -LiteralPath $lexicalParent -PathType Container)) {
        $realParent = Get-AutoharnessRealPath (Resolve-Path -LiteralPath $lexicalParent).Path
        return Join-Path $realParent $leafName
    }
    return $AbsolutePath
}

$targetPath = Resolve-AutoharnessBestEffortRealPath -AbsolutePath $absolutePath

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
# carry no authorisation weight. TC5d: every message below names the lock
# path, agent/pid/timestamp/age but NEVER the token or owner_digest.
#
# -Force must not depend on any token-processing tooling or shape at all
# (O3: the operator's override is unconditional): when -Force is supplied,
# ownership verification -- including token-shape validation and digest
# hashing -- is skipped entirely, so a malformed inherited LOCK_TOKEN can
# never block a force-break.
$ownershipVerified = $false
$tokenMalformed = $false
if (-not $Force) {
    if ($suppliedToken -and -not ($suppliedToken -cmatch $autoharnessTokenShapeRegex)) {
        $tokenMalformed = $true
    }
    elseif ($recordedDigest -and $suppliedToken) {
        $suppliedDigest = Get-AutoharnessTokenDigest -Token $suppliedToken
        if ($suppliedDigest.Equals($recordedDigest, [System.StringComparison]::OrdinalIgnoreCase)) {
            $ownershipVerified = $true
        }
    }
}

if ($tokenMalformed) {
    # V-c2: fail closed before any digest is computed -- a wrong-length or
    # wrong-charset token is a distinct, named validation error, not merely
    # a digest mismatch.
    Write-Error "autoharness-file-lock: TOKEN_MALFORMED -- supplied token is not 64 lowercase hex characters; refusing to verify ownership without computing a digest. Supply the exact value returned at acquire time, or have the operator supply -Force."
    exit 1
}

if (-not $ownershipVerified) {
    $ageReport = Get-AutoharnessLockAgeReport -RecordedTimestamp $recordedTimestamp
    $ownerReport = "lock=$lockFile, agent=$recordedAgent, pid=$recordedPid, timestamp=$recordedTimestamp, $ageReport"
    if (-not $Force) {
        # Decision (iii): a refusal is a non-zero exit -- exit 0 would make
        # the refusal indistinguishable from success.
        $quotedPath = Get-AutoharnessSingleQuoted -Value $FilePath
        Write-Error "autoharness-file-lock: refusing to release -- ownership could not be verified ($ownerReport). Supply -Token with the value returned at acquire time, or have the operator run: release_lock.ps1 $quotedPath -Force"
        exit 1
    }
    Write-Warning "autoharness-file-lock: -Force supplied; breaking this lock without a verified token ($ownerReport). O3: this is an advisory lock, not an adversarial guarantee -- only the operator should do this."
}

if ($ownershipVerified) {
    # Round-9 review follow-up (TOCTOU race): ownership was verified above
    # against a SNAPSHOT of the lock file read earlier in this script.
    # Between that read and the Remove-Item below, another legitimate
    # release could have removed this same lock and a new owner could have
    # acquired a DIFFERENT lock at the same path; without a recheck,
    # Remove-Item would delete "whatever currently occupies the path" --
    # i.e. the new owner's lock -- using this process's now-stale token
    # verification. Re-reading owner_digest immediately before deletion and
    # refusing to proceed unless it still matches narrows (though, absent an
    # atomic compare-and-delete filesystem primitive, cannot fully
    # eliminate) that race window. This mitigation only applies to the
    # token-verified path; -Force remains an unconditional operator
    # override per O3 and is not re-checked here.
    if ($env:AUTOHARNESS_TEST_RELEASE_RACE_DELAY_MS) {
        # TEST-ONLY HOOK: deterministically widens the TOCTOU window so an
        # automated test can inject a concurrent lock change between this
        # verification and the recheck below. Never set outside test runs;
        # when the environment variable is absent (the default), this is a
        # complete no-op with zero behavioural or timing impact.
        if ($env:AUTOHARNESS_TEST_RELEASE_RACE_SIGNAL_FILE) {
            # TEST-ONLY HOOK: signals the harness that this process has
            # entered the widened race window, so the test can perform the
            # concurrent swap deterministically instead of guessing at
            # process-startup timing. Never set outside test runs.
            New-Item -ItemType File -Path $env:AUTOHARNESS_TEST_RELEASE_RACE_SIGNAL_FILE -Force | Out-Null
        }
        Start-Sleep -Milliseconds ([int]$env:AUTOHARNESS_TEST_RELEASE_RACE_DELAY_MS)
    }
    if (-not (Test-Path -LiteralPath $lockFile)) {
        Write-Warning "autoharness-file-lock: lock file disappeared before deletion could be confirmed (already released by another process): $lockFile"
        exit 0
    }
    $recheckContent = Get-Content -LiteralPath $lockFile -Raw
    $recheckDigest = $null
    foreach ($line in ($recheckContent -split "`r?`n")) {
        if ($line -match '^owner_digest:\s*(.*)$') {
            $recheckDigest = $Matches[1]
            break
        }
    }
    if (-not ($recheckDigest -and $recheckDigest.Equals($recordedDigest, [System.StringComparison]::OrdinalIgnoreCase))) {
        Write-Error "autoharness-file-lock: refusing to release -- the lock at '$lockFile' changed between verification and deletion (a different owner now holds it); this process's token no longer matches the current owner. Re-run release to re-verify against the new owner, or have the operator use -Force."
        exit 1
    }
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
