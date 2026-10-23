"""Version-site collector for the release version-consistency check (217.001-T)."""

from __future__ import annotations

import json
import re
from pathlib import Path

_FALLBACK_RE = re.compile(r'__version__\s*=\s*"([^"]+)"')
_VERSION_LINE_RE = re.compile(r'^version\s*=\s*"([^"]+)"\s*$')
_NAME_LINE_RE = re.compile(r'^name\s*=\s*"([^"]+)"\s*$')


def _pyproject_project_version(text: str) -> str | None:
    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_project = stripped == "[project]"
        elif in_project:
            match = _VERSION_LINE_RE.match(stripped)
            if match:
                return match.group(1)
    return None


def _lock_editable_version(text: str, package: str) -> str | None:
    for block in re.split(r"^\[\[package\]\]\s*$", text, flags=re.MULTILINE)[1:]:
        name = version = None
        editable = False
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("["):
                break
            if (m := _NAME_LINE_RE.match(stripped)) and name is None:
                name = m.group(1)
            elif (m := _VERSION_LINE_RE.match(stripped)) and version is None:
                version = m.group(1)
            elif stripped.startswith("source") and "editable" in stripped:
                editable = True
        if name == package and editable and version:
            return version
    return None


def _missing(site: str) -> str:
    return f"<missing:{site}>"


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def collect_version_sites(root: Path, *, case: str) -> dict[str, str]:
    """Return a mapping of version-site name to its declared version string.

    A site that cannot be read maps to a distinct ``<missing:...>`` marker so a
    missing or unparsable site never compares equal to a real version.
    """
    del case
    sites: dict[str, str] = {}

    name = "pyproject.toml"
    try:
        found = _pyproject_project_version((root / name).read_text(encoding="utf-8"))
        sites[name] = found if found else _missing(name)
    except (OSError, ValueError):
        sites[name] = _missing(name)

    name = "src/autoharness/__init__.py"
    try:
        match = _FALLBACK_RE.search((root / name).read_text(encoding="utf-8"))
        sites[name] = match.group(1) if match else _missing(name)
    except OSError:
        sites[name] = _missing(name)

    name = "plugin.json"
    data = _read_json(root / name)
    sites[name] = str(data["version"]) if isinstance(data, dict) and "version" in data else _missing(name)

    market = _read_json(root / ".github" / "plugin" / "marketplace.json")
    name = ".github/plugin/marketplace.json#metadata"
    try:
        sites[name] = str(market["metadata"]["version"])
    except (TypeError, KeyError):
        sites[name] = _missing(name)
    name = ".github/plugin/marketplace.json#plugins[0]"
    try:
        sites[name] = str(market["plugins"][0]["version"])
    except (TypeError, KeyError, IndexError):
        sites[name] = _missing(name)

    name = "uv.lock"
    try:
        found = _lock_editable_version((root / name).read_text(encoding="utf-8"), "autoharness")
        sites[name] = found if found else _missing(name)
    except (OSError, ValueError):
        sites[name] = _missing(name)

    return sites
