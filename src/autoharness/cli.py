"""Thin CLI for autoharness — resolves installation paths for AI coding agents."""

from __future__ import annotations

import sys
from pathlib import Path

# The data directory is bundled inside the package at build time.
# In a dev/editable install, fall back to the repo root.
_PACKAGE_DIR = Path(__file__).resolve().parent
_DATA_DIR = _PACKAGE_DIR / "data"

if not _DATA_DIR.exists():
    # Editable / dev install — repo root is two levels up from src/autoharness/
    _DATA_DIR = _PACKAGE_DIR.parent.parent


def _home() -> Path:
    """Return the autoharness home directory containing templates, schemas, etc."""
    return _DATA_DIR


def _version() -> str:
    from autoharness import __version__
    return __version__


USAGE = """\
autoharness — agent harness framework

Usage:
  autoharness home       Print the autoharness installation path
  autoharness version    Print the installed version
  autoharness help       Show this message

Install:
  uv tool install autoharness
  uv tool install git+https://github.com/softwaresalt/autoharness.git

Update:
  uv tool upgrade autoharness

The AI coding assistant is the runtime. This CLI exists only so agents
can resolve the autoharness home path via `autoharness home`.
"""


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h"):
        print(USAGE)
        return

    command = args[0]

    if command == "home":
        print(_home())
    elif command == "version":
        print(_version())
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
