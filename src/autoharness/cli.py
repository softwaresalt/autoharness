"""Thin CLI for autoharness — resolves installation paths for AI coding agents."""

from __future__ import annotations

import json
import os
import platform
import shutil
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
  autoharness home              Print the autoharness installation path
  autoharness version           Print the installed version
  autoharness setup-vscode      Write agent discovery entries to VS Code user settings
  autoharness setup-copilot-cli Copy agents and skills into the Copilot CLI global config dir
  autoharness setup-claude      Copy agents and skills into the Claude Code global config dir
  autoharness setup-codex       Copy skills into the Codex global config dir
  autoharness help              Show this message

Install:
  uv tool install autoharness
  uv tool install git+https://github.com/softwaresalt/autoharness.git

Update:
  uv tool upgrade autoharness

The AI coding assistant is the runtime. This CLI exists only so agents
can resolve the autoharness home path via `autoharness home`.
"""


def _vscode_user_settings_path() -> Path | None:
    """Return the platform-appropriate VS Code user settings path (no tilde)."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None
        return Path(appdata) / "Code" / "User" / "settings.json"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "settings.json"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / "Code" / "User" / "settings.json"


def _strip_jsonc(text: str) -> str:
    """Strip JSONC comments and trailing commas without touching quoted strings.

    Uses a character-level state machine that tracks string boundaries so that
    comment-like sequences inside string values are never removed.
    """
    # Phase 1: strip comments
    result: list[str] = []
    i = 0
    in_string = False
    escape = False
    in_line_comment = False
    in_block_comment = False

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                result.append(ch)
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if in_string:
            result.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            result.append(ch)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue

        result.append(ch)
        i += 1

    if in_string:
        raise ValueError("Invalid JSONC: unterminated string literal in VS Code settings.")
    if in_block_comment:
        raise ValueError("Invalid JSONC: unterminated block comment in VS Code settings.")

    # Phase 2: strip trailing commas before } or ]
    stripped = "".join(result)
    cleaned: list[str] = []
    in_string = False
    escape = False
    i = 0

    while i < len(stripped):
        ch = stripped[i]

        if in_string:
            cleaned.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            cleaned.append(ch)
            i += 1
            continue

        if ch == ",":
            j = i + 1
            while j < len(stripped) and stripped[j] in " \t\r\n":
                j += 1
            if j < len(stripped) and stripped[j] in "}]":
                i += 1
                continue

        cleaned.append(ch)
        i += 1

    if in_string:
        raise ValueError("Invalid JSONC: unterminated string literal in VS Code settings.")

    return "".join(cleaned)


def _setup_vscode() -> None:
    """Write autoharness agent discovery entries into VS Code user settings."""
    home = _home()
    settings_path = _vscode_user_settings_path()

    if settings_path is None:
        print("Error: could not determine VS Code user settings path for this OS.", file=sys.stderr)
        sys.exit(1)

    # Build path keys using fully-resolved absolute paths — no tilde, no variables.
    # Use POSIX (forward-slash) paths so the same key works on all platforms and
    # avoids duplicate entries if the user already has forward-slash keys.
    agents_path  = home / ".github" / "agents"
    skills_path  = home / ".github" / "skills"
    prompts_path = home / ".github" / "prompts"

    entries = [
        ("chat.agentFilesLocations",  agents_path.as_posix()),
        ("chat.agentSkillsLocations", skills_path.as_posix()),
        ("chat.promptFilesLocations", prompts_path.as_posix()),
    ]

    # Read existing settings, tolerating JSONC comments.
    if settings_path.exists():
        raw = settings_path.read_text(encoding="utf-8")
        try:
            settings: dict = json.loads(raw)
        except json.JSONDecodeError:
            settings = json.loads(_strip_jsonc(raw))
    else:
        settings = {}
        settings_path.parent.mkdir(parents=True, exist_ok=True)

    added: list[str] = []
    skipped: list[str] = []

    for setting_key, entry_key in entries:
        existing = settings.get(setting_key)
        if existing is None:
            settings[setting_key] = {}
        elif not isinstance(existing, dict):
            print(
                f"Error: '{setting_key}' in {settings_path} is not an object "
                f"(found {type(existing).__name__}). "
                f"Fix or remove that key manually, then re-run this command.",
                file=sys.stderr,
            )
            sys.exit(1)
        bucket: dict = settings[setting_key]
        if entry_key in bucket:
            skipped.append(f"  {setting_key}  (already present)")
        else:
            bucket[entry_key] = True
            added.append(f"  {setting_key}")

    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"VS Code user settings: {settings_path}")
    if added:
        print("Added:")
        for line in added:
            print(line)
    if skipped:
        print("Already present (skipped):")
        for line in skipped:
            print(line)
    if not added:
        print("No changes needed — all entries were already present.")
    else:
        print("\nReload your VS Code window (Ctrl+Shift+P → 'Reload Window') for the")
        print("Harness Installer agent to appear in the agents dropdown.")


