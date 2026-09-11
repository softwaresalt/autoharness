#!/usr/bin/env bash
# Releases an advisory file lock for agent concurrency control.
# Deletes the .{filename}.lock file created by acquire_lock.sh.
# If the lock file does not exist, emits a warning but exits successfully.
#
# Requires proof of ownership (O2): the caller must supply, via --token or
# the LOCK_TOKEN environment variable, the same token acquire_lock.sh
# returned on stdout at acquire time. Release refuses (non-zero exit, lock
# left in place) when the token is absent or does not match the recorded
# owner_digest, unless the operator supplies --force. --force breaks the
# lock unconditionally and is intended for operator use only (O3: these are
# advisory locks, not an adversarial security boundary).
#
# --workspace-root <path> (optional; round-6 review, finding-6 parity):
# anchors a RELATIVE filepath argument to the given root instead of the
# process's current working directory, so a caller invoking acquire and
# release from two DIFFERENT working directories with the same documented
# workspace-relative path (e.g. "sub/file.txt") computes the SAME lock
# path in both cases. When omitted, relative paths continue to resolve
# against the process CWD exactly as before (no default root is derived
# and no root is required) -- this option is purely additive and does not
# change behaviour for any absolute-path invocation, or for any caller that
# does not supply it.
#
# Usage: scripts/release_lock.sh <filepath> [--token <token>] [--force] [--workspace-root <path>]

set -euo pipefail

FILEPATH=""
TOKEN="${LOCK_TOKEN:-}"
FORCE=0
WORKSPACE_ROOT=""

while [ $# -gt 0 ]; do
    case "$1" in
        --token)
            if [ $# -lt 2 ]; then
                echo "Error: --token requires a value" >&2
                exit 1
            fi
            TOKEN="$2"
            shift 2
            ;;
        --force)
            FORCE=1
            shift
            ;;
        --workspace-root)
            if [ $# -lt 2 ]; then
                echo "Error: --workspace-root requires a value" >&2
                exit 1
            fi
            WORKSPACE_ROOT="$2"
            shift 2
            ;;
        *)
            if [ -z "$FILEPATH" ]; then
                FILEPATH="$1"
            else
                echo "Usage: release_lock.sh <filepath> [--token <token>] [--force] [--workspace-root <path>]" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$FILEPATH" ]; then
    echo "Usage: release_lock.sh <filepath> [--token <token>] [--force] [--workspace-root <path>]" >&2
    exit 1
fi

