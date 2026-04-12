#!/usr/bin/env bash
# Acquires an advisory file lock for agent concurrency control.
# Creates a .{filename}.lock file in the same directory as the target file.
# Fails with exit code 1 if the lock already exists (another process holds it).
#
# Usage: scripts/acquire_lock.sh <filepath>

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: acquire_lock.sh <filepath>" >&2
    exit 1
fi

FILEPATH="$1"

if [ ! -e "$FILEPATH" ]; then
    echo "Error: Target file does not exist: $FILEPATH" >&2
    exit 1
fi

RESOLVED_PATH="$(realpath "$FILEPATH")"
DIRECTORY="$(dirname "$RESOLVED_PATH")"
FILENAME="$(basename "$RESOLVED_PATH")"
LOCKFILE="${DIRECTORY}/.${FILENAME}.lock"

if [ -e "$LOCKFILE" ]; then
    echo "Warning: Lock already held on: $FILEPATH" >&2
    echo "Warning: Lock info: $(cat "$LOCKFILE")" >&2
    exit 1
fi

AGENT_NAME="${AGENT_NAME:-unknown}"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
PID_VAL="$$"

LOCK_CONTENT="agent: ${AGENT_NAME}
timestamp: ${TIMESTAMP}
pid: ${PID_VAL}
file: ${FILEPATH}"

# Use exclusive file creation to minimize race window
if (set -o noclobber; echo "$LOCK_CONTENT" > "$LOCKFILE") 2>/dev/null; then
    echo "Lock acquired: $LOCKFILE"
    exit 0
else
    echo "Warning: Lock already held on: $FILEPATH (race condition)" >&2
    exit 1
fi