def _copilot_cli_config_dir() -> Path:
    """Return the Copilot CLI global config directory.

    Mirrors the resolution order in copilot.exe:
      1. COPILOT_HOME environment variable
      2. ~/.copilot/ (default)
    """
    env = os.environ.get("COPILOT_HOME")
    if env:
        return Path(env)
    return Path.home() / ".copilot"


def _setup_copilot_cli() -> None:
    """Copy autoharness agents and skills into the Copilot CLI global config dir.

    Copilot CLI discovers agents from {config_dir}/agents/ and skills from
    {config_dir}/skills/ at session start.  This command copies the autoharness
    .github/agents/ and .github/skills/ trees into those directories so the
    Harness Installer and Harness Tuner agents are available in every session.

    Re-run this command after upgrading autoharness to pick up new agents or
    updated skill files.
    """
    home = _home()
    config_dir = _copilot_cli_config_dir()
    src_agents = home / ".github" / "agents"
    src_skills = home / ".github" / "skills"
    dst_agents = config_dir / "agents"
    dst_skills = config_dir / "skills"

    print(f"Copilot CLI config dir: {config_dir}")
    print()

    a, u = _copy_tree(src_agents, dst_agents, "*.md")
    _report_copy("Agents", a, u)

    a, u = _copy_tree(src_skills, dst_skills, "SKILL.md")
    _report_copy("Skills", a, u)

    print("Done. Start a new Copilot CLI session to pick up the changes.")
    print("Run this command again after upgrading autoharness.")


def _copy_tree(src_dir: Path, dst_dir: Path, glob: str) -> tuple[list[str], list[str]]:
    """Copy files matching glob from src_dir into dst_dir, preserving structure.

    Returns (added, updated) lists of relative paths.
    """
    added: list[str] = []
    updated: list[str] = []
    for src_file in sorted(src_dir.rglob(glob)):
        rel = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        existed = dst_file.exists()
        shutil.copy2(src_file, dst_file)
        (updated if existed else added).append(f"  {rel}")
    return added, updated


def _report_copy(label: str, added: list[str], updated: list[str]) -> None:
    if added:
        print(f"{label} added:")
        print("\n".join(added))
    if updated:
        print(f"{label} updated:")
        print("\n".join(updated))
    if not added and not updated:
        print(f"{label}: nothing to copy (source directory empty or missing)")
    print()


def _claude_config_dir() -> Path:
    """Return the Claude Code global config directory.

    Resolution order (mirrors Claude Code):
      1. CLAUDE_CONFIG_DIR environment variable
      2. ~/.claude/ (default)
    """
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    if env:
        return Path(env)
    return Path.home() / ".claude"


def _setup_claude() -> None:
    """Copy autoharness agents and skills into the Claude Code global config dir.

    Claude Code discovers agents from {config_dir}/agents/ and skills from
    {config_dir}/skills/ at session start.
    """
    home = _home()
    config_dir = _claude_config_dir()
    print(f"Claude Code config dir: {config_dir}")
    print()

    a, u = _copy_tree(home / ".github" / "agents", config_dir / "agents", "*.md")
    _report_copy("Agents", a, u)

    a, u = _copy_tree(home / ".github" / "skills", config_dir / "skills", "SKILL.md")
    _report_copy("Skills", a, u)

    print("Done. Restart Claude Code to pick up the changes.")
    print("Run this command again after upgrading autoharness.")


def _codex_config_dir() -> Path:
    """Return the Codex global config directory.

    Resolution order (mirrors Codex):
      1. CODEX_HOME environment variable
      2. ~/.codex/ (default)
    """
    env = os.environ.get("CODEX_HOME")
    if env:
        return Path(env)
    return Path.home() / ".codex"


def _setup_codex() -> None:
    """Copy autoharness skills into the Codex global skills directory.

    Codex discovers skills from {config_dir}/skills/<skill-name>/SKILL.md.
    Codex does not have a separate agents directory — skills serve as the
    agent entry points. The skill directory name becomes the skill name
    (e.g. install-harness, tune-harness).

    Note: Codex SKILL.md files use the same frontmatter format as autoharness.
    If the frontmatter lacks a top-level 'name:' field, Codex infers the name
    from the directory.
    """
    home = _home()
    config_dir = _codex_config_dir()
    print(f"Codex config dir: {config_dir}")
    print()

    a, u = _copy_tree(home / ".github" / "skills", config_dir / "skills", "SKILL.md")
    _report_copy("Skills", a, u)

    print("Done. Restart Codex to pick up the changes.")
    print("Run this command again after upgrading autoharness.")


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
    elif command == "setup-vscode":
        _setup_vscode()
    elif command == "setup-copilot-cli":
        _setup_copilot_cli()
    elif command == "setup-claude":
        _setup_claude()
    elif command == "setup-codex":
        _setup_codex()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
