"""Non-runtime build/release-time helper modules.

Everything under ``build_support/`` supports the build or release pipeline
(for example, the PyPI pre-publish probe in ``pypi_probe.py``) and is never
imported by the installed ``autoharness`` package at runtime. This package
is already excluded from the wheel (``[tool.hatch.build.targets.wheel]``
``packages = ["src/autoharness"]`` does not include it). It is intended to
also be excluded from the sdist as an explicit exclusion rule so a future
runtime import of it fails the payload gate loudly instead of quietly
enlarging the shipped payload; that explicit sdist exclusion rule is carried
by a different shipment's manifest (SHIP-10 / 160.003-T) and is not yet
present as of this shipment.
"""

from __future__ import annotations
