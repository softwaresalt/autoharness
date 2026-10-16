"""Test helper: makes "the resolver performs no I/O" a tested property.

Stdlib only. A flat module (not collected by discovery), like `_env_patch.py`.
`forbid_io()` patches filesystem, environment, process, and network entry
points so any use raises `ImpureAccessError`; `assert_module_import_pure`
statically closes the bypasses a runtime patch cannot see (names bound at
import time and function-local imports).
"""

from __future__ import annotations

import ast
import builtins
import contextlib
import io
import os
import pathlib
import socket
import subprocess
from pathlib import Path
from typing import Any, Callable, Iterator


class ImpureAccessError(AssertionError):
    """Raised when guarded code touches the filesystem, environment, a process, or the network."""


_PATH_METHODS = (
    "open",
    "read_text",
    "read_bytes",
    "write_text",
    "write_bytes",
    "stat",
    "lstat",
    "exists",
    "is_file",
    "is_dir",
    "iterdir",
    "glob",
    "rglob",
    "resolve",
    "cwd",
)

_MISSING = object()


class _RaisingEnviron:
    def __init__(self, trip: Callable[[str], Any]) -> None:
        self._trip = trip

    def __getattr__(self, name: str) -> Any:
        return self._trip(f"os.environ.{name}")

    def __getitem__(self, key: Any) -> Any:
        return self._trip("os.environ[...]")

    def __setitem__(self, key: Any, value: Any) -> None:
        self._trip("os.environ[...]=")

    def __delitem__(self, key: Any) -> None:
        self._trip("del os.environ[...]")

    def __contains__(self, key: Any) -> bool:
        return self._trip("os.environ.__contains__")

    def __iter__(self) -> Iterator[Any]:
        return self._trip("iter(os.environ)")

    def __len__(self) -> int:
        return self._trip("len(os.environ)")


class forbid_io(contextlib.AbstractContextManager):
    """Context manager: every guarded entry point raises `ImpureAccessError`.

    Violations are also recorded, and `__exit__` raises if any was recorded,
    so code that swallows the error with `except Exception` still fails.
    """

    def __init__(self) -> None:
        self.violations: list[str] = []
        self._restores: list[Callable[[], None]] = []

    def _trip(self, channel: str) -> Any:
        self.violations.append(channel)
        raise ImpureAccessError(f"impure access through {channel}")

    def _stub(self, channel: str) -> Callable[..., Any]:
        def stub(*args: Any, **kwargs: Any) -> Any:
            return self._trip(channel)

        return stub

    def _patch(self, target: Any, name: str, replacement: Any) -> None:
        in_dict = isinstance(target, type) and name in target.__dict__
        original = getattr(target, name, _MISSING)
        setattr(target, name, replacement)

        def restore() -> None:
            if isinstance(target, type) and not in_dict:
                delattr(target, name)
            elif original is _MISSING:
                delattr(target, name)
            else:
                setattr(target, name, original)

        self._restores.append(restore)

    def __enter__(self) -> "forbid_io":
        self.violations = []
        self._restores = []
        try:
            self._patch(builtins, "open", self._stub("builtins.open"))
            self._patch(io, "open", self._stub("io.open"))
            for name in ("open", "stat", "lstat", "scandir", "listdir", "getcwd", "getenv", "putenv", "system", "popen"):
                self._patch(os, name, self._stub(f"os.{name}"))
            for name in ("exists", "isfile", "isdir"):
                self._patch(os.path, name, self._stub(f"os.path.{name}"))
            for name in _PATH_METHODS:
                self._patch(pathlib.Path, name, self._stub(f"pathlib.Path.{name}"))
            self._patch(os, "environ", _RaisingEnviron(self._trip))
            self._patch(subprocess, "Popen", self._stub("subprocess.Popen"))
            self._patch(socket, "socket", self._stub("socket.socket"))
            self._patch(socket, "create_connection", self._stub("socket.create_connection"))
            self._patch(socket, "getaddrinfo", self._stub("socket.getaddrinfo"))
        except BaseException:
            self._restore()
            raise
        return self

    def _restore(self) -> None:
        while self._restores:
            self._restores.pop()()

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        self._restore()
        if self.violations and not isinstance(exc, ImpureAccessError):
            raise ImpureAccessError(f"impure access recorded: {', '.join(self.violations)}") from exc
        return False


def guarded_resolve(*args: Any, **kwargs: Any) -> Any:
    """Call `model_routing.resolve_site` with all I/O forbidden."""
    from autoharness import model_routing

    resolve = model_routing.resolve_site
    with forbid_io():
        return resolve(*args, **kwargs)


ALLOWED_IMPORT_MODULES = frozenset(
    {"__future__", "dataclasses", "typing", "collections.abc", "enum", "re", "types"}
)
ALLOWED_FROM_IMPORTS = {"autoharness.frontmatter_contract": frozenset({"CONTEXT_TIER_VALUES"})}
FORBIDDEN_NAMES = frozenset(
    {"os", "io", "sys", "pathlib", "subprocess", "socket", "shutil", "tempfile", "yaml", "open", "environ", "getenv"}
)


def assert_source_import_pure(source: str, name: str = "<module>") -> None:
    """AST walk over every import and name (including function-local imports)."""
    problems: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_IMPORT_MODULES:
                    problems.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = ("." * node.level) + (node.module or "")
            allowed_names = ALLOWED_FROM_IMPORTS.get(module)
            if allowed_names is not None:
                extra = {a.name for a in node.names} - allowed_names
                if extra:
                    problems.append(f"line {node.lineno}: from {module} import {sorted(extra)}")
            elif module not in ALLOWED_IMPORT_MODULES:
                problems.append(f"line {node.lineno}: from {module} import ...")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            problems.append(f"line {node.lineno}: name {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_NAMES:
            problems.append(f"line {node.lineno}: attribute .{node.attr}")
    if problems:
        raise AssertionError(f"{name} is not import-pure: " + "; ".join(problems))


def assert_module_import_pure(module: Any) -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert_source_import_pure(source, getattr(module, "__name__", "<module>"))
