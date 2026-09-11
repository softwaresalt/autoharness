#!/usr/bin/env bash
# Acquires an advisory file lock for agent concurrency control.
# Creates a .{filename}.lock file in the same directory as the target file.
# Fails with exit code 1 if the lock already exists (another process holds it).
#
# Enforces workspace-root containment (H2/H4): the target file must resolve,
# after full symlink dereferencing (`realpath`), to a path inside the
# workspace root. Containment is decided by path-segment comparison (never a
# bare string prefix), so a sibling directory that merely shares the root's
# name as a string prefix (e.g. `ws-evil` vs `ws`) is never mistaken for a
# contained path.
#
# Usage: scripts/acquire_lock.sh <filepath> [--workspace-root <path>]

set -euo pipefail

WORKSPACE_ROOT=""
FILEPATH=""
while [ $# -gt 0 ]; do
    case "$1" in
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
                echo "Usage: acquire_lock.sh <filepath> [--workspace-root <path>]" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$FILEPATH" ]; then
    echo "Usage: acquire_lock.sh <filepath> [--workspace-root <path>]" >&2
    exit 1
fi

# --- Resolve the workspace root -------------------------------------------
#
# When --workspace-root is omitted, derive a default from
# `git rev-parse --show-toplevel` run from this script's own directory, but
# trust it only when this script's own directory is a direct `scripts` child
# of the derived top-level. This guards against a nested checkout with no
# `.git` of its own silently widening to an ancestor repository's root
# (finding 2): in that scenario the derived root's `scripts` child does not
# match this script's own directory, so the check fails closed and the
# caller must supply --workspace-root explicitly.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

if [ -n "$WORKSPACE_ROOT" ]; then
    if [ ! -e "$WORKSPACE_ROOT" ]; then
        echo "Error: --workspace-root does not exist: $WORKSPACE_ROOT" >&2
        exit 1
    fi
    REAL_ROOT="$(realpath "$WORKSPACE_ROOT")"
else
    GIT_TOPLEVEL="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
    if [ -z "$GIT_TOPLEVEL" ]; then
        echo "Error: no --workspace-root supplied and no git repository found from this script's directory; pass --workspace-root explicitly." >&2
        exit 1
    fi
    REAL_GIT_TOPLEVEL="$(realpath "$GIT_TOPLEVEL")"
    if [ -d "${REAL_GIT_TOPLEVEL}/scripts" ]; then
        EXPECTED_SCRIPTS_DIR="$(realpath "${REAL_GIT_TOPLEVEL}/scripts")"
    else
        EXPECTED_SCRIPTS_DIR="${REAL_GIT_TOPLEVEL}/scripts"
    fi
    if [ "$EXPECTED_SCRIPTS_DIR" != "$SCRIPT_DIR" ]; then
        echo "Error: git-derived root '$REAL_GIT_TOPLEVEL' does not match this script's own installed location; this workspace is likely a nested checkout without its own .git (widening guard, finding 2). Pass --workspace-root explicitly." >&2
        exit 1
    fi
    REAL_ROOT="$REAL_GIT_TOPLEVEL"
fi

if [ ! -e "$FILEPATH" ]; then
    echo "Error: Target file does not exist: $FILEPATH" >&2
    exit 1
fi

REAL_TARGET="$(realpath "$FILEPATH")"

# Path-segment containment: equal to the root, or the root plus a trailing
# separator followed by the rest. Never a bare string prefix.
case "$REAL_TARGET" in
    "$REAL_ROOT")
        ;;
    "$REAL_ROOT"/*)
        ;;
    *)
        echo "Error: target path escapes the workspace root and was rejected (root=$REAL_ROOT, target=$REAL_TARGET)." >&2
        exit 1
        ;;
esac

DIRECTORY="$(dirname "$REAL_TARGET")"
FILENAME="$(basename "$REAL_TARGET")"
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
