"""Version-site collector for the release version-consistency check (217.001-T)."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

_FALLBACK_RE = re.compile(r'__version__\s*=\s*"([^"]+)"')


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
        data = tomllib.loads((root / name).read_text(encoding="utf-8"))
        sites[name] = str(data["project"]["version"])
    except (OSError, KeyError, ValueError):
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
        data = tomllib.loads((root / name).read_text(encoding="utf-8"))
        found = [
            str(p["version"])
            for p in data.get("package", [])
            if p.get("name") == "autoharness" and "editable" in p.get("source", {})
        ]
        sites[name] = found[0] if found else _missing(name)
    except (OSError, ValueError):
        sites[name] = _missing(name)

    return sites
