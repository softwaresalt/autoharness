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

# Finding 6 fix: normalise to an absolute path via `realpath -m` unconditionally
# -- this canonicalises as much of the path as exists and works whether or not
# the target itself exists, so dirname/basename never operate on an
# unnormalised relative root-level filename.
TARGET_PATH="$(realpath -m "$FILEPATH")"

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

OWNERSHIP_VERIFIED=0
if [ -n "$RECORDED_DIGEST" ] && [ -n "$TOKEN" ]; then
    SUPPLIED_DIGEST="$(compute_digest "$TOKEN")"
    SUPPLIED_DIGEST_LOWER="$(printf '%s' "$SUPPLIED_DIGEST" | tr '[:upper:]' '[:lower:]')"
    RECORDED_DIGEST_LOWER="$(printf '%s' "$RECORDED_DIGEST" | tr '[:upper:]' '[:lower:]')"
    if [ "$SUPPLIED_DIGEST_LOWER" = "$RECORDED_DIGEST_LOWER" ]; then
        OWNERSHIP_VERIFIED=1
    fi
fi

# O2: possession of a token hashing to the recorded owner_digest is the
# capability check. O1: agent/pid/timestamp are courtesy identity only and
# carry no authorisation weight. TC5d: the refusal/warning below names
# agent/pid/timestamp but NEVER the token or owner_digest.
if [ "$OWNERSHIP_VERIFIED" -ne 1 ]; then
    OWNER_REPORT="agent=${RECORDED_AGENT}, pid=${RECORDED_PID}, timestamp=${RECORDED_TIMESTAMP}"
    if [ "$FORCE" -ne 1 ]; then
        # Decision (iii): refusal is a non-zero exit -- exit 0 would make the
        # refusal indistinguishable from success.
        echo "Error: refusing to release -- ownership could not be verified (${OWNER_REPORT}). Supply --token with the value returned at acquire time, or have the operator supply --force." >&2
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
