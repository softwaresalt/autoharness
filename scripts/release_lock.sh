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
# Usage: scripts/release_lock.sh <filepath> [--token <token>] [--force]

set -euo pipefail

FILEPATH=""
TOKEN="${LOCK_TOKEN:-}"
FORCE=0

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
        *)
            if [ -z "$FILEPATH" ]; then
                FILEPATH="$1"
            else
                echo "Usage: release_lock.sh <filepath> [--token <token>] [--force]" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$FILEPATH" ]; then
    echo "Usage: release_lock.sh <filepath> [--token <token>] [--force]" >&2
    exit 1
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
if [ -e "$FILEPATH" ]; then
    TARGET_PATH="$(realpath "$FILEPATH")"
else
    PARENT_DIR="$(dirname "$FILEPATH")"
    LEAF_NAME="$(basename "$FILEPATH")"
    if [ ! -d "$PARENT_DIR" ]; then
        # A missing parent directory means no lock file could possibly
        # exist beside this target either -- a lock file always lives in
        # the same directory as its target. This mirrors the PowerShell
        # variant, which never errors on a missing parent (GetFullPath is
        # pure string normalisation with no filesystem access), and the
        # documented "no lock file exists" contract: a warning and a
        # successful exit, not a failure.
        echo "Warning: No lock file found for: $FILEPATH (parent directory does not exist; already released or never locked)" >&2
        exit 0
    fi
    TARGET_PATH="$(realpath "$PARENT_DIR")/${LEAF_NAME}"
fi

RESOLVED_DIR="$(dirname "$TARGET_PATH")"
FILENAME="$(basename "$TARGET_PATH")"
LOCKFILE="${RESOLVED_DIR}/.${FILENAME}.lock"

if [ ! -e "$LOCKFILE" ]; then
    echo "Warning: No lock file found for: $FILEPATH (already released or never locked)" >&2
    exit 0
fi

LOCK_CONTENT="$(cat "$LOCKFILE")"
RECORDED_DIGEST="$(printf '%s\n' "$LOCK_CONTENT" | sed -n 's/^owner_digest: //p' | head -n1)"
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
        echo "Error: refusing to release -- ownership could not be verified (${OWNER_REPORT}). Supply --token with the value returned at acquire time, or have the operator run: release_lock.sh '${FILEPATH}' --force" >&2
        exit 1
    fi
    echo "Warning: --force supplied; breaking this lock without a verified token (${OWNER_REPORT}). O3: this is an advisory lock, not an adversarial guarantee -- only the operator should do this." >&2
fi

if rm -f "$LOCKFILE"; then
    echo "Lock released: $LOCKFILE"
    exit 0
else
    echo "Error: Failed to remove lock file: $LOCKFILE" >&2
    exit 1
fi
