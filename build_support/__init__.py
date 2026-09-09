"""Non-runtime build/release-time helper modules.

Everything under ``build_support/`` supports the build or release pipeline
(for example, the PyPI pre-publish probe in ``pypi_probe.py``) and is never
imported by the installed ``autoharness`` package at runtime. This package is
excluded from both distribution channels (wheel and sdist) so it never
enlarges the shipped payload.
"""

from __future__ import annotations