# When --workspace-root is supplied and FILEPATH is relative (does not
# start with "/"), anchor it to the given root instead of the process CWD.
# An absolute FILEPATH is left untouched -- there is no CWD ambiguity to
# resolve for it, matching acquire_lock.sh's own treatment of --workspace-root
# (which affects containment decisions, never path resolution, for an
# already-absolute target).
if [ -n "$WORKSPACE_ROOT" ]; then
    if [ ! -e "$WORKSPACE_ROOT" ]; then
        echo "Error: --workspace-root does not exist: $WORKSPACE_ROOT" >&2
        exit 1
    fi
    REAL_WORKSPACE_ROOT="$(realpath "$WORKSPACE_ROOT")"
    case "$FILEPATH" in
        /*) ;;
        *) FILEPATH="${REAL_WORKSPACE_ROOT}/${FILEPATH}" ;;
    esac
fi

if [ ! -e "$FILEPATH" ]; then
    echo "Warning: Target file does not exist: $FILEPATH" >&2
fi

# Finding 6 fix: resolve the target to an absolate real path so dirname/
# basename never operate on an unnormalised relative root-level filename --
# even when the target itself does not yet exist. `realpath` on a
# non-existent path is NOT reliably portable: GNU coreutils' plain
# `realpath` (no flags) tolerates a missing *final* path component, but
# BSD/macOS `realpath` requires every component, including the leaf, to
# already exist and errors under `set -e` otherwise. Deliberately NOT
# `realpath -m`: that flag is a GNU-only extension
# (`--canonicalize-missing`) unsupported by BSD/macOS realpath.
#
# The portable fix: only call `realpath` on the full path when the target
# already exists. When it does not, resolve just the (always-required-to-
# exist) parent directory with `realpath` and re-append the leaf filename --
# this needs no non-existent-path canonicalisation support from `realpath`
# at all, so it works identically on GNU and BSD/macOS.
#
# Round-8 review fix: `[ -e "$path" ]` follows a symlink and reports the
# TARGET's existence, so a BROKEN symlink leaf (its own recorded target
# deleted) falls into the "does not exist" branch below. The parent-only
# recovery there previously re-appended the symlink's own lexical name as
# the leaf, computing the WRONG lock path (beside the symlink, not beside
# the real target acquire actually locked). `[ -L "$path" ]` checks the
# link entry itself without following it, so it still reports true for a
# broken symlink; `readlink` then reads its raw recorded target without
# requiring that target to exist, letting release recover and resolve the
# SAME real path acquire stored the lock beside. A depth cap guards against
# a hand-crafted symlink cycle recursing indefinitely. `exit 0` is
# deliberately never called from inside this function: it runs inside the
# command-substitution subshell created by its caller below, where `exit`
# would only terminate that subshell, not the script -- callers detect the
# "no resolvable parent" case via this function's non-zero return status
# instead, and perform the warn-and-exit-0 themselves at the top level.
resolve_autoharness_best_effort_real_path() {
    local candidate="$1"
    local depth="${2:-0}"
    if [ "$depth" -gt 20 ]; then
        printf '%s\n' "$candidate"
        return 0
    fi
    if [ -e "$candidate" ]; then
        realpath "$candidate"
        return 0
    fi
    if [ -L "$candidate" ]; then
        local raw_target
        raw_target="$(readlink "$candidate")"
        case "$raw_target" in
            /*) ;;
            *) raw_target="$(dirname "$candidate")/${raw_target}" ;;
        esac
        resolve_autoharness_best_effort_real_path "$raw_target" "$((depth + 1))"
        return $?
    fi
    local parent_dir leaf_name
    parent_dir="$(dirname "$candidate")"
    leaf_name="$(basename "$candidate")"
    if [ ! -d "$parent_dir" ]; then
        # A missing parent directory means no lock file could possibly
        # exist beside this target either -- a lock file always lives in
        # the same directory as its target. This mirrors the PowerShell
        # variant, which never errors on a missing parent (GetFullPath is
        # pure string normalisation with no filesystem access), and the
        # documented "no lock file exists" contract: a warning and a
        # successful exit, not a failure -- signalled to the caller via a
        # non-zero return here rather than exiting directly (see above).
        return 1
    fi
    printf '%s/%s\n' "$(realpath "$parent_dir")" "$leaf_name"
}
if ! TARGET_PATH="$(resolve_autoharness_best_effort_real_path "$FILEPATH")"; then
    echo "Warning: No lock file found for: $FILEPATH (parent directory does not exist; already released or never locked)" >&2
    exit 0
fi

RESOLVED_DIR="$(dirname "$TARGET_PATH")"
FILENAME="$(basename "$TARGET_PATH")"
LOCKFILE="${RESOLVED_DIR}/.${FILENAME}.lock"

if [ ! -e "$LOCKFILE" ]; then
    echo "Warning: No lock file found for: $FILEPATH (already released or never locked)" >&2
    exit 0
fi

LOCK_CONTENT="$(cat "$LOCKFILE")"
# Round-6/7 review fix: acquire_lock.sh always writes owner_digest as the
# LAST field of the lock content (agent, timestamp, pid, file,
# owner_digest, in that order). The `agent` and `file` fields are
# caller-controlled and are written BEFORE owner_digest; either can legally
# contain an embedded newline (e.g. a FILEPATH value like
# "x\nowner_digest: <attacker-chosen>") that injects a second, fake
# `owner_digest:` line ahead of the genuine one. Selecting the FIRST match
# (`head -n1`) would then read the injected value instead of the real
# digest acquire computed. Since the genuine field is always written last
# and nothing legitimate follows it, selecting the LAST match (`tail -n1`)
# is safe and always yields the authentic digest regardless of any
# newline injected earlier in the file.
RECORDED_DIGEST="$(printf '%s\n' "$LOCK_CONTENT" | sed -n 's/^owner_digest: //p' | tail -n1)"
RECORDED_AGENT="$(printf '%s\n' "$LOCK_CONTENT" | sed -n 's/^agent: //p' | head -n1)"
RECORDED_PID="$(printf '%s\n' "$LOCK_CONTENT" | sed -n 's/^pid: //p' | head -n1)"
RECORDED_TIMESTAMP="$(printf '%s\n' "$LOCK_CONTENT" | sed -n 's/^timestamp: //p' | head -n1)"
RECORDED_AGENT="${RECORDED_AGENT:-unknown}"
RECORDED_PID="${RECORDED_PID:-unknown}"
RECORDED_TIMESTAMP="${RECORDED_TIMESTAMP:-unknown}"

# V-a: the token this script's sibling acquire_lock.sh generates is always
# 64 lowercase hex characters (32 CSPRNG bytes, V-a's fixed-length,
# lowercase-only alphabet). V-c2 requires a wrong-length or wrong-charset
# token to be rejected outright -- non-zero exit, a NAMED validation error,
# no digest ever computed -- rather than silently hashed and compared, which
# would let a truncating or charset-loose implementation slip through.
_TOKEN_SHAPE_RE='^[0-9a-f]{64}$'

# V-d: SHA-256 only, via sha256sum or shasum -a 256; never a weaker digest.
compute_digest() {
    if command -v sha256sum >/dev/null 2>&1; then
        printf '%s' "$1" | sha256sum | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        printf '%s' "$1" | shasum -a 256 | awk '{print $1}'
    else
        echo "Error: neither 'sha256sum' nor 'shasum -a 256' is available; cannot verify ownership." >&2
        exit 1
    fi
}

# 1-hour staleness heuristic (concurrency.instructions.md): report the lock
# age so an operator deciding whether to --force has the same information
# the policy asks them to consider. The recorded timestamp may have been
# written by either acquire variant (POSIX `date -u +%Y-%m-%dT%H:%M:%SZ`, or
# PowerShell's round-trip `Get-Date -Format 'o'`, which carries a local UTC
# offset instead of a trailing Z); GNU `date -d` parses both forms, BSD/macOS
# `date -j -f` only the POSIX-Z form. When neither succeeds, report the age
# as unknown rather than fabricating a value.
compute_lock_age_report() {
    local ts="$1"
    local now_epoch lock_epoch
    now_epoch="$(date -u +%s)"
    lock_epoch="$(date -u -d "$ts" +%s 2>/dev/null || true)"
    if [ -z "$lock_epoch" ]; then
        lock_epoch="$(date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +%s 2>/dev/null || true)"
    fi
    if [ -z "$lock_epoch" ]; then
        echo "age=unknown (unable to parse timestamp: $ts)"
        return
    fi
    local age_seconds=$(( now_epoch - lock_epoch ))
    if [ "$age_seconds" -lt 0 ]; then
        age_seconds=0
    fi
    local age_minutes=$(( age_seconds / 60 ))
    if [ "$age_seconds" -ge 3600 ]; then
        echo "age=${age_minutes}m (stale: exceeds the 1-hour heuristic)"
    else
        echo "age=${age_minutes}m"
    fi
}

# The refusal remedy below embeds the caller-supplied path inside a
# single-quoted shell command that the operator is expected to copy and
# paste verbatim. A path containing an embedded single quote would
# otherwise terminate that quoting early and let trailing characters be
# interpreted as additional shell syntax (command injection via a crafted
# filename). Render the path through the standard POSIX-safe single-quote
# idiom instead: replace each embedded "'" with the four-character
# sequence '\'' (close quote, escaped literal quote, reopen quote), then
# wrap the whole result in an outer pair of single quotes.
shell_quote() {
    printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"
}

# O2: possession of a token hashing to the recorded owner_digest is the
# capability check. O1: agent/pid/timestamp are courtesy identity only and
# carry no authorisation weight. TC5d: every message below names the lock
# path, agent/pid/timestamp/age but NEVER the token or owner_digest.
#
# --force must not depend on any token-processing tooling or shape at all
# (O3: the operator's override is unconditional): when FORCE=1, ownership
# verification -- including token-shape validation and digest hashing -- is
# skipped entirely, so a host without sha256sum/shasum, or a malformed
# inherited LOCK_TOKEN, can never block a force-break.
OWNERSHIP_VERIFIED=0
TOKEN_MALFORMED=0
if [ "$FORCE" -ne 1 ]; then
    if [ -n "$TOKEN" ] && ! [[ "$TOKEN" =~ $_TOKEN_SHAPE_RE ]]; then
        TOKEN_MALFORMED=1
    elif [ -n "$RECORDED_DIGEST" ] && [ -n "$TOKEN" ]; then
        SUPPLIED_DIGEST="$(compute_digest "$TOKEN")"
        SUPPLIED_DIGEST_LOWER="$(printf '%s' "$SUPPLIED_DIGEST" | tr '[:upper:]' '[:lower:]')"
        RECORDED_DIGEST_LOWER="$(printf '%s' "$RECORDED_DIGEST" | tr '[:upper:]' '[:lower:]')"
        if [ "$SUPPLIED_DIGEST_LOWER" = "$RECORDED_DIGEST_LOWER" ]; then
            OWNERSHIP_VERIFIED=1
        fi
    fi
fi

if [ "$TOKEN_MALFORMED" -eq 1 ]; then
    # V-c2: fail closed before any digest is computed -- a wrong-length or
    # wrong-charset token is a distinct, named validation error, not merely
    # a digest mismatch.
    echo "Error: TOKEN_MALFORMED -- supplied token is not 64 lowercase hex characters; refusing to verify ownership without computing a digest. Supply the exact value returned at acquire time, or have the operator supply --force." >&2
    exit 1
fi

if [ "$OWNERSHIP_VERIFIED" -ne 1 ]; then
    AGE_REPORT="$(compute_lock_age_report "$RECORDED_TIMESTAMP")"
    OWNER_REPORT="lock=${LOCKFILE}, agent=${RECORDED_AGENT}, pid=${RECORDED_PID}, timestamp=${RECORDED_TIMESTAMP}, ${AGE_REPORT}"
    if [ "$FORCE" -ne 1 ]; then
        # Decision (iii): refusal is a non-zero exit -- exit 0 would make the
        # refusal indistinguishable from success.
        echo "Error: refusing to release -- ownership could not be verified (${OWNER_REPORT}). Supply --token with the value returned at acquire time, or have the operator run: release_lock.sh $(shell_quote "${FILEPATH}") --force" >&2
        exit 1
    fi
    echo "Warning: --force supplied; breaking this lock without a verified token (${OWNER_REPORT}). O3: this is an advisory lock, not an adversarial guarantee -- only the operator should do this." >&2
fi

if [ "$OWNERSHIP_VERIFIED" -eq 1 ]; then
    # Round-9 review follow-up (TOCTOU race): ownership was verified above
    # against a SNAPSHOT of the lock file read earlier in this script.
    # Between that read and the `rm -f` below, another legitimate release
    # could have removed this same lock and a new owner could have
    # acquired a DIFFERENT lock at the same path; without a recheck, `rm -f`
    # would delete whatever currently occupies the pathname -- i.e. the new
    # owner's lock -- using this process's now-stale token verification.
    # Re-reading owner_digest immediately before deletion and refusing to
    # proceed unless it still matches narrows (though, absent an atomic
    # compare-and-delete filesystem primitive, cannot fully eliminate) that
    # race window. This mitigation only applies to the token-verified path;
    # --force remains an unconditional operator override per O3 and is not
    # re-checked here.
    if [ -n "${AUTOHARNESS_TEST_RELEASE_RACE_DELAY_MS:-}" ]; then
        # TEST-ONLY HOOK: deterministically widens the TOCTOU window so an
        # automated test can inject a concurrent lock change between this
        # verification and the recheck below. Never set outside test runs;
        # when the environment variable is absent (the default), this is a
        # complete no-op with zero behavioural or timing impact.
        if [ -n "${AUTOHARNESS_TEST_RELEASE_RACE_SIGNAL:-}" ]; then
            # TEST-ONLY HOOK: signals the harness that this process has
            # entered the widened race window, so the test can perform the
            # concurrent swap deterministically instead of guessing at
            # process-startup timing. Round-11 review follow-up: the
            # signal path is ALWAYS derived here from the already-resolved,
            # already-contained $LOCKFILE -- this toggle only turns the
            # signal on/off, it never accepts a caller-supplied path, so a
            # stray inherited environment variable cannot be used to
            # truncate or create an arbitrary file anywhere on the host.
            # Never set outside test runs.
            : > "$LOCKFILE.race-signal"
        fi
        _delay_seconds="$(awk -v ms="$AUTOHARNESS_TEST_RELEASE_RACE_DELAY_MS" 'BEGIN { printf "%f", ms / 1000 }')"
        sleep "$_delay_seconds"
    fi
    if [ ! -e "$LOCKFILE" ]; then
        echo "Warning: lock file disappeared before deletion could be confirmed (already released by another process): $LOCKFILE" >&2
        exit 0
    fi
    RECHECK_CONTENT="$(cat "$LOCKFILE")"
    RECHECK_DIGEST="$(printf '%s\n' "$RECHECK_CONTENT" | sed -n 's/^owner_digest: //p' | tail -n1)"
    RECHECK_DIGEST_LOWER="$(printf '%s' "$RECHECK_DIGEST" | tr '[:upper:]' '[:lower:]')"
    if [ -z "$RECHECK_DIGEST" ] || [ "$RECHECK_DIGEST_LOWER" != "$RECORDED_DIGEST_LOWER" ]; then
        echo "Error: refusing to release -- the lock at '$LOCKFILE' changed between verification and deletion (a different owner now holds it); this process's token no longer matches the current owner. Re-run release to re-verify against the new owner, or have the operator use --force." >&2
        exit 1
    fi
fi

if rm -f "$LOCKFILE"; then
    echo "Lock released: $LOCKFILE"
    exit 0
else
    echo "Error: Failed to remove lock file: $LOCKFILE" >&2
    exit 1
fi
