"""Sole authority for workspace bootstrap policy (120.001-T).

Consolidates the workspace-bootstrap logic that was previously duplicated
between ``start.ps1`` and ``start.sh`` (``.env.local`` loading,
``COPILOT_HOME``/``ENGRAM_DATA_DIR`` defaulting, GitHub token resolution)
into a single, unit-testable, platform-branch-free module.

Deliberate unifications relative to the pre-migration scripts (documented
here and in ``docs/design-docs/``):

* **DELTA 1 (WINDOWS_PAT_NO_GH)** -- ``gh`` absent or failing is now
  non-fatal on Windows exactly as it always was on POSIX: a warning is
  recorded and the affected variable is left UNSET (never an empty-string
  placeholder).
* **DELTA 2 (POSIX_ENGRAM_DATA_DIR)** -- ``ENGRAM_DATA_DIR`` now defaults to
  ``<workspace_root>/.engram`` on POSIX too (today's ``start.sh`` has this
  line present but commented out).
* **DELTA 3 (POSIX_PAT_BOOTSTRAP)** -- ``GITHUB_TOKEN``/
  ``GITHUB_PERSONAL_ACCESS_TOKEN`` resolution via ``gh auth token`` now runs
  on POSIX too (today's ``start.sh`` has no PAT handling at all), with the
  SAME non-fatal-on-``gh``-absent/failing contract as Windows.

Deliberately NOT unified (preserved byte-identical to the pre-migration
Windows script, on both platforms): ``GITHUB_TOKEN`` remains guarded
(NO-CLOBBER -- ``gh`` is never invoked for it once set) while
``GITHUB_PERSONAL_ACCESS_TOKEN`` remains UNGUARDED (always re-resolved via
``gh`` whenever it is available, even if already set), exactly mirroring
``start.ps1``'s own pre-existing per-variable asymmetry
(``$env:GITHUB_PERSONAL_ACCESS_TOKEN = (gh auth token)`` unconditionally vs.
``if (-not $env:GITHUB_TOKEN) { ... }``). Unifying the two variables' guard
behavior with each other would be an unnamed fourth delta outside the
approved three-entry matrix (ruling A, 2026-08-12) -- see
:data:`_TOKEN_VAR_NO_CLOBBER`.

This module never uses ``shell=True`` for the ``gh`` subprocess call
(always an argv list), never mutates ``os.environ`` directly (the resolved
additions are returned for the caller to apply), and NEVER puts a raw
resolved secret value into ``warnings``/``messages`` -- only variable NAMES
and boolean/status information. The actual resolved secret value only ever
appears in :attr:`BootstrapResult.env`, which the caller is expected to
apply to a CHILD process environment (never logged/journaled/echoed
verbatim by this module itself). Every resolved secret is ALSO registered
with the redactor (:func:`autoharness.supervise.redact.register_secret` or
an injected :class:`~autoharness.supervise.redact.Redactor`) so it is
caught by any downstream emission path even if it matches no regex pattern
(H5).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, MutableMapping, Optional

from autoharness.supervise.redact import (
    Redactor,
    register_secret,
)
from autoharness.supervise.redact import _SECRET_KEY_PATTERN as _REDACT_SECRET_KEY_PATTERN

#: Matches a KEY=VALUE line. Deliberately permissive on case (a superset of
#: both start.ps1's incidentally-case-insensitive `-match` and start.sh's
#: explicitly case-inclusive `[A-Za-z_][A-Za-z0-9_]*`), so a bootstrap
#: written for either legacy script's .env.local convention parses
#: identically here.
_ENV_LINE_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*\r?$")

#: Variables this module resolves via `gh auth token`, in resolution order.
_TOKEN_VAR_NAMES: tuple[str, ...] = ("GITHUB_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN")


@dataclass(frozen=True)
class BootstrapResult:
    """Typed, frozen outcome of :func:`bootstrap_workspace`.

    Attributes:
        env: The resolved env ADDITIONS only (name -> value) -- i.e. every
            variable this call actually set because it was not already
            present (or was present-but-empty for the truthy-default
            variables). This INCLUDES resolved secret values so a caller can
            apply them directly to a child process environment; it never
            includes a variable that was already set (NO-CLOBBER) or that
            gh resolution left deliberately unset.
        warnings: Human-readable non-fatal warnings (variable NAMES and
            status only -- never a raw secret value).
        messages: Human-readable informational messages.
    """

    env: Mapping[str, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    messages: tuple[str, ...] = ()


def _strip_matching_quotes(value: str) -> str:
    """Strip a SINGLE matching pair of surrounding quotes (' or "), if present."""

    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _parse_env_local(text: str) -> list[tuple[str, str]]:
    """Parse ``.env.local`` content into an ordered list of (key, value) pairs.

    Non-KEY=VALUE lines (comments, blank lines, malformed assignments) are
    silently skipped, mirroring both legacy scripts' baseline behavior.
    """

    pairs: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        match = _ENV_LINE_PATTERN.match(raw_line)
        if match is None:
            continue
        name = match.group(1)
        value = _strip_matching_quotes(match.group(2))
        pairs.append((name, value))
    return pairs


def _load_env_local(
    workspace_root: Path,
    working_env: MutableMapping[str, str],
    resolved: MutableMapping[str, str],
    messages: list[str],
    redactor: Optional[Redactor] = None,
) -> None:
    """Load ``.env.local`` (NO-CLOBBER) and register secret-shaped values.

    **Fix (P-018 Copilot review finding, PR #331, comment 3778627788)**:
    previously only ``GITHUB_TOKEN``/``GITHUB_PERSONAL_ACCESS_TOKEN`` values
    were ever registered with the redactor -- any OTHER secret-named
    ``.env.local`` entry (e.g. the documented ``TAVILY_API_KEY=...``) was
    copied into the child environment but never protected, so a value a
    child happened to echo back on stdout/stderr could reach the journal or
    bus completely unredacted (it matches no GitHub-token-shaped regex and
    was never registered). Every loaded value whose KEY NAME matches the
    same ``TOKEN|SECRET|KEY|PASSWORD`` pattern used for mapping-key
    redaction (:data:`autoharness.supervise.redact._SECRET_KEY_PATTERN`,
    reused here rather than duplicated to avoid the two patterns drifting
    out of sync) is now registered with the redactor at load time,
    regardless of whether this module's own token-resolution logic ever
    looks at that variable again.
    """

    env_local_path = workspace_root / ".env.local"
    if not env_local_path.is_file():
        return

    text = env_local_path.read_text(encoding="utf-8")
    for name, value in _parse_env_local(text):
        if _REDACT_SECRET_KEY_PATTERN.search(name) and value:
            if redactor is not None:
                redactor.register_secret(value)
            else:
                register_secret(value)
        if name in working_env:
            continue  # NO-CLOBBER: an already-set variable always wins.
        working_env[name] = value
        resolved[name] = value
    messages.append(f"loaded .env.local from {env_local_path}")


def _apply_directory_default(
    var_name: str,
    default_value: str,
    working_env: MutableMapping[str, str],
    resolved: MutableMapping[str, str],
) -> None:
    """Default ``var_name`` to ``default_value`` unless already set (truthy).

    An empty-string pre-set value is treated as unset, mirroring both
    legacy scripts' truthy-check default conventions
    (`${VAR:-default}` in bash; `if ($env:VAR) { ... }` in PowerShell).
    """

    if working_env.get(var_name):
        return
    working_env[var_name] = default_value
    resolved[var_name] = default_value


#: Per-variable NO-CLOBBER guard, EXACTLY mirroring the pre-migration
#: start.ps1 asymmetry (byte-identical preservation outside the three named
#: deltas): GITHUB_TOKEN was already guarded (`if (-not $env:GITHUB_TOKEN)`)
#: and already non-fatal on a gh failure there; GITHUB_PERSONAL_ACCESS_TOKEN
#: was UNGUARDED (`$env:GITHUB_PERSONAL_ACCESS_TOKEN = (gh auth token)`,
#: always (re)assigned) and was the ONLY one that was FATAL on gh-absent --
#: DELTA 1 makes that one variable's gh-absent/failing case non-fatal too,
#: on both platforms, without otherwise changing its unguarded semantics.
#: This module deliberately does NOT unify the two variables' guard
#: behavior with each other -- doing so would be an unnamed fourth delta
#: outside the approved three-entry matrix (ruling A, 2026-08-12).
_TOKEN_VAR_NO_CLOBBER: Mapping[str, bool] = {
    "GITHUB_TOKEN": True,
    "GITHUB_PERSONAL_ACCESS_TOKEN": False,
}


def _resolve_one_github_token(
    var_name: str,
    working_env: MutableMapping[str, str],
    resolved: MutableMapping[str, str],
    warnings: list[str],
    gh_executable: str,
    redactor: Optional[Redactor],
) -> None:
    """Resolve a single GITHUB_TOKEN/GITHUB_PERSONAL_ACCESS_TOKEN variable.

    Preserves the pre-migration per-variable guard asymmetry (see
    :data:`_TOKEN_VAR_NO_CLOBBER`) exactly: a NO-CLOBBER variable already
    set is left untouched and `gh` is never invoked for it; a non-guarded
    variable is (re)resolved unconditionally whenever `gh` is available.

    gh being absent or failing is ALWAYS non-fatal (DELTA 1 / DELTA 3 on
    POSIX): a warning naming the missing tool and the left-unset variable is
    recorded, and the variable is left UNSET -- never assigned an empty
    string. The resolved secret VALUE, when found, is registered with the
    redactor (H5) and is the only place it appears outside the returned
    ``env`` mapping.

    **Preset-value redaction (P-018 Copilot review finding, PR #331,
    comment 3778408843)**: a value ALREADY present in ``working_env``
    (e.g. a nonstandard ``GITHUB_TOKEN`` loaded from ``.env.local``) is now
    registered with the redactor unconditionally, BEFORE the no-clobber/gh
    resolution logic below runs. Previously, the NO-CLOBBER early return
    skipped registration entirely for a preset ``GITHUB_TOKEN``, so
    captured child output containing that value would bypass both the
    built-in token regexes and registered-value redaction. Registration is
    idempotent (registering the same secret value twice is harmless) and
    happens regardless of which branch (no-clobber early return, gh
    success, gh failure) this call ultimately takes.
    """

    preset_value = working_env.get(var_name)
    if preset_value:
        if redactor is not None:
            redactor.register_secret(preset_value)
        else:
            register_secret(preset_value)

    if _TOKEN_VAR_NO_CLOBBER[var_name] and preset_value:
        return  # NO-CLOBBER: already set, gh is never invoked for this var.

    resolved_path = shutil.which(gh_executable)
    if resolved_path is None:
        warnings.append(f"{gh_executable!r} not found on PATH; leaving unset: {var_name}")
        return

    try:
        proc = subprocess.run(
            [resolved_path, "auth", "token"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        warnings.append(
            f"{gh_executable!r} auth token invocation failed ({type(exc).__name__}); "
            f"leaving unset: {var_name}"
        )
        return

    if proc.returncode != 0:
        warnings.append(
            f"{gh_executable!r} auth token exited {proc.returncode}; leaving unset: {var_name}"
        )
        return

    token = proc.stdout.strip()
    if not token:
        warnings.append(f"{gh_executable!r} auth token returned no output; leaving unset: {var_name}")
        return

    if redactor is not None:
        redactor.register_secret(token)
    else:
        register_secret(token)

    working_env[var_name] = token
    resolved[var_name] = token


def _resolve_github_tokens(
    working_env: MutableMapping[str, str],
    resolved: MutableMapping[str, str],
    warnings: list[str],
    gh_executable: str,
    redactor: Optional[Redactor],
) -> None:
    """Resolve GITHUB_TOKEN/GITHUB_PERSONAL_ACCESS_TOKEN via `gh auth token`.

    Each variable is resolved independently, preserving the pre-migration
    per-variable guard/call-count asymmetry (see
    :data:`_TOKEN_VAR_NO_CLOBBER` and :func:`_resolve_one_github_token`) --
    this can invoke `gh auth token` up to twice, exactly matching the
    pre-migration start.ps1 call pattern (PAT first, unguarded; GITHUB_TOKEN
    second, guarded), now extended non-fatally to both platforms (DELTA 1 /
    DELTA 3).
    """

    for var_name in _TOKEN_VAR_NAMES:
        _resolve_one_github_token(var_name, working_env, resolved, warnings, gh_executable, redactor)


def bootstrap_workspace(
    workspace_root: Path,
    *,
    env: Optional[MutableMapping[str, str]] = None,
    gh_executable: str = "gh",
    redactor: Optional[Redactor] = None,
) -> BootstrapResult:
    """Resolve workspace bootstrap policy. Never mutates ``os.environ``.

    ``env`` (when given) is treated as the CALLER's baseline environment
    mapping -- it is copied, never mutated in place, and never assumed to
    be ``os.environ`` itself. When ``env`` is ``None``, a COPY of
    ``os.environ`` is used as the baseline.

    Returns a :class:`BootstrapResult` whose ``env`` field carries ONLY the
    additions this call actually resolved (see the class docstring) so a
    caller can merge them onto whatever child-process environment it is
    constructing.
    """

    workspace_root = Path(workspace_root)
    working_env: dict[str, str] = dict(env) if env is not None else dict(os.environ)

    resolved: dict[str, str] = {}
    warnings: list[str] = []
    messages: list[str] = []

    _load_env_local(workspace_root, working_env, resolved, messages, redactor)

    _apply_directory_default(
        "COPILOT_HOME", str(workspace_root / ".copilot"), working_env, resolved
    )
    # DELTA 2: ENGRAM_DATA_DIR now defaults on BOTH platforms -- no
    # platform branch, unlike today's start.sh (commented out) vs
    # start.ps1 (active).
    _apply_directory_default(
        "ENGRAM_DATA_DIR", str(workspace_root / ".engram"), working_env, resolved
    )

    # DELTA 1 / DELTA 3: token resolution runs on BOTH platforms with the
    # SAME non-fatal-on-gh-absent-or-failing contract.
    _resolve_github_tokens(working_env, resolved, warnings, gh_executable, redactor)

    return BootstrapResult(env=resolved, warnings=tuple(warnings), messages=tuple(messages))
