"""The ``cascade-close`` command package (192-F).

This module holds only the command's ``EXIT_*`` constants, their single
definition (re-plan cycle-1 R15). Every ``shipment_close`` module imports them
from here; the read-only ``gates/cascade_evidence.py`` never defines or
imports them.
"""

from __future__ import annotations

from typing import Final

# Mutating mode: all postconditions passed. --classify-only: CASCADE selected.
EXIT_OK: Final = 0
# Input, I/O, no-clobber refusal, a disposition planning_error, or a
# pre-invocation write failure. Nothing mutated.
EXIT_INPUT: Final = 2
# The selected path is not CASCADE; a verdict record was written, nothing invoked.
EXIT_SAFE_CLOSE_SELECTED: Final = 3
# Pre-invocation revalidation drift (snapshot, engine re-probe, binary hash, or a
# difference from a cascade-selected --classify-only record). Nothing invoked.
EXIT_REVALIDATION_DRIFT: Final = 4
# A postcondition failed (including linked_deliberation_drift).
EXIT_POSTCONDITION_FAILED: Final = 5
# backlogit exited non-zero, timed out, or stdout did not parse.
EXIT_INVOCATION_INDETERMINATE: Final = 6
# An existing lock or invoking record; nothing invoked.
EXIT_LOCKED: Final = 7
# The post-close evidence write failed after invocation.
EXIT_POST_WRITE_FAILED: Final = 8
