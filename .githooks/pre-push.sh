#!/usr/bin/env bash
# .githooks/pre-push.sh
# autoharness dogfood instance of the unified CI + local-gating primitive (P-019).
# Generated from templates/scripts/pre-push-quality-gates.sh.tmpl, resolved for
# autoharness's real toolchain: the stdlib unittest suite + markdownlint.
#
# Runs the local quality gates before a push and BLOCKS the push (exit 1) on any
# failure. markdownlint is skipped with a warning when not installed. Single
# deterministic pass — no retry loop (circuit-breaker compatible).
#
# OPT-IN activation (see .githooks/README.md). This hook is committed but NOT
# active by default; nothing in the repo sets core.hooksPath for you.

set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

# Drain stdin (ref updates) so git does not see a broken pipe.
cat >/dev/null 2>&1 || true

FAILED=0

echo "[Test] PYTHONPATH=src python -m unittest discover -s tests"
if ! PYTHONPATH=src python -m unittest discover -s tests; then
  echo "ERROR: unittest suite failed — push blocked (P-019)." >&2
  FAILED=1
fi

if command -v markdownlint >/dev/null 2>&1; then
  echo "[Docs] markdownlint '**/*.md'"
  if ! markdownlint "**/*.md"; then
    echo "ERROR: markdownlint failed (P-008) — push blocked." >&2
    FAILED=1
  fi
else
  echo "WARNING: markdownlint not found — skipping Markdown lint gate." >&2
  echo "         Install with: npm install -g markdownlint-cli" >&2
fi

if [ "$FAILED" -ne 0 ]; then
  echo "One or more quality gates failed. Fix them, or push with --no-verify to bypass." >&2
  exit 1
fi

echo "All local quality gates passed."
exit 0
