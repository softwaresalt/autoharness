"""Pytest bootstrap for the throwaway 088-F compression experiment's tests.

Inserts the experiment root (the parent of this ``tests/`` directory) onto
``sys.path`` so ``import brainspace...`` resolves without touching the
repository's global ``pyproject.toml`` pytest configuration. This keeps the
experiment trivially removable: deleting
``experiments/088-compression-experiment/`` removes this bootstrap too.
"""

import os
import sys

_EXPERIMENT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _EXPERIMENT_ROOT not in sys.path:
    sys.path.insert(0, _EXPERIMENT_ROOT)
