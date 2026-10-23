"""Version-site collector for the release version-consistency check (217.001-T)."""

from __future__ import annotations

from pathlib import Path


def collect_version_sites(root: Path, *, case: str) -> dict[str, str]:
    """Return a mapping of version-site name to its declared version string."""
    raise NotImplementedError(f"217.001-T:{case}")
